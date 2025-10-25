from qdrant_client import models, AsyncQdrantClient
from langchain_qdrant import QdrantVectorStore
from langchain_core.embeddings import Embeddings
import uuid
from app.adapters.db import schemas
import asyncio
import app.config as config

def get_qdrant_retriever(
    qdrant_host: str,
    # qdrant_api_key: str,
    collection_name: str,
    embeddings: Embeddings
):
    vector_store = QdrantVectorStore.from_existing_collection(
         embedding=embeddings,
         collection_name=collection_name,
         host=qdrant_host,
        #  api_key=qdrant_api_key,
         prefer_grpc=False
     )
    
    return vector_store.as_retriever()

async def add_message_vector(
    message: schemas.ChatMessageRead, # Terima objek pesan yang sudah disimpan (punya ID)
    embeddings: Embeddings, # Terima instance embedding model
    collection_name: str = "chat_history_collection"
):
    """
    Membuat vektor dari teks pesan dan menyimpannya ke Qdrant.
    """
    # 1. Buat Vektor dari Teks Pesan
    # Gunakan run_in_executor karena embedding CPU-bound
    loop = asyncio.get_running_loop()
    vector = await loop.run_in_executor(
        None,
        embeddings.embed_query, # Fungsi embed_query cocok untuk satu teks
        message.message_text
    )

    # 2. Siapkan Payload (Metadata)
    payload = {
        "text": message.message_text,
        "sender": message.sender,
        "room_id": message.room_id,
        "timestamp": message.timestamp.isoformat(), # Simpan sebagai string ISO format
        "original_message_id": message.message_id # Simpan ID dari MySQL
    }

    # 3. Siapkan Point untuk Qdrant
    # Gunakan UUID baru untuk ID point Qdrant, atau bisa juga message_id jika unik
    point_id = str(uuid.uuid4())
    point = models.PointStruct(
        id=point_id,
        vector=vector,
        payload=payload
    )

    # 4. Buat Koneksi Qdrant Client (bisa dioptimalkan dengan instance global)
    # Untuk background task, mungkin lebih aman membuat koneksi baru tiap task
    client = AsyncQdrantClient(
        host=config.QDRANT_HOST,
        # api_key=config.QDRANT_API_KEY,
        prefer_grpc=False
    )

    try:
        # ✅ Use await with the async client's upsert method
        await client.upsert(collection_name=collection_name, points=[point], wait=False)
        print(f"✅ Successfully upserted message vector {point_id} to Qdrant collection '{collection_name}'")
    except Exception as e:
        print(f"❌ Error upserting message vector to Qdrant: {e}")
    finally:
        # ✅ Use await with the async client's close coroutine
        await client.close() # Use close() coroutine for the async client