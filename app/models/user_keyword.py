# app/models/user_keyword.py

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime
from typing import Annotated
from uuid import uuid4
import datetime as dt
from app.core.configuration import settings

class UserKeyword(SQLModel, table=True):
    __tablename__ = "user_keyword"

    id: Annotated[str, Field(default_factory=lambda: str(uuid4()), primary_key=True)]
    user_id: Annotated[str, Field(foreign_key="user.id", index=True)]
    conversation_id: Annotated[str, Field(foreign_key="conversation.id", index=True)]
    keyword: str
    created_at: Annotated[dt.datetime, Field(default_factory=lambda: dt.datetime.now(settings.KST), sa_column=Column(DateTime(timezone=True)))]