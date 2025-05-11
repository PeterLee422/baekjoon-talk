# app/dependencies.py

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import decode_access_token
from app.db.database import get_session
from app.schemas.user import UserOut
from app.crud import user as crud_user

from app.services.boj_llmrec.llmrec import Session

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
    db_user = await crud_user.get_user_by_email(session, email)
    
    if db_user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return UserOut.model_validate(db_user)