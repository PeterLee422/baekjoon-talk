# app/routers/friend.py

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from app.schemas.user import UserOut
from app.schemas.friend import FriendRequestCreate, FriendRequestUpdate, FriendRequestOut, FriendOut
from app.dependencies import get_current_user
from app.db.database import get_session
from app.crud import user as crud_user
from app.crud import friend as crud_friend

router = APIRouter()

@router.post("/requests", response_model=FriendRequestOut)
async def create_friend_request(
    request: FriendRequestCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[UserOut, Depends(get_current_user)]
):
    """
    친구 요청 생성
    """
    if user.id == request.receiver_id:
        raise HTTPException(status_code=400, detail="Cannot add yourself as a friend")
    
    try:
        result = await crud_friend.create_friend_request(session, user.id, request.receiver_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return result

@router.put("/requests/{request_id}", response_model=FriendRequestOut)
async def update_friend_request(
    request_id: str,
    update: FriendRequestUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[UserOut, Depends(get_current_user)]
):
    """
    친구 요청 수락 또는 거절 (수신자만 사용하기)
    """
    request = await crud_friend.get_friend_request_by_id(session, request_id)

    if not request:
        raise HTTPException(status_code=404, detail="Friend request not found")
    if request.receiver_id != user.id:
        raise HTTPException(status_code=403, detail="You are not the receiver of this request")
    if request.status != "pending":
        raise HTTPException(status_code=400, detail="This request has already been processed")

    # try:
    #     if update.status == "accepted":
    #         await crud_friend.accept_friend_request(session, request_id, request_id)
    #     elif update.status == "rejected":
    #         await crud_friend.reject_friend_request(session, request_id, request_id)
    #     else:
    #         raise HTTPException(status_code=400, detail="Invalid request status")
    # except HTTPException as e:
    #     raise e
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=str(e))

    if update.status == "accepted":
        updated_request = await crud_friend.accept_friend_request(session, request_id, user.id)
    elif update.status == "rejected":
        updated_request = await crud_friend.reject_friend_request(session, request_id, user.id)
    else:
        raise HTTPException(status_code=400, detail="Invalid request status")
    
    return updated_request

@router.get("/requests/received", response_model=list[FriendRequestOut])
async def get_received_requests(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[UserOut, Depends(get_current_user)]
):
    """
    받은 친구 요청 목록
    """
    return await crud_friend.list_received_requests(session, user.id)

@router.get("/requests/sent", response_model=list[FriendRequestOut])
async def get_sent_requests(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[UserOut, Depends(get_current_user)]
):
    """
    보낸 친구 요청 목록
    """
    return await crud_friend.list_sent_requests(session, user.id)

@router.get("/search", response_model=list[UserOut])
async def serach_users(
    q: str = Query(..., min_length=2),
    session: AsyncSession = Depends(get_session),
    current_user: UserOut = Depends(get_current_user)
):
    """
    사용자 검색 (Username or Email)
    """
    users = await crud_user.search_users(session, q, exclude_id=current_user.id)
    return users

@router.get("/friends", response_model=list[FriendOut])
async def get_friend_list(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[UserOut, Depends(get_current_user)]
):
    """
    친구 목록
    """
    return await crud_friend.list_friends(session, user.id)

@router.delete("/friends/{friend_id}")
async def delete_friend(
    friend_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[UserOut, Depends(get_current_user)]
):
    """
    친구 삭제
    """
    try:
        await crud_friend.delete_friend(session, user.id, friend_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return {"detail": "Friend removed successfully"}