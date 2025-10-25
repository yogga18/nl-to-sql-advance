from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Dict, Any

from ...services.nl2sql_service import get_nl2sql_service, NL2SQLService
from .dependencies import get_db, verify_token
from ...core.memory_providers import get_window_memory # Impor provider memori
from langchain.memory import ConversationBufferWindowMemory # Impor tipe memori
from ...core.sql_chat_history import SQLChatMessageHistory
from langchain.schema import get_buffer_string

# Definisikan router dengan prefix, tags, dan dependensi keamanan global
router = APIRouter(
    prefix="/nl-to-sql",
    tags=["NL-to-SQL"],
    # dependencies=[Depends(verify_token)]
)

# Definisikan bentuk payload yang diharapkan dari user
class NLQueryRequest(BaseModel):
    prompt: str
    model: str
    nip: str
    kode_unit: str
    display_name: str
    room_id: int

@router.post("/sql-data-reasoning", response_model=Dict[str, Any])
async def handle_nl_query(
    request: Request, # jika ingin akses informasi request request.state.user 
    request_body: NLQueryRequest,
    nl2sql_service: NL2SQLService = Depends(get_nl2sql_service),
    db: AsyncSession = Depends(get_db),
    BackgroundTasks: BackgroundTasks = BackgroundTasks(),
):
    try:
        result = await nl2sql_service.execute_flow(
            nl_query=request_body.prompt,
            model_name=request_body.model,
            room_id=request_body.room_id,
            nip=request_body.nip,
            kode_unit=request_body.kode_unit,
            display_name=request_body.display_name,
            endpoint_path=str(request.url.path),
            db_session=db,
            background_tasks=BackgroundTasks,
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

@router.post("/sql-data", response_model=Dict[str, Any])
async def handle_simple_nl_query(
    request: Request,
    request_body: NLQueryRequest,
    nl2sql_service: NL2SQLService = Depends(get_nl2sql_service),
    db: AsyncSession = Depends(get_db),
    BackgroundTasks: BackgroundTasks = BackgroundTasks()
):
    try:
        result = await nl2sql_service.generate_sql_and_data(
            nl_query=request_body.prompt,
            model_name=request_body.model,
            nip=request_body.nip,
            kode_unit=request_body.kode_unit,
            display_name=request_body.display_name,
            room_id=request_body.room_id,
            endpoint_path=str(request.url.path),
            db_session=db,
            background_tasks=BackgroundTasks,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="Terjadi kesalahan internal pada server."
)
    
# CONVERSATION HISTORY USING SQL (MySQL)
@router.post("/sql-data-reasoning-converstation", response_model=Dict[str, Any])
async def handle_nl_query_converstation(
    request: Request,
    request_body: NLQueryRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    nl2sql_service: NL2SQLService = Depends(get_nl2sql_service),
):
    try:
        room_id_from_body = request_body.room_id

        # Langkah 1: Buat backend history
        message_history = SQLChatMessageHistory(session=db, room_id=room_id_from_body)

        # Langkah 2: Muat pesan terakhir (await karena .messages async)
        # Ambil sejumlah pesan (misal 6 = 3 pasang)
        k = 2
        list_of_langchain_messages = await message_history.messages # Ambil history dari DB
        
        # Langkah 3: Format menjadi string (ambil K interaksi terakhir)
        chat_history_string = get_buffer_string(list_of_langchain_messages[-k*2:]) # Format K terakhir

        print("Chat History String:")
        print(chat_history_string)

        # Langkah 4: Panggil service dengan data yang diperlukan
        result = await nl2sql_service.execute_flow_conversation(
            nl_query=request_body.prompt,
            model_name=request_body.model,
            # user_info=current_user,
            room_id=room_id_from_body,
            endpoint_path=str(request.url.path),
            db_session=db,
            background_tasks=background_tasks,
            # Teruskan string history & backend history
            chat_history_string=chat_history_string,
            message_history_backend=message_history
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
