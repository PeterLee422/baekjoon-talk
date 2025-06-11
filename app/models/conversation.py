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