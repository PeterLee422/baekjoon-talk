# app/routers/auth.py

import datetime as dt
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from app.schemas.user import UserCreate, UserOut, Token, RefreshToken, ProfileUpdate
from app.core.security import create_access_token, create_refresh_token, get_password_hash, verify_password, decode_access_token
from app.crud import user as crud_user
from app.crud import conversation as crud_conv
from app.crud import message as crud_msg
from app.dependencies import get_current_user, get_session

router = APIRouter()

@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def signup(
    user_in: UserCreate,
    session: Annotated[Session, Depends(get_session)]
):
    """
    신규 사용자 회원가입 기능
    """
    # 중복 체크하기
    existing_user = crud_user.get_user_by_email(session, user_in.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="User (email) already registered")
    
    # Hashing, DB에 저장
    hashed_pw = get_password_hash(user_in.password)

    # User 생성
    new_user = crud_user.create_user(
        session=session,
        email=user_in.email,
        username=user_in.username,
        hashed_password=hashed_pw,
    )

    return UserOut(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        photo_url=new_user.photo_url
    )


@router.post("/token", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[Session, Depends(get_session)]
):
    """
    토큰(OAuth2, bearer) 방식을 통한 로그인 기능
    """
    db_user = crud_user.get_user_by_email(session, form_data.username)
    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # JWT Access Token 생성
    access_token = create_access_token(
        data={"sub": db_user.email},
        #expires_delta=dt.timedelta(minutes=),
    )

    refresh_token = create_refresh_token(
        data={"sub": db_user.email},
    )

    return Token(access_token=access_token, refresh_token=refresh_token)


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
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[UserOut, Depends(get_current_user)]
):
    """
    로그인한 유저의 회원 정보 수정
    """
    #updated_user = crud_user.
    updated_user = crud_user.update_user_profile(
        session,
        user_id=user.id,
        username=update.username
    )
    return UserOut(
        id=updated_user.id,
        username=updated_user.username,
        email=updated_user.email,
        photo_url=updated_user.photo_url
    )
# 2. 회원 탈퇴
@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[UserOut, Depends(get_current_user)]
):
    """
    회원 탈퇴: 유저 및 관련 대화, 메시지 모두 삭제!
    """
    # 대화 및 메시지 삭제
    conversations = crud_conv.list_user_conversation(session, owner_id=user.id)
    for conv in conversations:
        crud_msg.delete_messages_by_conversation(session, conv_id=conv.id)
        crud_conv.delete_conversation(session, conv_id=conv.id)

    # 유저 삭제
    crud_user.delete_user(session, user_id=user.id)
    
    return None

# 3. 비밀번호 재설정


@router.post("/me/photo", response_model=UserOut)
def upload_photo(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    user = Depends(get_current_user)
):
    """
    이미지 파일 업로드하기
    """
    path = f"static/img/{user.username}.png"

    with open(path, "wb") as f:
        f.write(file.file.read())

    updated_user = crud_user.update_user_photo(session, user_id=user.id, photo_url=f"/{path}")

    return UserOut(
        id=updated_user.id,
        username=updated_user.username,
        email=updated_user.email,
        photo_url=updated_user.photo_url
    )
