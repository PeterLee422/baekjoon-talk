# app/crud/message.py

import datetime as dt
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.message import Message
from typing import Annotated
from uuid import uuid4

async def create_message(
        session: AsyncSession,
        conv_id: str,
        sender: str,
        content: str
) -> Message:
    """
    Message 생성
    - Conversation ID (특정 conversation에 종속되어야 함)
    - Sender (User / LLM(bot))
    - Content (메시지 내용)
    """
    message = Message(
        id=str(uuid4()),
        conv_id=conv_id,
        created_at=dt.datetime.now(),
        sender=sender,
        content=content
    )
    session.add(message)
    await session.commit()
    await session.refresh(message)
    return message

async def get_message(
        session: AsyncSession,
        message_id: str
) -> Message | None:
    """
    Returns Message by Message ID
    """
    statement = select(Message).where(Message.id == message_id)
    result = await session.exec(statement)
    return result.first()

async def list_messages_by_conversation(
        session: AsyncSession,
        conv_id: str
) -> list[Message]:
    """
    Returns All messages of Conversation (conv_id)
    """
    statement = (
        select(Message)
        .where(Message.conv_id == conv_id)
        .order_by(Message.created_at.asc())
    )
    #statement = select(Message).where(Message.conv_id == conv_id)
    result = await session.exec(statement)
    return result.all()

async def delete_messages_by_conversation(
        session: AsyncSession,
        conv_id: str
) -> None:
    statement = select(Message).where(Message.conv_id == conv_id)
    result = await session.exec(statement)
    messages = result.all()
    for msg in messages:
        await session.delete(msg)
    
    await session.commit()