# app/models/message.py

from sqlmodel import SQLModel, Field
from typing import Annotated
from uuid import uuid4
import datetime as dt

class Message(SQLModel, table=True):
    __tablename__ = "message"

    id: Annotated[str, Field(default_factory=lambda: str(uuid4()), primary_key=True)]
    conv_id: Annotated[str, Field(foreign_key="conversation.id")]
    created_at: Annotated[dt.datetime, Field(default_factory=lambda: dt.datetime.now())]
    sender: str
    content: str