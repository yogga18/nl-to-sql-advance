from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, messages_from_dict, message_to_dict
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import json

# Import CRUD, Skema, dan Model Anda
from ..adapters.db import crud, schemas, models

class SQLChatMessageHistory(BaseChatMessageHistory):
    """
    Implementasi Chat Message History yang menyimpan/mengambil pesan
    dari database SQL (MySQL) menggunakan fungsi CRUD async.
    """
    def __init__(self, session: AsyncSession, room_id: int):
        self.session = session
        self.room_id = room_id
        self._latest_user_message_id: Optional[int] = None 

    @property
    async def messages(self) -> List[BaseMessage]:
        """Ambil pesan dari DB dan konversi ke format LangChain."""

        db_messages_orm: List[models.ChatMessage] = await crud.get_chat_messages_by_room(
            self.session, self.room_id, limit=50
        )

        items = []
        for msg_orm in db_messages_orm:
            try:
                msg_schema = schemas.ChatMessageRead.from_orm(msg_orm)
                item = {
                    "type": "human" if msg_schema.sender == 'user' else "ai",
                    "data": {
                        "content": msg_schema.message_text,
                        "additional_kwargs": {
                            "message_id": msg_schema.message_id,
                            "timestamp": msg_schema.timestamp.isoformat() if msg_schema.timestamp else None
                        },
                    },
                }
                items.append(item)
            except Exception as e:
                print(f"Error converting message {msg_orm.message_id} to dict: {e}")

        retrieved_messages = messages_from_dict(items)
        return retrieved_messages

    async def add_message(self, message: BaseMessage) -> Optional[models.ChatMessage]:
        sender = 'user' if message.type == 'human' else 'ai'
        reply_to_id = None

        if sender == 'ai' and self._latest_user_message_id is not None:
            reply_to_id = self._latest_user_message_id
            self._latest_user_message_id = None

        message_to_save = schemas.ChatMessageCreate(
            room_id=self.room_id,
            sender=sender,
            message_text=str(message.content),
            in_reply_to_message_id=reply_to_id
        )

        saved_message: Optional[models.ChatMessage] = None

        try:
            saved_message = await crud.create_chat_message(self.session, message_to_save)

            if sender == 'user' and saved_message:
                self._latest_user_message_id = saved_message.message_id

        except Exception as e:
            print(f"Error saving message in SQLChatMessageHistory: {e}")

        return saved_message

    async def clear(self) -> None:
        """Hapus semua pesan untuk room ini."""
        print(f"Clearing history for room_id {self.room_id}...")
        # Implementasi penghapusan jika diperlukan (hati-hati!)
        # await self.session.execute(delete(models.ChatMessage).where(models.ChatMessage.room_id == self.room_id))
        # await self.session.commit()
        print(f"Clear history function called for room_id {self.room_id}.")