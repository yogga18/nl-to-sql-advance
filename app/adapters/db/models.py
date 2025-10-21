from sqlalchemy import (
    String, TIMESTAMP, ForeignKey, Enum, TEXT, INT, BOOLEAN, Integer
)
from sqlalchemy.orm import relationship, Mapped, mapped_column 
from typing import Optional, List
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nip: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    kode_unit: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, default=datetime.utcnow, nullable=True)
    chat_rooms: Mapped[List["ChatRoom"]] = relationship(back_populates="user")

class ChatRoom(Base):
    __tablename__ = "chat_rooms"
    room_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, default=datetime.utcnow, nullable=True)

    user: Mapped["User"] = relationship(back_populates="chat_rooms")
    messages: Mapped[List["ChatMessage"]] = relationship(back_populates="room", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    message_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(Integer, ForeignKey("chat_rooms.room_id", ondelete="CASCADE"), nullable=False, index=True)
    sender: Mapped[str] = mapped_column(Enum('user', 'ai', name='sender_enum'), nullable=False)
    message_text: Mapped[str] = mapped_column(TEXT, nullable=False)
    token_user: Mapped[Optional[int]] = mapped_column(INT, nullable=True)
    timestamp: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, default=datetime.utcnow, index=True, nullable=True)
    in_reply_to_message_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("chat_messages.message_id", ondelete="SET NULL"), nullable=True)

    room: Mapped["ChatRoom"] = relationship(back_populates="messages")
    llm_run: Mapped[Optional["LLMRun"]] = relationship(back_populates="user_message", uselist=False, cascade="all, delete-orphan") # Optional karena relasi one-to-one/zero

class LLMRun(Base):
    __tablename__ = "llm_runs"
    run_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_message_id: Mapped[int] = mapped_column(Integer, ForeignKey("chat_messages.message_id", ondelete="CASCADE"), unique=True, nullable=False)
    retrieved_context_knowledge: Mapped[Optional[str]] = mapped_column(TEXT, nullable=True)
    retrieved_context_memory: Mapped[Optional[str]] = mapped_column(TEXT, nullable=True)
    generated_sql: Mapped[Optional[str]] = mapped_column(TEXT, nullable=True)
    llm_model_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    llm_provider_user: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    token_llm: Mapped[Optional[int]] = mapped_column(INT, nullable=True)
    is_success: Mapped[Optional[bool]] = mapped_column(BOOLEAN, default=False, nullable=True)
    endpoint_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # Kolom latency baru juga diupdate
    latency_total_ms: Mapped[Optional[int]] = mapped_column(INT, nullable=True)
    latency_classification_ms: Mapped[Optional[int]] = mapped_column(INT, nullable=True)
    latency_rag_ms: Mapped[Optional[int]] = mapped_column(INT, nullable=True)
    latency_sql_generation_ms: Mapped[Optional[int]] = mapped_column(INT, nullable=True)
    latency_sql_execution_ms: Mapped[Optional[int]] = mapped_column(INT, nullable=True)
    latency_reasoning_ms: Mapped[Optional[int]] = mapped_column(INT, nullable=True)
    timestamp: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, default=datetime.utcnow, nullable=True)

    user_message: Mapped["ChatMessage"] = relationship(back_populates="llm_run")