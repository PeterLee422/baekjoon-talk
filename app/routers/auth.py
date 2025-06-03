# app/routers/auth.py

import datetime as dt
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.database import get_session
from app.schemas.user import UserCreate, UserOut, Token, RefreshToken, ProfileUpdate, UserProfileUpdateOnFirstLogin
from app.core.security import create_access_token, create_refresh_token, get_password_hash, verify_password, decode_access_token
from app.crud import user as crud_user
from app.crud import conversation as crud_conv
from app.crud import message as crud_msg
from app.dependencies import get_current_user

router = APIRouter()

@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def signup(
    user_in: UserCreate,
    session: Annotated[AsyncSession, Depends(get_session)]
):
    """
    신규 사용자 회원가입 기능
    """
    # 중복 체크하기
    existing_user = await crud_user.get_user_by_email(session, user_in.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="User (email) already registered")
    
    # Hashing, DB에 저장
    hashed_pw = get_password_hash(user_in.password)
    new_user = await crud_user.create_user(
        session=session,
        email=user_in.email,
        username=user_in.username,
        hashed_password=hashed_pw,
        photo_url=None
    )

    return UserOut.model_validate(new_user)


@router.post("/token", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(get_session)]
):
    """
    토큰(OAuth2, bearer) 방식을 통한 로그인 기능
    """
    db_user = await crud_user.get_user_by_email(session, form_data.username)
    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    first_login = db_user.first_login_at is None

    # 최초 로그인 시 시간 기록 -> 기록은 다른 라우터에서 하기로!
    # if db_user.first_login_at is None:
    #     db_user.first_login_at = dt.datetime.now()
    #     session.add(db_user)
    #     await session.commit()
    
    # JWT Access Token 생성
    access_token = create_access_token(
        data={"sub": db_user.email},
    )

    refresh_token = create_refresh_token(
        data={"sub": db_user.email},
    )

    return Token(access_token=access_token, refresh_token=refresh_token, first_login=first_login)

@router.post("/confirm-first-login", response_model=UserOut)
async def confirm_first_login(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[UserOut, Depends(get_current_user)],
    profile_data: UserProfileUpdateOnFirstLogin
):
    """
    첫 로그인 확정 (설문조사 이후에 호출)
    """
    if user.first_login_at is not None:
        raise HTTPException(status_code=400, detail="First login already confirmed.")
    
    try:
        updated_user = await crud_user.update_user_profile(
            session=session,
            user_id=user.id,
            user_level=profile_data.user_level,
            goal=profile_data.goal,
            interested_tags=profile_data.interested_tags
        )
        updated_user = await crud_user.update_first_login_at(session, user.id, dt.datetime.now())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to confirm first login and update profile: {e}")

    #return {"message": "First login confirmed", "first_login_at": updated_user.first_login_at}
    return UserOut.model_validate(updated_user)


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_refresh: RefreshToken
):
    """
    Refresh Token을 통해 Access Token 생성
    -> User 쪽에서 Refresh Token을 보내면 검증 후 새로운 Access Token 반환
    """
    payload = decode_access_token(token_refresh.refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    access_token = create_access_token({"sub": payload["sub"]})

    return Token(access_token=access_token)


@router.get("/me", response_model=UserOut)
async def read_users_me(
    current_user: Annotated[UserOut, Depends(get_current_user)]
):
    """
    User 정보를 Token에서 추출해서 반환
    """
    return current_user

# 1. 회원 정보 수정
@router.put("/me", response_model=UserOut)
async def update_profile(
    update: ProfileUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[UserOut, Depends(get_current_user)]
):
    """
    로그인한 유저의 회원 정보 수정
    """
    #updated_user = crud_user.
    try:
        updated_user = await crud_user.update_user_profile(
            session,
            user_id=user.id,
            username=update.username,
            user_level=update.user_level,
            goal=update.goal,
            interested_tags=update.interested_tags
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update user profile : {e}")

    return UserOut.model_validate(updated_user)


@router.post("/me/photo", response_model=UserOut)
async def upload_photo(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    user = Depends(get_current_user)
):
    """
    이미지 파일 업로드하기
    """
    path = f"static/img/{user.username}.png"

    with open(path, "wb") as f:
        f.write(file.file.read())

    updated_user = await crud_user.update_user_photo(session, user_id=user.id, photo_url=f"/{path}")

    return UserOut.model_validate(updated_user)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[UserOut, Depends(get_current_user)]
):
    """
    회원 탈퇴: 유저 및 관련 대화, 메시지 모두 삭제!
    """
    # 대화 및 메시지 삭제
    conversations = await crud_conv.list_user_conversation(session, owner_id=user.id)
    for conv in conversations:
        await crud_msg.delete_messages_by_conversation(session, conv_id=conv.id)
        await crud_conv.delete_conversation(session, conv_id=conv.id)

    # 유저 삭제
    await crud_user.delete_user(session, user_id=user.id)
    
    return None