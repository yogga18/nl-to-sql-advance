from ..core.security.sql_validator import sanitize_sql_output, is_safe_select_query
from ..core.db_executor import execute_select_query
from ..core.retriever_provider import get_schema_retriever
from ..core.promts.nl2sql import QUESTION_CLASSIFICATION_PROMT, SQL_PROMPT

# Impor untuk interaksi async dan tipe data
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

# Impor "pabrik" LLM yang dinamis
from ..adapters.llm.llm_factory import get_llm_adapter

# Impor untuk logging di masa depan
# from ..adapters.db import crud, schemas

class NL2SQLService:
    """
    Service layer yang bertanggung jawab untuk seluruh logika bisnis NL-to-SQL.
    Menggunakan RAG on Schema untuk konteks dinamis dan memiliki penanganan error yang bersih.
    """
    def __init__(self):
        print("Initializing NL2SQL Service (stateless)...")
        self.schema_retriever = get_schema_retriever() # Ambil retriever untuk skema database dari provider terpusat.
        print("✅ NL2SQL Service Initialized.")

    async def _generate_and_execute_sql(self, nl_query: str, llm) -> tuple[str, list]:
        """
        ✨ NEW: Metode private untuk menangani logika inti yang berulang.
        Ini menjalankan RAG, generasi SQL, validasi, dan eksekusi.
        """
        # === LANGKAH 3 (DINAMIS): LAKUKAN RAG ON SCHEMA ===
        retrieved_schema_docs = await self.schema_retriever.ainvoke(nl_query)
        dynamic_context = "\n".join([doc.page_content for doc in retrieved_schema_docs])

        # === LANGKAH 4: GENERATE SQL QUERY DENGAN KONTEKS DINAMIS ===
        sql_generation_prompt = SQL_PROMPT.format(
            context=dynamic_context,
            nl_query=nl_query
        )
        sql_response = await llm.ainvoke(sql_generation_prompt)
        
        # === LANGKAH 5 & 6: SANITASI DAN VALIDASI KEAMANAN ===
        sanitized_sql = sanitize_sql_output(sql_response.content)
        if not is_safe_select_query(sanitized_sql):
            raise ValueError("Kueri yang dihasilkan tidak aman dan telah diblokir.")
        
        # === LANGKAH 7: EKSEKUSI KUERI & AMBIL HASIL ===
        try:
            data_raw = await execute_select_query(sanitized_sql)
            return sanitized_sql, data_raw
        except Exception as e:
            # Biarkan service melempar error non-HTTP. Router yang akan menanganinya.
            raise RuntimeError(f"Gagal mengeksekusi SQL: {e}")

    async def execute_flow(
        self,
        nl_query: str,
        model_name: str,
        # db_session: AsyncSession,
        # username: str
    ) -> Dict[str, Any]:
        """
        Orkestrator utama untuk alur kerja LENGKAP, termasuk reasoning.
        """
        llm = get_llm_adapter(model_name=model_name)

        # === LANGKAH 1 & 2: KLASIFIKASI & VALIDASI PROMPT ===
        validation_prompt = QUESTION_CLASSIFICATION_PROMT.format(nl_query=nl_query)
        validation_response = await llm.ainvoke(validation_prompt)

        if "data_perusahaan" not in validation_response.content.lower():
            raise ValueError("Pertanyaan tidak relevan dengan data perusahaan.")

        # Panggil helper untuk mendapatkan SQL dan data
        sanitized_sql, data_raw = await self._generate_and_execute_sql(nl_query, llm)
        
        # === LANGKAH 8: BUAT ANALISA/REASONING DARI HASIL ===
        if not data_raw:
            reasoning = "Kueri berhasil dieksekusi tetapi tidak menghasilkan data."
        else:
            reasoning_prompt = f"""
            Given the user's question: "{nl_query}"
            And the following data retrieved from the database:
            {str(data_raw)[:2500]}
            Provide a concise, natural language summary based on the data.
            """
            reasoning_response = await llm.ainvoke(reasoning_prompt)
            reasoning = reasoning_response.content
        
        # === LANGKAH (MASA DEPAN): SIMPAN LOG KE DATABASE ===
        # await crud.create_query_log(...)

        # === LANGKAH 9: KEMBALIKAN HASIL LENGKAP ===
        return {"query": sanitized_sql, "data_raw": data_raw, "reasoning": reasoning}

    async def generate_sql_and_data(
        self,
        nl_query: str,
        model_name: str,
    ) -> Dict[str, Any]:
        """
        Orkestrator untuk alur kerja SEDERHANA, hanya kueri dan data mentah.
        """
        llm = get_llm_adapter(model_name=model_name)

        # Validasi prompt
        validation_prompt = QUESTION_CLASSIFICATION_PROMT.format(nl_query=nl_query)
        validation_response = await llm.ainvoke(validation_prompt)
        if "data_perusahaan" not in validation_response.content.lower():
            raise ValueError("Pertanyaan tidak relevan dengan data perusahaan.")

        # Panggil helper untuk mendapatkan SQL dan data
        sanitized_sql, data_raw = await self._generate_and_execute_sql(nl_query, llm)

        return {"query": sanitized_sql, "data_raw": data_raw}

# --- Singleton Pattern (tidak berubah) ---
nl2sql_service_instance = NL2SQLService()

def get_nl2sql_service() -> NL2SQLService:
    return nl2sql_service_instance