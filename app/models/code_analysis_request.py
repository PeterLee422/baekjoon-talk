# app/models/code_request_analysis.py

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime    
from typing import Annotated
from uuid import uuid4
import datetime as dt
from app.core.configuration import settings

class CodeAnalysisRequest(SQLModel, table=True):
    __tablename__ = "code_analysis_request"

    id: Annotated[str, Field(default_factory=lambda: str(uuid4()), primary_key=True)]
    user_id: Annotated[str, Field(foreign_key="user.id", index=True)]
    request_date: Annotated[dt.date, Field(index=True)]
    timestamp: Annotated[dt.datetime, Field(default_factory=lambda: dt.datetime.now(settings.KST), sa_column=Column(DateTime(timezone=True)))]
    request_type: str | None = Field(default=None, description="요청 종류 (hint, review, complexity, optimize, general)")