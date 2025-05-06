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