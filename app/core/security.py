# app/core/security.py

from fastapi import HTTPException
import datetime as dt
from typing import Annotated

import jwt
from passlib.context import CryptContext

from app.core.configuration import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(
        plain_password: str,
        hashed_password: str
) -> bool:
    """
    Password Verification
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(
        password: str
) -> str:
    """
    Plain Password를 Hashed Password로 변환
    """
    return pwd_context.hash(password)

def create_access_token(
        data: dict,
        expires_delta: dt.timedelta | None = None
) -> str:
    """
    JWT Token 생성
    """
    to_encode = data.copy()
    expire = dt.datetime.now() + (
        expires_delta or dt.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    encode_jwt: str = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encode_jwt

def create_refresh_token(
        data: dict
) -> str:
    """
    JWT Refresh Token 생성
    """
    to_encode = data.copy()
    expire = dt.datetime.now() + dt.timedelta(minutes=settings.ACCESS_TOKEN_REFRESH_MINUTES)
    to_encode.update({"exp": expire})
    encode_jwt: str = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encode_jwt

def decode_access_token(
        token: str
):
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None