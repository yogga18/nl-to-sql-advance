from qdrant_client import QdrantClient
from langchain_qdrant import Qdrant
from langchain_core.embeddings import Embeddings

def get_qdrant_retriever(
    qdrant_host: str,
    # qdrant_api_key: str,
    collection_name: str,
    embeddings: Embeddings
):
    client = QdrantClient(
        host=qdrant_host,
        # api_key=qdrant_api_key,
        prefer_grpc=False
    )

    vector_store = Qdrant(
        client=client,
        collection_name=collection_name,
        embeddings=embeddings
    )

    return vector_store.as_retriever()