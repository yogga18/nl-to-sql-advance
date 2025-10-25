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

@lru_cache(maxsize=1)
def get_document_retriever():
    """Membuat retriever SINGLETON untuk koleksi dokumen umum."""
    print(f"✅ Creating Document Retriever for '{config.COLLECTION_NAME}'...")
    shared_embeddings = get_embedding_model()
    return get_qdrant_retriever(
        qdrant_host=config.QDRANT_HOST,
        # qdrant_api_key=config.QDRANT_API_KEY,
        collection_name=config.COLLECTION_NAME,
        embeddings=shared_embeddings
    )

@lru_cache(maxsize=1)
def get_chat_history_retriever():
    """
    Membuat retriever SINGLETON untuk koleksi riwayat chat di Qdrant.
    """
    print(f"✅ Creating Chat History Retriever for 'chat_history_collection'...")
    shared_embeddings = get_embedding_model()
    return get_qdrant_retriever(
        qdrant_host=config.QDRANT_HOST,
        # qdrant_api_key=config.QDRANT_API_KEY,
        # Pastikan nama koleksi ini sesuai dengan yang Anda buat
        collection_name="chat_history_collection",
        embeddings=shared_embeddings
    )