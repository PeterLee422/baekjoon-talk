# app/core/security.py

from fastapi import HTTPException
import datetime as dt
from typing import Annotated, Any

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
    
def create_password_reset_token(
        user_id: str,
        rev: int
) -> str:
    expire = dt.datetime.now(settings.KST) + dt.timedelta(minutes=30)
    to_encode: dict[str, Any] = {
        "sub": str(user_id),
        "rev": rev,
        "scope": "password_reset",
        "exp": expire,
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_password_reset_token(
        token: str
) -> dict:
    """
    비밀번호 재설정 토큰 검증
    - 만료 / 유효성 / scope 체크
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("scope") != "password_reset":
            raise jwt.InvalidTokenError("Invalid scope for password reset")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="비밀번호 재설정 토큰이 만료되었습니다.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="유효하지 않은 비밀번호 재설정 토큰입니다.")

def create_password_init_token(
        user_id: str
) -> str:
    """
    초기 비밀번호(or 강제 재등록)용 토큰 발급
    - scope: password_init
    - 최초 로그인시 비밀번호를 반드시 새로 설정하도록 유도할 때 사용
    """
    expire = dt.datetime.now(settings.KST) + dt.timedelta(minutes=60*24)
    to_encode = {
        "sub": str(user_id),
        "scope": "password_init",
        "exp": expire
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_password_init_token(
        token: str
) -> dict:
    """
    초기 비밀번호 토큰 검증
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("scope") != "password_init":
            raise jwt.InvalidTokenError("Invalid scope for password init")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="초기화 토큰이 만료되었습니다.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="유효하지 않은 초기화 토큰입니다.")