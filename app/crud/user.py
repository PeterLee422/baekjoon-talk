# app/crud/user.py

from sqlmodel import select, Session
from app.models.user import User
from typing import Annotated
from uuid import uuid4

def create_user(
        session: Session,
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
    session.commit()
    session.refresh(user)
    return user

def create_user_oauth(
        session: Session,
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
    session.commit()
    session.refresh(user)
    return user

def get_user_by_email(
        session: Session,
        email:str
) -> User | None:
    """
    Returns User by E-mail
    """
    statement = select(User).where(User.email == email)
    result = session.exec(statement)
    return result.first()

def get_user_by_username(
        session: Session,
        username: str
) -> User | None:
    """
    Returns User by User Name
    """
    statement = select(User).where(User.username == username)
    result = session.exec(statement)
    return result.first()

def update_user_profile(
        session: Session,
        user_id: str,
        username: str | None = None
) -> User:
    """
    유저 프로필 수정
    """
    user = session.get(User, user_id)
    if not user:
        raise ValueError("User not found")
    
    if username:
        user.username = username

    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def update_user_photo(
        session: Session,
        user_id: str,
        photo_url: str
) -> User | None:
    """
    Updates User Photo
    """
    user = session.get(User, user_id)
    if user:
        user.photo_url = photo_url
        session.add(user)
        session.commit()
        session.refresh(user)
    return user

def delete_user(
        session: Session,
        user_id: str
) -> User | None:
    """
    유저 정보 삭제
    """
    user = session.get(User, user_id)
    if user:
        session.delete(user)
        session.commit()
