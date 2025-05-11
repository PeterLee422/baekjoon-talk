# app/routers/google_auth.py

from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends
from google.oauth2 import id_token
from google.auth.transport import requests
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.configuration import settings
from app.core.security import create_access_token
from app.schemas.user import UserWithToken, GoogleToken
from app.crud import user as crud_user
from app.dependencies import get_session
#from app.db import fake_db

router = APIRouter()

@router.post("/google")
async def google_login(
        payload: GoogleToken,
        session: Annotated[AsyncSession, Depends(get_session)]
):
    """
    Google 인증 방식
    """
    try:
        info = id_token.verify_oauth2_token(
            payload.id_token,
            requests.Request(),
            audience=settings.GOOGLE_CLIENT_ID,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid Google ID Token: {e}")
    
    email = info["email"]
    username = info.get("name", email.split("@")[0])
    photo_url = info.get("picture")

    user = await crud_user.get_user_by_email(session, email)
    if not user:
        user = await crud_user.create_user_oauth(
            session=session,
            username=username,
            email=email,
            photo_url=photo_url
        )
    
    access_token = create_access_token({"sub": user.email})

    return UserWithToken(
        id=user.id,
        username=user.username,
        email=user.email,
        photo_url=photo_url,
        access_token=access_token
    )