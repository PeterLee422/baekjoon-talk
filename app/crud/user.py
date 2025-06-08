# app/crud/user.py

from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.user import User
from typing import Annotated
from uuid import uuid4
import datetime as dt

async def create_user(
        session: AsyncSession,
        username: str,
        email: str,
        hashed_password: str,
        photo_url: str | None = None
) -> User:
    """
    User 생성
    - User Name
    - Email
    - Hashed Password
    - Photo URL (Optional)
    """
    user = User(
        id=str(uuid4()),
        email=email,
        username=username,
        hashed_password=hashed_password,
        photo_url=photo_url,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def create_user_oauth(
        session: AsyncSession,
        username: str,
        email: str,
        photo_url: str | None = None
) -> User:
    user = User(
        id=str(uuid4()),
        username=username,
        email=email,
        hashed_password="",
        photo_url=photo_url
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def get_user_by_email(
        session: AsyncSession,
        email: str
) -> User | None:
    """
    Returns User by E-mail
    """
    statement = select(User).where(User.email == email)
    result = await session.exec(statement)
    return result.first()

async def get_user_by_username(
        session: AsyncSession,
        username: str
) -> User | None:
    """
    Returns User by User Name
    """
    statement = select(User).where(User.username == username)
    result = await session.exec(statement)
    return result.first()

async def search_users(
        session: AsyncSession,
        query: str,
        exclude_id: str | None = None
) -> list[User]:
    """
    Search Users by Username or Email
    """
    statement = select(User).where(
        or_(
            User.username.ilike(f"%{query}%"),
            User.email.ilike(f"%{query}%")
        )
    )
    if exclude_id:
        statement = statement.where(User.id != exclude_id)
        
    result = await session.exec(statement)
    return result.all()

# first_login_at 수정
async def update_first_login_at(
        session: AsyncSession,
        user_id: str,
        timestamp: dt.datetime
) -> User:
    statement = select(User).where(User.id == user_id)
    result = await session.exec(statement)
    user = result.first()

    if not user:
        raise ValueError("User not found")
    
    user.first_login_at = timestamp
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

# User Profile 수정
async def update_user_profile(
        session: AsyncSession,
        user_id: str,
        username: str | None = None,
        user_level: str | None = None,
        goal: str | None = None,
        interested_tags: list[str] | None = None
        # about: str | None = None
) -> User:
    user = await session.get(User, user_id)
    if not user:
        raise ValueError("User not found")
    
    if username is not None:
        user.username = username
    #if about is not None:
    #    user.about = about
    if user_level is not None:
        user.user_level = user_level
    if goal is not None:
        user.goal = goal
    if interested_tags is not None:
        user.interested_tags = interested_tags
    
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def update_user_photo(
        session: AsyncSession,
        user_id: str,
        photo_url: str
) -> User | None:
    """
    Updates User Photo
    """
    user = await session.get(User, user_id)
    if user:
        user.photo_url = photo_url
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user

async def delete_user(
        session: AsyncSession,
        user_id: str
):
    user = await session.get(User, user_id)
    if user:
        await session.delete(user)
        await session.commit()

async def increment_code_analysis(
        session: AsyncSession,
        user_id: str
) -> User | None:
    """
    특정 사용자의 code_analysis (코드 분석/힌트 요청 횟수) 1 증가
    """
    user = await session.get(User, user_id)
    if user:
        user.code_analysis = (user.code_analysis or 0) + 1
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user