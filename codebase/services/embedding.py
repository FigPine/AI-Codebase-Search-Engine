import os
import chromadb
from sentence_transformers import SentenceTransformer
from django.conf import settings

# Initialize persistent ChromaDB client in the project directory
CHROMA_DB_DIR = os.path.join(settings.BASE_DIR, "chroma_db")
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_DIR)

# Initialize embedding model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def index_repository(repo_name, chunks_data):
    """
    Indexes the chunks of a repository into ChromaDB.
    """
    # Create or get collection for the repo
    # ChromaDB collection names must be a valid identifier. We'll sanitize it.
    safe_repo_name = "".join([c if c.isalnum() else "_" for c in repo_name]).strip("_")
    
    collection = chroma_client.get_or_create_collection(name=safe_repo_name)
    
    if not chunks_data:
        return
        
    documents = []
    metadatas = []
    ids = []
    embeddings = []
    
    # Process in batches to avoid memory issues if large
    texts = [chunk['text'] for chunk in chunks_data]
    
    # Generate embeddings
    chunk_embeddings = embedding_model.encode(texts).tolist()
    
    for i, chunk in enumerate(chunks_data):
        documents.append(chunk['text'])
        metadatas.append({
            'filepath': chunk['filepath'],
            'chunk_index': chunk['chunk_index']
        })
        ids.append(f"{chunk['filepath']}_{chunk['chunk_index']}")
        embeddings.append(chunk_embeddings[i])
        
    # Upsert into ChromaDB
    collection.upsert(
        documents=documents,
        metadatas=metadatas,
        ids=ids,
        embeddings=embeddings
    )
    return safe_repo_name

def search_codebase(repo_name, query, top_k=5):
    """
    Searches the codebase for chunks relevant to the query.
    """
    safe_repo_name = "".join([c if c.isalnum() else "_" for c in repo_name]).strip("_")
    try:
        collection = chroma_client.get_collection(name=safe_repo_name)
    except Exception:
        return [] # Collection does not exist
        
    query_embedding = embedding_model.encode([query]).tolist()
    
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k
    )
    
    if not results['documents'] or not results['documents'][0]:
        return []
        
    # Format the results
    context_chunks = []
    for i in range(len(results['documents'][0])):
        context_chunks.append({
            'text': results['documents'][0][i],
            'filepath': results['metadatas'][0][i]['filepath'],
            'chunk_index': results['metadatas'][0][i]['chunk_index']
        })
        
    return context_chunks
