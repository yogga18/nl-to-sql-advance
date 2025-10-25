from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from . import models, schemas
from typing import List, Optional

# --- Chat Messages ---
async def create_chat_message(db: AsyncSession, message: schemas.ChatMessageCreate) -> models.ChatMessage:
    """Reusable function to INSERT a new chat message."""
    db_message = models.ChatMessage(**message.dict())
    db.add(db_message)
    await db.commit()
    await db.refresh(db_message)
    return db_message

async def get_chat_messages_by_room(db: AsyncSession, room_id: int, limit: int = 10) -> List[models.ChatMessage]:
    """Reusable function to SELECT chat messages for a room, newest first."""
    stmt = (
        select(models.ChatMessage)
        .where(models.ChatMessage.room_id == room_id)
        .order_by(desc(models.ChatMessage.timestamp))
        .limit(limit)
    )
    result = await db.execute(stmt)
    messages = result.scalars().all()
    return list(reversed(messages))  # Kembalikan dalam urutan lama ke baru

# --- LLM Runs ---
async def create_llm_run(db: AsyncSession, run_data: schemas.LLMRunCreate) -> models.LLMRun:
    """Reusable function to INSERT LLM run details."""
    db_run = models.LLMRun(**run_data.dict())
    db.add(db_run)
    await db.commit()
    await db.refresh(db_run)
    return db_run

async def get_llm_run_by_message_id(db: AsyncSession, user_message_id: str) -> Optional[models.LLMRun]:
    """Reusable function to SELECT LLM run details based on user message."""
    stmt = select(models.LLMRun).where(models.LLMRun.user_message_id == user_message_id)
    result = await db.execute(stmt)
    return result.scalars().first()