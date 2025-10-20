from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Dict, Any

from ...services.nl2sql_service import get_nl2sql_service, NL2SQLService
from .dependencies import get_db, verify_token

# Definisikan router dengan prefix, tags, dan dependensi keamanan global
router = APIRouter(
    prefix="/nl2sql",
    tags=["NL-to-SQL"],
    # dependencies=[Depends(verify_token)]
)

# Definisikan bentuk payload yang diharapkan dari user
class NLQueryRequest(BaseModel):
    prompt: str
    model: str

@router.post("/query", response_model=Dict[str, Any])
async def handle_nl_query(
    request: Request, # jika ingin akses informasi request request.state.user 
    request_body: NLQueryRequest,
    nl2sql_service: NL2SQLService = Depends(get_nl2sql_service),
    # db: AsyncSession = Depends(get_db),
):
    try:
        result = await nl2sql_service.execute_flow(
            nl_query=request_body.prompt,
            model_name=request_body.model,
            # db_session=db,
            # username=current_user.get("username", "unknown")
        )
        return result
    except ValueError as e:
        # Menangani error yang diharapkan (misal: pertanyaan tidak valid, query berbahaya)
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        # Menangani error saat eksekusi SQL
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        # Menangkap semua error tak terduga lainnya untuk mencegah crash
        print(f"An unexpected error occurred: {e}") # Log error untuk debug
        raise HTTPException(status_code=500, detail="Terjadi kesalahan internal pada server.")