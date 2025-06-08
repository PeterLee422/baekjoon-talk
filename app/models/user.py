# app/models/user.py

from sqlmodel import SQLModel, Field, JSON
from sqlalchemy import Column
from typing import Annotated
from uuid import uuid4
import datetime as dt

class User(SQLModel, table=True):
    __tablename__ = "user"

    id: Annotated[str, Field(default_factory=lambda: str(uuid4()), primary_key=True)]
    username: Annotated[str, Field(index=True)]
    email: Annotated[str, Field(unique=True, index=True)]
    hashed_password: str
    photo_url: str | None = None
    first_login_at: dt.datetime | None = None
    # Profile Field
    user_level: str | None = Field(default=None, description="'very low', 'low', 'medium', 'high', 'very high'")
    goal: str | None = Field(default=None, description="'coding test', 'contest', 'learning', 'hobby'")
    interested_tags: list[str] = Field(default_factory=list, sa_column=Column(JSON), description="(복수 선택 가능) 'DP', '그래프', '자료구조', '수학', '구현', '문자열', '탐욕법', '트리', '정렬'")
    # For Feedback
    code_analysis: int = Field(default=0, description="코드 분석 / 힌트 요청 횟수")