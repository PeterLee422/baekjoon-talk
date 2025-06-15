# app/models/conversation.py

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime
from typing import Annotated
from uuid import uuid4
import datetime as dt
from app.core.configuration import settings

class Conversation(SQLModel, table=True):
    __tablename__ = "conversation"

    id: Annotated[str, Field(default_factory=lambda: str(uuid4()), primary_key=True)]
    owner_id: Annotated[str, Field(foreign_key="user.id")]   # User ID
    title: str      # Conversation Title
    last_modified: Annotated[dt.datetime, Field(default_factory=lambda: dt.datetime.now(settings.KST), sa_column=Column(DateTime(timezone=True)))]
    last_problem_number: int | None = Field(default=None, description="대화에서 가장 최근에 입력된 문제 번호")
    last_problem_info: str | None = Field(default=None, description="대화에서 가장 최근에 입력된 문제 정보 (text)")
    last_code_content: str | None = Field(default=None, description="대화에서 가장 최근에 입력된 코드 내용")
    last_code_language: str | None = Field(default=None, description="대화에서 가장 최근에 입력된 코드 언어")