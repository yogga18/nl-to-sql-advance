from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class ChatMessageBase(BaseModel):
    room_id: int 
    sender: str
    message_text: str
    token_user: Optional[int] = None

class ChatMessageCreate(ChatMessageBase):
    in_reply_to_message_id: Optional[int] = None

class ChatMessageRead(ChatMessageBase):
    message_id: int
    timestamp: datetime
    in_reply_to_message_id: Optional[int] = None
    # class Config:
    #     orm_mode = True
    model_config = ConfigDict(from_attributes=True)

class LLMRunCreate(BaseModel):
    user_message_id: int
    retrieved_context_knowledge: Optional[str] = None
    retrieved_context_memory: Optional[str] = None
    generated_sql: Optional[str] = None
    llm_model_used: Optional[str] = None
    llm_provider_user: Optional[str] = None
    token_llm: Optional[int] = None
    is_success: Optional[bool] = False
    endpoint_path: Optional[str] = None
    latency_total_ms: Optional[int] = None
    latency_classification_ms: Optional[int] = None
    latency_rag_ms: Optional[int] = None
    latency_sql_generation_ms: Optional[int] = None
    latency_sql_execution_ms: Optional[int] = None
    latency_reasoning_ms: Optional[int] = None

class LLMRunRead(LLMRunCreate):
    run_id: int
    timestamp: datetime
    # class Config:
    #     orm_mode = True
    model_config = ConfigDict(from_attributes=True)