# app/crud/conversation.py

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.conversation import Conversation
from typing import Annotated
from uuid import uuid4
import datetime as dt
from app.core.configuration import settings

async def create_conversation(
        session: AsyncSession,
        owner_id: str,
        title: str
) -> Conversation:
    """
    Conversation 생성
    - 소유자 (User)
    - Title (대화 제목. 대화의 첫번째 질의로 변경하도록 구현하기)
    """
    #now = dt.datetime.now().isoformat()
    now = dt.datetime.now(settings.KST)
    #now = dt.datetime.utcnow()
    conversation = Conversation(
        id=str(uuid4()),
        owner_id=owner_id,
        title=title,
        last_modified=now,
    )
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    return conversation

async def get_conversation(
        session: AsyncSession,
        conversation_id: str
) -> Conversation | None:
    """
    Conversation ID로 대화를 찾아 반환하기 (Conversation)
    """
    statement = select(Conversation).where(Conversation.id == conversation_id)
    result = await session.exec(statement)
    return result.first()

async def update_last_modified(
        session: AsyncSession,
        conversation_id: str
) -> Conversation | None:
    """
    Update Last Modified Date-Time
    대화에 메시지가 추가될 때마다 호출하기
    """
    conversation = await session.get(Conversation, conversation_id)
    if conversation:
        #conversation.last_modified = dt.datetime.now().isoformat()
        #conversation.last_modified = dt.datetime.now(dt.timezone.utc)
        conversation.last_modified = dt.datetime.now(settings.KST)
        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)
    return conversation

async def update_latest_problem_info(
        session: AsyncSession,
        conversation_id: str,
        problem_number: int | None = None,
        problem_info: str | None = None
) -> Conversation | None:
    """
    대화의 가장 최근 문제 번호와 문제 정보 업데이트
    """
    conversation = await session.get(Conversation, conversation_id)
    if conversation:
        if problem_number is not None:
            conversation.last_problem_number = problem_number
        if problem_info is not None:
            conversation.last_problem_info = problem_info
        
        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)
    return conversation

async def list_user_conversation(
        session: AsyncSession,
        owner_id: str
) -> list[Conversation]:
    """
    Returns All Conversations (of a user)
    """
    statement = select(Conversation).where(Conversation.owner_id == owner_id).order_by(Conversation.last_modified.desc())
    result = await session.exec(statement)
    return result.all()

async def delete_conversation(
        session: AsyncSession,
        conv_id: str
) -> None:
    conversation = await session.get(Conversation, conv_id)
    if conversation:
        await session.delete(conversation)
        await session.commit()