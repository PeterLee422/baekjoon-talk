# app/models/friend.py

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime
from typing import Annotated
from uuid import uuid4
import datetime as dt
from app.core.configuration import settings

class FriendRequest(SQLModel, table=True):
    __tablename__ = "friend_request"

    id: Annotated[str, Field(default_factory=lambda: str(uuid4()), primary_key=True)]
    sender_id: Annotated[str, Field(foreign_key="user.id")]
    receiver_id: Annotated[str, Field(foreign_key="user.id")]
    created_at: Annotated[dt.datetime, Field(default_factory=lambda: dt.datetime.now(settings.KST), sa_column=Column(DateTime(timezone=True)))]
    status: Annotated[str, Field(default="pending")] # "pending", "accepted", "rejected"

class Friend(SQLModel, table=True):
    __tablename__ = "friend"

    id: Annotated[str, Field(default_factory=lambda: str(uuid4()), primary_key=True)]
    user_id: Annotated[str, Field(foreign_key="user.id")]
    friend_id: Annotated[str, Field(foreign_key="user.id")]
    created_at: Annotated[dt.datetime, Field(default_factory=lambda: dt.datetime.now(settings.KST), sa_column=Column(DateTime(timezone=True)))]