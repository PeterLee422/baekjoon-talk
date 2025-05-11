# app/crud/user.py

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.user import User
from typing import Annotated
from uuid import uuid4

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

# User Profile 수정
async def update_user_profile(
        session: AsyncSession,
        user_id: str,
        username: str | None = None,
        # about: str | None = None
) -> User:
    user = await session.get(User, user_id)
    if not user:
        raise ValueError("User not found")
    
    if username:
        user.username = username
    #if about is not None:
    #    user.about = about
    
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