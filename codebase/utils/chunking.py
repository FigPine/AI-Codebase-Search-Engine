def chunk_text(text, chunk_size=500, overlap=50):
    """
    Split text into chunks of `chunk_size` characters with `overlap` characters.
    """
    if not text:
        return []
    
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start += chunk_size - overlap
    return chunks
