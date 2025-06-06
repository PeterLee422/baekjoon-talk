# app/models/conversation.py

from sqlmodel import SQLModel, Field
from typing import Annotated
from uuid import uuid4

class Conversation(SQLModel, table=True):
    __tablename__ = "conversation"

    id: Annotated[str, Field(default_factory=lambda: str(uuid4()), primary_key=True)]
    owner_id: str   # User ID
    title: str      # Conversation Title
    last_modified: str