from typing import List, Dict, Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from ..adapters.db.database import engine # Import engine async kita

async def execute_select_query(query: str, db_engine: AsyncEngine = engine) -> List[Dict[str, Any]]:
    print(f"Mengeksekusi query: {query}")
    async with db_engine.connect() as connection:
        result_proxy = await connection.execute(text(query))
        # Konversi hasil menjadi format List[Dict] yang ringan dan universal
        return [dict(row._mapping) for row in result_proxy]