# app/crud/user_activity.py

from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.user_activity import UserActivity
from typing import Annotated
from uuid import uuid4
import datetime as dt
from app.core.configuration import settings

async def create_user_activity(
        session: AsyncSession,
        user_id: str,
        event_type: str,
        session_id: str | None = None
) -> UserActivity:
    """
    User 활동 레코드를 DB에 저장
    """
    user_activity = UserActivity(
        id=str(uuid4()),
        user_id=user_id,
        event_type=event_type,
        timestamp=dt.datetime.now(settings.KST),
        session_id=session_id
    )
    session.add(user_activity)
    await session.commit()
    await session.refresh(user_activity)
    return user_activity

async def get_latest_session_start(
        session: AsyncSession,
        user_id: str,
        session_id: str
) -> UserActivity | None:
    """
    특정 session ID의 가장 최근 'session_start' 활동 레코드 조회
    """
    statement = (
        select(UserActivity)
        .where(
            UserActivity.user_id == user_id,
            UserActivity.session_id == session_id,
            UserActivity.event_type == "session_start"
        )
        .order_by(UserActivity.timestamp.desc())
    )
    result = await session.exec(statement)
    return result.first()

async def update_user_activity_duration(
        session: AsyncSession,
        activity_id: str,
        duration_seconds: int
) -> UserActivity | None:
    """
    duration_seconds 업데이트 (세션 길이)
    """
    activity = await session.get(UserActivity, activity_id)
    if activity:
        activity.duration_seconds = duration_seconds
        session.add(activity)
        await session.commit()
        await session.refresh(activity)
    return activity

async def delete_user_activity(
        session: AsyncSession,
        user_id: str
) -> None:
    """
    특정 유저와 관련된 모든 activity 제거
    """
    statement = select(UserActivity).where(UserActivity.user_id == user_id)
    result = await session.exec(statement)
    activities = result.all()
    for activity in activities:
        await session.delete(activity)
    await session.commit()