# app/models/user_activity.py

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime
from typing import Annotated
from uuid import uuid4
import datetime as dt
from app.core.configuration import settings

class UserActivity(SQLModel, table=True):
    __tablename__ = "user_activity"

    id: Annotated[str, Field(default_factory=lambda: str(uuid4()), primary_key=True)]
    user_id: Annotated[str, Field(foreign_key="user.id", index=True)]
    event_type: str = Field(description="활동 유형: 'login', 'logout', 'session_start', 'session_end'")
    timestamp: dt.datetime = Field(default_factory=lambda: dt.datetime.now(settings.KST), sa_column=Column(DateTime(timezone=True)))
    session_id: str | None = Field(default=None, index=True, description="로그인 ~ 로그아웃까지 사용될 세션 ID")
    duration_seconds: int | None = Field(default=None, description="세션 지속 시간 (seconds), session_end 시 업데이트")