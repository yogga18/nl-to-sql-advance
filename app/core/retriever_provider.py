from functools import lru_cache
from app import config

from .embedding_provider import get_embedding_model
from ..adapters.vector_store.qdrant_adapter import get_qdrant_retriever

@lru_cache(maxsize=1)
def get_schema_retriever():
    """
    Membuat dan mengembalikan retriever SINGLETON untuk koleksi skema.
    """
    print("✅ Creating Schema Retriever...")

    shared_embeddings = get_embedding_model()
    
    return get_qdrant_retriever(
        qdrant_host=config.QDRANT_HOST,
        # qdrant_api_key=config.QDRANT_API_KEY,
        collection_name=config.COLLECTION_NAME,
        embeddings=shared_embeddings
    )