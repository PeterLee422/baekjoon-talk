# app/crud/user_keyword.py

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.user_keyword import UserKeyword
from uuid import uuid4
import datetime as dt

async def create_user_keyword(
    session: AsyncSession,
    user_id: str,
    conversation_id: str,
    keyword: str
) -> UserKeyword:
    """
    하나의 키워드를 DB에 저장장
    """
    user_keyword = UserKeyword(
        id=str(uuid4()),
        user_id=user_id,
        conversation_id=conversation_id,
        keyword=keyword,
        created_at=dt.datetime.now()
    )
    session.add(user_keyword)
    await session.commit()
    await session.refresh(user_keyword)
    return user_keyword

async def create_multiple_user_keywords(
    session: AsyncSession,
    user_id: str,
    conversation_id: str,
    keywords: list[str]
) -> list[UserKeyword]:
    """
    여러 개의 키워드(list)를 DB에 저장
    """
    user_keywords = []
    for keyword in keywords:
        user_keywords.append(UserKeyword(
            id=str(uuid4()),
            user_id=user_id,
            conversation_id=conversation_id,
            keyword=keyword,
            created_at=dt.datetime.now()
        ))
    session.add_all(user_keywords)
    await session.commit()
    for keyword_object in user_keywords:
        await session.refresh(keyword_object)
    return user_keywords

async def get_user_keywords_by_user(
        session: AsyncSession,
        user_id: str
) -> list[UserKeyword]:
    """
    특정 사용자의 모든 키워드 조회
    """
    statement = select(UserKeyword).where(UserKeyword.user_id == user_id)
    result = await session.exec(statement)
    return result.all()

async def delete_user_keywords(
        session: AsyncSession,
        user_id: str
) -> None:
    """
    특정 유저와 관련된 모든 키워드 정보 삭제
    """
    statement = select(UserKeyword).where(UserKeyword.user_id == user_id)
    result = await session.exec(statement)
    keywords = result.all()
    for keyword in keywords:
        await session.delete(keyword)
    await session.commit()

async def delete_user_keywords(
        session: AsyncSession,
        user_id: str
) -> None:
    """
    특정 유저와 관련된 모든 키워드 삭제
    """
    statement = select(UserKeyword).where(UserKeyword.user_id == user_id)
    result = await session.exec(statement)
    keywords = result.all()
    for keyword in keywords:
        await session.delete(keyword)
    await session.commit()

async def delete_user_keywords_by_conversation(
        session: AsyncSession,
        conv_id: str
) -> None:
    """
    특정 대화에 속한 모든 사용자의 키워드 삭제
    """
    statement = select(UserKeyword).where(UserKeyword.conversation_id == conv_id)
    result = await session.exec(statement)
    keywords = result.all()
    for keyword in keywords:
        await session.delete(keyword)
    await session.commit()