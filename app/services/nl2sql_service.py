from ..core.security.sql_validator import sanitize_sql_output, is_safe_select_query
from ..core.db_executor import execute_select_query
from ..core.retriever_provider import get_schema_retriever
from ..core.promts.nl2sql import (
    QUESTION_CLASSIFICATION_PROMT,
    SQL_PROMPT,
    REASONING_PROMPT,
    QUESTION_CLASSIFICATION_CONVERSTATION_PROMT,
    SQL_CONVERSTATION_PROMPT,
    REASONING_CONVERSTATION_PROMPT,
)
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, cast
from ..adapters.llm.llm_factory import get_llm_adapter
from ..adapters.db import crud, schemas
from fastapi import BackgroundTasks
from datetime import datetime
from ..adapters.vector_store.qdrant_adapter import add_message_vector
from ..core.embedding_provider import get_embedding_model
from ..core.sql_chat_history import SQLChatMessageHistory 
from langchain_core.messages import HumanMessage, AIMessage

class NL2SQLService:
    """
    Service layer yang bertanggung jawab untuk seluruh logika bisnis NL-to-SQL.
    Menggunakan RAG on Schema untuk konteks dinamis dan memiliki penanganan error yang bersih.
    """
    def __init__(self):
        print("Initializing NL2SQL Service (stateless)...")
        self.schema_retriever = get_schema_retriever() # Ambil retriever untuk skema database dari provider terpusat.
        print("✅ NL2SQL Service Initialized.")
    
    async def _measure_time(self, func, *args, **kwargs):
        """Helper untuk mengukur waktu eksekusi fungsi async."""
        start = datetime.now()
        result = await func(*args, **kwargs)
        end = datetime.now()
        latency_ms = int((end - start).total_seconds() * 1000)
        return result, latency_ms

    async def _generate_and_execute_sql(self, nl_query: str, llm) -> tuple[str, list[dict[str, Any]], str, dict]:
        """
        Menjalankan RAG, generasi SQL, validasi, eksekusi, dan mengukur latency.
        Mengembalikan (SQL, Data Mentah, Konteks RAG, Dictionary Latency).
        """
        latencies = {}

        # === LANGKAH 3 (DINAMIS): RAG ON SCHEMA ===
        rag_result, rag_latency = await self._measure_time(self.schema_retriever.ainvoke, nl_query)
        latencies['rag'] = rag_latency
        retrieved_schema_docs = rag_result
        dynamic_context = "\n".join([doc.page_content for doc in retrieved_schema_docs])
        print(f"--- RAG Latency: {rag_latency} ms ---")

        # === LANGKAH 4: GENERATE SQL QUERY ===
        sql_generation_prompt = SQL_PROMPT.format(
            context=dynamic_context,
            nl_query=nl_query
        )
        sql_response, sql_gen_latency = await self._measure_time(llm.ainvoke, sql_generation_prompt)
        latencies['sql_generation'] = sql_gen_latency
        print(f"--- SQL Gen Latency: {sql_gen_latency} ms ---")

        # === LANGKAH 5 & 6: SANITASI DAN VALIDASI ===
        sanitized_sql = sanitize_sql_output(sql_response.content)
        if not is_safe_select_query(sanitized_sql):
            raise ValueError("Kueri yang dihasilkan tidak aman dan telah diblokir.")

        # === LANGKAH 7: EKSEKUSI KUERI ===
        try:
            # Ukur waktu eksekusi query secara terpisah
            sql_exec_start = datetime.now()
            data_raw = await execute_select_query(sanitized_sql)
            sql_exec_end = datetime.now()
            latencies['sql_execution'] = int((sql_exec_end - sql_exec_start).total_seconds() * 1000)
            print(f"--- SQL Exec Latency: {latencies['sql_execution']} ms ---")
            
            # Kembalikan semua hasil termasuk dictionary latencies
            return sanitized_sql, data_raw, dynamic_context, latencies
        except Exception as e:
            raise RuntimeError(f"Gagal mengeksekusi SQL: {e}")
        
    async def _generate_and_execute_sql_with_history(
        self,
        nl_query: str,
        llm,
        conversation_history: str # Tambahkan parameter history
    ) -> tuple[str, list[dict[str, Any]], str, dict]:
        """
        Versi helper yang menerima chat history.
        Mengembalikan (SQL, Data Mentah, Konteks RAG, Dictionary Latency).
        """
        latencies = {}
        
        print(f"====yahoooo")
        print(conversation_history)

        # RAG (tetap sama)
        rag_result, rag_latency = await self._measure_time(self.schema_retriever.ainvoke, nl_query)
        latencies['rag'] = rag_latency
        dynamic_context = "\n".join([doc.page_content for doc in rag_result])
        print(f"--- RAG Context Provided to LLM ---") # Log Awal
        print(dynamic_context)                         # Cetak Konteksnya
        print(f"------------------------------------") # Log Akhir
        print(f"--- RAG Latency: {rag_latency} ms ---")

        # SQL Gen (gunakan history dan prompt conversation)
        sql_generation_prompt = SQL_CONVERSTATION_PROMPT.format(
            conversation_history=conversation_history,
            context=dynamic_context,
            nl_query=nl_query,
        )
        sql_response, sql_gen_latency = await self._measure_time(llm.ainvoke, sql_generation_prompt)
        latencies['sql_generation'] = sql_gen_latency
        print(f"--- SQL Gen Latency: {sql_gen_latency} ms ---")

        # Sanitasi & Validasi (tetap sama)
        sanitized_sql = sanitize_sql_output(sql_response.content)
        if not is_safe_select_query(sanitized_sql):
            raise ValueError("Kueri yang dihasilkan tidak aman dan telah diblokir.")

        # Eksekusi (tetap sama)
        try:
            sql_exec_start = datetime.now()
            data_raw = await execute_select_query(sanitized_sql)
            sql_exec_end = datetime.now()
            latencies['sql_execution'] = int((sql_exec_end - sql_exec_start).total_seconds() * 1000)
            print(f"--- SQL Exec Latency: {latencies['sql_execution']} ms ---")
            return sanitized_sql, data_raw, dynamic_context, latencies
        except Exception as e:
            raise RuntimeError(f"Gagal mengeksekusi SQL: {e}")

    async def execute_flow(
        self,
        nl_query: str,
        model_name: str,
        nip: str,
        kode_unit: str,
        display_name: str,
        room_id: int,
        endpoint_path: str,
        db_session: AsyncSession,
        background_tasks: BackgroundTasks,
    ) -> Dict[str, Any]:
        """
        Generate Query, Get Data, Reasoning, dan log ke DB & Qdrant di background.
        """
        start_flow_time = datetime.now()
        overall_latencies = {}

        llm = get_llm_adapter(model_name=model_name)

        # === Simpan Pesan User (Foreground - dapatkan ID dan objek tersimpan) ===
        user_message_schema = schemas.ChatMessageCreate(
            room_id=room_id, sender='user', message_text=nl_query
        )
        saved_user_message = await crud.create_chat_message(db_session, user_message_schema)
        user_msg_id = cast(int, saved_user_message.message_id)

        # === LANGKAH 1 & 2: KLASIFIKASI & VALIDASI ===
        validation_response, classification_latency = await self._measure_time(llm.ainvoke, QUESTION_CLASSIFICATION_PROMT.format(nl_query=nl_query))
        overall_latencies['classification'] = classification_latency
        if "data_perusahaan" not in validation_response.content.lower():
            raise ValueError("Pertanyaan tidak relevan dengan data perusahaan.")

        # === LANGKAH 3-7: RAG, SQL GEN, VALIDASI, EKSEKUSI ===
        sanitized_sql, data_raw, dynamic_context, sql_latencies = await self._generate_and_execute_sql(nl_query, llm)
        overall_latencies.update(sql_latencies)

        # === LANGKAH 8: REASONING ===
        reasoning = "Kueri berhasil dieksekusi tetapi tidak menghasilkan data."
        reasoning_latency = 0
        if data_raw:
             # ✅ Gunakan PromptTemplate yang baru
             reasoning_prompt_formatted = REASONING_PROMPT.format(
                 nl_query=nl_query,
                 data_raw=str(data_raw)[:2500] # Tetap potong data jika perlu
             )
             reasoning_response, reasoning_latency = await self._measure_time(llm.ainvoke, reasoning_prompt_formatted)
             reasoning = reasoning_response.content
        overall_latencies['reasoning'] = reasoning_latency

        # === Simpan Jawaban AI (Foreground - agar dapat objek untuk Qdrant) ===
        ai_message_schema = schemas.ChatMessageCreate(
            room_id=room_id, sender='ai', message_text=reasoning, in_reply_to_message_id=user_msg_id
        )
        # Simpan ke MySQL dan dapatkan objek yang sudah disimpan
        saved_ai_message = await crud.create_chat_message(db_session, ai_message_schema)

        # === PERSIAPAN LOG (Sekarang menyertakan latency per langkah) ===
        end_flow_time = datetime.now()
        total_latency = int((end_flow_time - start_flow_time).total_seconds() * 1000)
        provider = "Gemini" if "Google/gemini-2.5-flash" in model_name.lower() else model_name

        if user_msg_id:
            llm_run_schema = schemas.LLMRunCreate(
                user_message_id=user_msg_id,
                generated_sql=sanitized_sql,
                retrieved_context_knowledge=dynamic_context,
                llm_model_used=model_name,
                llm_provider_user=provider,
                latency_total_ms=total_latency,
                endpoint_path=endpoint_path,
                latency_classification_ms=overall_latencies.get('classification'),
                latency_rag_ms=overall_latencies.get('rag'),
                latency_sql_generation_ms=overall_latencies.get('sql_generation'),
                latency_sql_execution_ms=overall_latencies.get('sql_execution'),
                latency_reasoning_ms=overall_latencies.get('reasoning'),
                is_success=True
            )

            # Task untuk menyimpan log LLM Run (MySQL)
            background_tasks.add_task(crud.create_llm_run, db_session, llm_run_schema)

            # Dapatkan embedding model sekali untuk background tasks
            shared_embeddings = get_embedding_model()

            if saved_user_message:
                print(f"save question from user to qdrant")
                user_msg_read_schema = schemas.ChatMessageRead.from_orm(saved_user_message)
                background_tasks.add_task(add_message_vector, user_msg_read_schema, shared_embeddings)
            if saved_ai_message:
                print(f"save answer from ai to qdrant")
                ai_msg_read_schema = schemas.ChatMessageRead.from_orm(saved_ai_message)
                background_tasks.add_task(add_message_vector, ai_msg_read_schema, shared_embeddings)
        else:
            print("Warning: user_msg_id is None, skipping LLM run logging.")

        return {"query": sanitized_sql, "data_raw": data_raw, "reasoning": reasoning}
    
    async def generate_sql_and_data(
        self,
        nl_query: str,
        model_name: str,
        nip: str,
        kode_unit: str,
        display_name: str,
        room_id: int,
        endpoint_path: str,
        db_session: AsyncSession,
        background_tasks: BackgroundTasks,
    ) -> Dict[str, Any]:
        """
        Generate Query and Get Data Only
        """

        start_flow_time = datetime.now()
        overall_latencies = {} # Dictionary untuk menyimpan semua latency

        llm = get_llm_adapter(model_name=model_name)
        
        user_message_schema = schemas.ChatMessageCreate(
            room_id=room_id, sender='user', message_text=nl_query
        )
        saved_user_message = await crud.create_chat_message(db_session, user_message_schema)
        user_msg_id = cast(int, saved_user_message.message_id)
        
        # Validasi prompt
        validation_prompt = QUESTION_CLASSIFICATION_PROMT.format(nl_query=nl_query) # Pastikan nama prompt benar
        validation_response, classification_latency = await self._measure_time(llm.ainvoke, validation_prompt)
        overall_latencies['classification'] = classification_latency
        print(f"--- Classification Latency: {classification_latency} ms ---")
        if "data_perusahaan" not in validation_response.content.lower():
            raise ValueError("Pertanyaan tidak relevan dengan data perusahaan.")
        
        sanitized_sql, data_raw, dynamic_context, sql_latencies = await self._generate_and_execute_sql(nl_query, llm)
        overall_latencies.update(sql_latencies)
        end_flow_time = datetime.now()
        total_latency = int((end_flow_time - start_flow_time).total_seconds() * 1000)
        provider = "Gemini" if "gemini" in model_name.lower() else "OpenRouter"

        llm_run_schema = schemas.LLMRunCreate(
            user_message_id=user_msg_id,
            generated_sql=sanitized_sql,
            retrieved_context_knowledge=dynamic_context,
            llm_model_used=model_name,
            llm_provider_user=provider,
            is_success=True,
            endpoint_path=endpoint_path,
            latency_total_ms=total_latency,
            latency_classification_ms=overall_latencies.get('classification'),
            latency_rag_ms=overall_latencies.get('rag'),
            latency_sql_generation_ms=overall_latencies.get('sql_generation'),
            latency_sql_execution_ms=overall_latencies.get('sql_execution')
        )

        ai_message_schema = schemas.ChatMessageCreate(
            room_id=room_id, sender='ai', message_text="Berikut adalah hasil data yang Anda minta.", in_reply_to_message_id=user_msg_id
        )

        # === BACKGROUND TASK ===
        background_tasks.add_task(crud.create_llm_run, db_session, llm_run_schema)
        background_tasks.add_task(crud.create_chat_message, db_session, ai_message_schema)

        # Kembalikan hanya query dan data mentah
        return {"query": sanitized_sql, "data_raw": data_raw}

    async def execute_flow_conversation(
        self,
        nl_query: str,
        model_name: str,
        room_id: int,
        endpoint_path: str,
        db_session: AsyncSession,
        background_tasks: BackgroundTasks,
        chat_history_string: str,
        message_history_backend: SQLChatMessageHistory
    ) -> Dict[str, Any]:
        """
        Versi execute_flow yang menggunakan history string & backend MySQL.
        """
        start_flow_time = datetime.now()
        overall_latencies = {}

        llm = get_llm_adapter(model_name=model_name)

        # === Simpan Pesan User (Melalui Backend History Langsung) ===
        user_message_obj = HumanMessage(content=nl_query)
        saved_user_message = await message_history_backend.add_message(user_message_obj)
        user_msg_id = saved_user_message.message_id if saved_user_message else None

        try:
            validation_prompt = QUESTION_CLASSIFICATION_CONVERSTATION_PROMT.format(
                conversation_history=chat_history_string,
                nl_query=nl_query
            )
            validation_response, classification_latency = await self._measure_time(llm.ainvoke, validation_prompt)
            overall_latencies['classification'] = classification_latency

            classification_result = validation_response.content.lower()
            print(f"--- Classification Result: {classification_result} ---")

            if "data_perusahaan" not in classification_result and "lanjutan" not in classification_result:
                error_msg = f"Pertanyaan diklasifikasikan sebagai '{validation_response.content.strip()}' dan dianggap tidak relevan."
                await message_history_backend.add_message(AIMessage(content=error_msg))
                raise ValueError(error_msg)

            # === RAG, SQL GEN (DENGAN HISTORY), VALIDASI, EKSEKUSI ===
            sanitized_sql, data_raw, dynamic_context, sql_latencies = await self._generate_and_execute_sql_with_history(
                nl_query, llm, chat_history_string
            )
            overall_latencies.update(sql_latencies)
            print(f"Sanitized SQL: {sanitized_sql}")

            # === REASONING (DENGAN HISTORY) ===
            reasoning = "Kueri berhasil dieksekusi tetapi tidak menghasilkan data."
            reasoning_latency = 0
            if data_raw:
                # Gunakan history string yang diteruskan
                reasoning_prompt_formatted = REASONING_CONVERSTATION_PROMPT.format(
                    conversation_history=chat_history_string,
                    nl_query=nl_query,
                    data_raw=str(data_raw)[:2500]
                )
                reasoning_response, reasoning_latency = await self._measure_time(llm.ainvoke, reasoning_prompt_formatted)
                reasoning = reasoning_response.content
            overall_latencies['reasoning'] = reasoning_latency

            # === Simpan Jawaban AI (Melalui Backend History Langsung) ===
            ai_message_obj = AIMessage(content=reasoning)
            # Gunakan backend history yang diteruskan dan tangkap hasilnya
            saved_ai_message = await message_history_backend.add_message(ai_message_obj)

            # --- Persiapan & Jadwalkan Log Background Task ---
            end_flow_time = datetime.now()
            total_latency = int((end_flow_time - start_flow_time).total_seconds() * 1000)
            provider = "Gemini" if "gemini" in model_name.lower() else ("Anthropic" if "claude" in model_name.lower() else "OpenRouter")

            if user_msg_id:
                llm_run_schema = schemas.LLMRunCreate(
                    user_message_id=user_msg_id, endpoint_path=endpoint_path,
                    generated_sql=sanitized_sql, retrieved_context_knowledge=dynamic_context,
                    llm_model_used=model_name, llm_provider_user=provider,
                    is_success=True, latency_total_ms=total_latency,
                    latency_classification_ms=overall_latencies.get('classification'),
                    latency_rag_ms=overall_latencies.get('rag'),
                    latency_sql_generation_ms=overall_latencies.get('sql_generation'),
                    latency_sql_execution_ms=overall_latencies.get('sql_execution'),
                    latency_reasoning_ms=overall_latencies.get('reasoning')
                )

                background_tasks.add_task(crud.create_llm_run, db_session, llm_run_schema)

                shared_embeddings = get_embedding_model()

                if saved_user_message:
                    print(f"save question from user to qdrant")
                    user_msg_read_schema = schemas.ChatMessageRead.from_orm(saved_user_message)
                    background_tasks.add_task(add_message_vector, user_msg_read_schema, shared_embeddings)
                if saved_ai_message:
                    print(f"save answer from ai to qdrant")
                    ai_msg_read_schema = schemas.ChatMessageRead.from_orm(saved_ai_message)
                    background_tasks.add_task(add_message_vector, ai_msg_read_schema, shared_embeddings)
            else:
                print("WARNING: Could not retrieve user message object or ID, skipping LLM run and vector logging.")

            # === KEMBALIKAN HASIL ===
            return {"query": sanitized_sql, "data_raw": data_raw, "reasoning": reasoning}

        except Exception as e:
            error_reasoning = f"Terjadi kesalahan saat memproses permintaan: {e}"
            try:
                await message_history_backend.add_message(AIMessage(content=error_reasoning))
            except Exception as log_e:
                print(f"Failed to log AI error message to history: {log_e}")
            raise e
        
nl2sql_service_instance = NL2SQLService()

def get_nl2sql_service() -> NL2SQLService:
    return nl2sql_service_instance