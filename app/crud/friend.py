# app/crud/friend.py

from fastapi import HTTPException
from sqlmodel import select, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.friend import FriendRequest, Friend
from typing import Annotated
from uuid import uuid4
import datetime as dt

async def create_friend_request(
        session: AsyncSession,
        sender_id: str,
        receiver_id: str
) -> FriendRequest:
    """
    FriendRequest 생성
    """
    statement = select(FriendRequest).where(
        (FriendRequest.sender_id == sender_id) &
        (FriendRequest.receiver_id == receiver_id) &
        (FriendRequest.status == "pending")
    )
    existing = await session.exec(statement)
    if existing.first():
        raise HTTPException(status_code=400, detail="Friend request already exists")
    
    friend_request = FriendRequest(
        id=str(uuid4()),
        sender_id=sender_id,
        receiver_id=receiver_id,
        status="pending",
        created_at=dt.datetime.now()
    )

    session.add(friend_request)
    await session.commit()
    await session.refresh(friend_request)
    return friend_request

async def get_friend_request_by_id(
        session: AsyncSession,
        request_id: str
) -> FriendRequest | None:
    return await session.get(FriendRequest, request_id)

async def accept_friend_request(
        session: AsyncSession,
        request_id: str,
        user_id: str
) -> FriendRequest:
    """
    FriendRequest 수락
    """
    request = await session.get(FriendRequest, request_id)
    
    if not request:
        raise HTTPException(status_code=404, detail="Friend request not found")
    if request.receiver_id != user_id:
        raise HTTPException(status_code=403, detail="You are not the receiver of this request")
    if request.status != "pending":
        raise HTTPException(status_code=400, detail="This request has already been processed")

    request.status = "accepted"

    session.add_all([
        Friend(id=str(uuid4()), user_id=request.sender_id, friend_id=request.receiver_id),
        Friend(id=str(uuid4()), user_id=request.receiver_id, friend_id=request.sender_id),
        request
    ])

    await session.commit()
    await session.refresh(request)
    return request
    
async def reject_friend_request(
        session: AsyncSession,
        request_id: str,
        user_id: str
) -> FriendRequest:
    """
    FriendRequest 거절
    """
    request = await session.get(FriendRequest, request_id)
    
    if not request:
        raise HTTPException(status_code=404, detail="Friend request not found")
    if request.receiver_id != user_id:
        raise HTTPException(status_code=403, detail="You are not the receiver of this request")
    if request.status != "pending":
        raise HTTPException(status_code=400, detail="This request has already been processed")

    request.status = "rejected"
    session.add(request)
    await session.commit()
    await session.refresh(request)
    return request
    
async def list_received_requests(
        session: AsyncSession,
        user_id: str
) -> list[FriendRequest]:
    """
    받은 친구 요청 목록 조회
    """
    statement = select(FriendRequest).where(
        FriendRequest.receiver_id == user_id
    )
    result = await session.exec(statement)
    return result.all()

async def list_sent_requests(
        session: AsyncSession,
        user_id: str
) -> list[FriendRequest]:
    """
    보낸 친구 요청 목록 조회
    """
    statement = select(FriendRequest).where(
        FriendRequest.sender_id == user_id
    )
    result = await session.exec(statement)
    return result.all()

async def list_friends(
        session: AsyncSession,
        user_id: str
) -> list[Friend]:
    """
    친구 목록 조회
    """
    statement = select(Friend).where(
        Friend.user_id == user_id
    )
    result = await session.exec(statement)
    return result.all()

async def delete_friend(
        session: AsyncSession,
        user_id: str,
        friend_id: str
) -> None:
    """
    친구 삭제
    """
    for uid, fid in [(user_id, friend_id), (friend_id, user_id)]:
        statement = select(Friend).where(
            Friend.user_id == uid,
            Friend.friend_id == fid
        )
        result = await session.exec(statement)
        friend = result.first()
        if friend:
            session.delete(friend)
    await session.commit()
