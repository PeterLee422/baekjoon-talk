# app/schemas/chat.py

import datetime as dt
from typing import Annotated
from pydantic import BaseModel, Field

class ConversationCreate(BaseModel):
    title: str | None = Field(None, example="Daily Chat")

class ConversationOut(BaseModel):
    id: str
    title: str
    last_modified: dt.datetime # ISO8601
    class Config:
        from_attributes = True

class MessageIn(BaseModel):
    content: Annotated[str, Field(None, example="Hello, how are you?")]
    voice: bytes | None = None
    code: str | None = None
    language: str | None = None

class MessageOut(BaseModel):
    id: str
    sender: str
    content: str
    keywords: list[str] | None = None
    # audio_base64: str | None = None

class ConversationOutWithFirstMessage(BaseModel):
    id: str
    title: str
    last_modified: dt.datetime
    first_message: MessageOut
    class Config:
        from_attributes = True