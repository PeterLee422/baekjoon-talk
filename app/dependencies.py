# app/dependencies.py

from typing import Annotated
from collections.abc import Generator
import datetime as dt

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.configuration import settings
from app.core.security import decode_access_token
from app.core.redis import get_redis_client
from app.db.database import get_session
from app.schemas.user import UserOut, TokenData
from app.crud import user as crud_user
from app.crud import user_activity as crud_user_activity

from app.services.boj_llmrec.llmrec import Session

REDIS_LAST_ACTIVE_PREFIX = "last_active:"
REDIS_SESSION_START_PREFIX = "session_start:"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

async def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)],
        session: Annotated[AsyncSession, Depends(get_session)]
) -> UserOut:
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Token"
        )
    email: str = payload.get("sub")    
    current_session_id: str | None = payload.get("session_id")
    db_user = await crud_user.get_user_by_email(session, email)
    
    if db_user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Heartbeat Logic (using Redis)
    # 사용자가 살아있는가
    if db_user.id and current_session_id:
        redis_client = get_redis_client()
        current_time = dt.datetime.now()

        await redis_client.set(f"{REDIS_LAST_ACTIVE_PREFIX}{db_user.id}", current_time.isoformat())
        session_start_key = f"{REDIS_SESSION_START_PREFIX}{db_user.id}:{current_session_id}"
        if not await redis_client.exists(session_start_key):
            await redis_client.set(session_start_key, current_time.isoformat())

    return UserOut.model_validate(db_user)