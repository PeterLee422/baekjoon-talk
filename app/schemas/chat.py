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
    content: Annotated[str, Field(None, example="내가 풀어보지 않은 문제 추천해줘.")]
    voice: bytes | None = None
    code: str | None = None
    language: str | None = None
    problem_info: str | None = Field(None, example="문제 정보 입력하기")
    problem_num: int | None = Field(None, description="문제 번호 입력하기 (ex. 1800 (integer))")
    request_type: str | None = Field(None, description="요청 종류 (hint, review, complexity, optimize)")

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