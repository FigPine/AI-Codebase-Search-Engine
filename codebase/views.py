from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Repository
from .services.ingestion import process_zip_upload
from .services.embedding import index_repository, search_codebase
from .services.llm import generate_explanation

def index(request):
    """Render the main UI."""
    repositories = Repository.objects.all().order_by('-uploaded_at')
    return render(request, 'codebase/index.html', {'repositories': repositories})

@csrf_exempt
def upload_repo(request):
    """Handle zip upload, extraction, chunking, and embedding."""
    if request.method == 'POST' and request.FILES.get('repo_zip'):
        zip_file = request.FILES['repo_zip']
        repo_name = zip_file.name.replace('.zip', '')
        
        # Save to DB
        repo = Repository.objects.create(name=repo_name)
        
        try:
            # Extract and chunk
            chunks_data = process_zip_upload(zip_file)
            
            # Index in ChromaDB
            safe_repo_name = index_repository(repo_name, chunks_data)
            
            return JsonResponse({
                'status': 'success', 
                'message': f'Repository {repo_name} indexed successfully.',
                'repo_name': safe_repo_name
            })
        except Exception as e:
            # Rollback DB entry if failed
            repo.delete()
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request.'}, status=400)

@csrf_exempt
def ask_question(request):
    """Handle user query, retrieve context, and generate explanation."""
    if request.method == 'POST':
        query = request.POST.get('query')
        repo_name = request.POST.get('repo_name') # Pass the safe_repo_name
        
        if not query or not repo_name:
            return JsonResponse({'status': 'error', 'message': 'Missing query or repo_name.'}, status=400)
            
        try:
            # 1. Retrieve context
            context_chunks = search_codebase(repo_name, query, top_k=5)
            
            if not context_chunks:
                return JsonResponse({'status': 'success', 'answer': "No relevant code found in the repository to answer your question."})
                
            # 2. Generate explanation
            answer = generate_explanation(query, context_chunks)
            
            return JsonResponse({
                'status': 'success',
                'answer': answer,
                'context_files': list(set(c['filepath'] for c in context_chunks))
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request.'}, status=400)