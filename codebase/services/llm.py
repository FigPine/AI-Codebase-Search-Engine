import requests

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
MODEL_NAME = "qwen3.5-2B"

def generate_explanation(query, context_chunks):
    """
    Generates an explanation using the local LM Studio instance.
    """
    
    # Construct context string
    context_str = ""
    for i, chunk in enumerate(context_chunks):
        context_str += f"\n--- File: {chunk['filepath']} (Chunk {chunk['chunk_index']}) ---\n"
        context_str += chunk['text'] + "\n"
        
    system_prompt = (
        "You are an expert AI programming assistant. "
        "Use the provided codebase context to answer the user's question. "
        "If the context doesn't contain the answer, say you don't know based on the context."
    )
    
    user_prompt = f"Context from codebase:\n{context_str}\n\nQuestion: {query}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.3,
        "max_tokens": -1,
        "stream": False
    }
    
    try:
        response = requests.post(LM_STUDIO_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        return f"Error communicating with LLM: {str(e)}"
