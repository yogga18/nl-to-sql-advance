from langchain.memory import (
    ConversationBufferWindowMemory,
    VectorStoreRetrieverMemory,
    CombinedMemory,
    ConversationSummaryMemory,
    ConversationSummaryBufferMemory
)
from langchain_core.chat_history import BaseChatMessageHistory
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

# Impor komponen yang dibutuhkan
from .sql_chat_history import SQLChatMessageHistory # Class backend MySQL kita
from .retriever_provider import get_chat_history_retriever # Retriever Qdrant history
# Anda mungkin perlu mengimpor factory LLM jika Summary Memory butuh LLM
from ..adapters.llm.llm_factory import get_llm_adapter
from app import config # Impor config jika perlu nama model default

# --- 1. Provider untuk Window Memory (MySQL Backend) ---
def get_window_memory(db_session: AsyncSession, room_id: int, k: int = 2) -> ConversationBufferWindowMemory:
    """
    Membuat instance ConversationBufferWindowMemory dengan backend SQLChatMessageHistory.
    """
    print(f"Creating Window Memory (k={k}) for room_id {room_id}")
    message_history = SQLChatMessageHistory(session=db_session, room_id=room_id)
    memory = ConversationBufferWindowMemory(
        chat_memory=message_history,
        k=k,
        memory_key="chat_history", # Kunci standar
        input_key="nl_query",      # Kunci standar input user di prompt
        return_messages=True
    )
    return memory

# # --- 2. Provider untuk Vector Memory (Qdrant Backend) ---
# def get_vector_memory(room_id: int, k_retrieved: int = 3) -> VectorStoreRetrieverMemory:
#     """
#     Membuat instance VectorStoreRetrieverMemory dengan backend Qdrant.
#     """
#     print(f"Creating Vector Memory (k_retrieved={k_retrieved}) for room_id {room_id}")
#     # TODO: Pastikan retriever ini dikonfigurasi untuk filter room_id
#     history_retriever = get_chat_history_retriever()

#     memory = VectorStoreRetrieverMemory(
#         retriever=history_retriever,
#         memory_key="relevant_history", # Kunci berbeda
#         input_key="nl_query" # Kunci input user di prompt
#     )
#     return memory

# # --- 3. Provider untuk Combined Memory ---
# def get_combined_memory(
#     db_session: AsyncSession,
#     room_id: int,
#     k_window: int = 3,
#     k_vector: int = 2
# ) -> CombinedMemory:
#     """
#     Membuat instance CombinedMemory yang menggabungkan Window dan Vector memory.
#     """
#     print(f"Creating Combined Memory for room_id {room_id}")
#     window_mem = get_window_memory(db_session, room_id, k=k_window)
#     vector_mem = get_vector_memory(room_id, k_retrieved=k_vector)

#     # ✅ FIX: Hapus memory_key dari constructor CombinedMemory
#     combined_memory = CombinedMemory(
#         memories=[window_mem, vector_mem]
#     )
#     # Variabel memori akan bisa diakses melalui keys masing-masing:
#     # context['chat_history'] dan context['relevant_history']
#     return combined_memory

# --- 4. Provider untuk Summary Memory (Contoh: SummaryBuffer) ---
def get_summary_buffer_memory(
    db_session: AsyncSession,
    room_id: int,
    model_name: str = config.GEMINI_MODEL_NAME,
    max_token_limit: int = 1000
) -> ConversationSummaryBufferMemory:
    """
    Membuat instance ConversationSummaryBufferMemory dengan backend SQLChatMessageHistory.
    """
    print(f"Creating Summary Buffer Memory for room_id {room_id}")
    # Panggi LLM untuk melakukan summarization pada percakapan sebelumnya
    llm_instance = get_llm_adapter(model_name)
    message_history = SQLChatMessageHistory(session=db_session, room_id=room_id)
    memory = ConversationSummaryBufferMemory(
        llm=llm_instance,
        chat_memory=message_history,
        max_token_limit=max_token_limit,
        memory_key="summary_history",
        input_key="nl_query",
        return_messages=True,
    )
    return memory
