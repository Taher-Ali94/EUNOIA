config = {
    "version" : "v1.1",
    "embedder":{
        "provider": "ollama",
        "config": {
        "model": "nomic-embed-text",
        "embedding_dims": 768,
        "ollama_base_url": "http://localhost:11434"
    }
    },
    "llm": {
        "provider": "ollama",
        "config": {
            "model": "llama3.2:1b",
            "temperature": 0,
            "ollama_base_url": "http://localhost:11434"
        }
    },
    "vector_store":{
        "provider": "chroma",
        "config": {
            "host": "localhost",
            "port": 8000,
            "collection_name": "Eunoia_Memories",
        },
    }
}