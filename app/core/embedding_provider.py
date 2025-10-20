from langchain_huggingface import HuggingFaceEmbeddings
from functools import lru_cache
from app import config

@lru_cache(maxsize=1)
def get_embedding_model() -> HuggingFaceEmbeddings:
    print(f"✅ Loading embedding model: {config.EMBEDDING_MODEL_NAME}...")

    embeddings = HuggingFaceEmbeddings(
        model_name=config.EMBEDDING_MODEL_NAME,
        model_kwargs={'device': 'cpu'}
    )
    
    print("✅ Embedding model loaded into memory.")
    return embeddings