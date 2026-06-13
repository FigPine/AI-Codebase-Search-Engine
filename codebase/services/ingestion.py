import os
import zipfile
import tempfile
import shutil
from ..utils.chunking import chunk_text

IGNORED_DIRS = {'.git', 'node_modules', 'venv', '__pycache__', '.venv', 'env', '.idea', '.vscode'}

def is_binary(filepath):
    """Check if a file is binary by looking for null bytes or failing utf-8 decode."""
    try:
        with open(filepath, 'rb') as f:
            chunk = f.read(1024)
            if b'\0' in chunk:
                return True
            chunk.decode('utf-8')
            return False
    except UnicodeDecodeError:
        return True
    except Exception:
        return True # If we can't read it, treat as binary/skip

def process_zip_upload(zip_file):
    """
    Extracts zip, reads valid text files, chunks them, and returns a list of chunks.
    Each chunk is a dict: {'text': ..., 'filepath': ..., 'chunk_index': ...}
    """
    chunks_data = []
    
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Extract the zip
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
            
        # Walk the directory
        for root, dirs, files in os.walk(temp_dir):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            
            for file in files:
                filepath = os.path.join(root, file)
                
                # Skip binary files
                if is_binary(filepath):
                    continue
                    
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Get relative path for metadata
                    rel_path = os.path.relpath(filepath, temp_dir)
                    
                    file_chunks = chunk_text(content, chunk_size=1000, overlap=100)
                    for i, chunk in enumerate(file_chunks):
                        chunks_data.append({
                            'text': chunk,
                            'filepath': rel_path,
                            'chunk_index': i
                        })
                except Exception as e:
                    print(f"Error reading file {filepath}: {e}")
                    
    finally:
        # Cleanup temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)
        
    return chunks_data
