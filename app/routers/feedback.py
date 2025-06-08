# app/routers/feedback.py

from typing import Annotated
from collections import Counter

from fastapi import APIRouter, Depends
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.database import get_session
from app.schemas.user import UserOut
from app.schemas.feedback import UserFeedbackStats, CodeErrorStats
from app.crud import user as crud_user
from app.crud import user_keyword as crud_user_keyword
from app.dependencies import get_current_user
from app.models.user_activity import UserActivity

router = APIRouter()

@router.get("/user-stats", response_model=UserFeedbackStats)
async def get_user_feedback_stats(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[UserOut, Depends(get_current_user)]
):
    """
    피드백 세션
    - 힌트 요청 횟수 (코드 분석 요쳥)
    - LLM이 분석한 사용자의 실수 (가장 많은 오류 종류)
    - 총 접속 횟수 및 평균 접속 시간
    """
    user_id = user.id

    # 1. 힌트 요청 횟수 (code_analysis)
    db_user = await crud_user.get_user_by_email(session, user.email)
    total_code_analysis = db_user.code_analysis if db_user else 0

    # 2. LLM이 분석한 사용자의 실수 (top_code_errors)
    code_error_keywords_list = [
        "time_complexity_over",
        "space_complexity_over",
        "syntax_error",
        "edge_case_error",
        "readability_issue",
        "off_by_one_error"
    ]

    all_user_keywords_records = await crud_user_keyword.get_user_keywords_by_user(session, user_id=user_id)
    error_counts = Counter()
    for keyword in all_user_keywords_records:
        if keyword.keyword in code_error_keywords_list:
            error_counts[keyword.keyword] += 1
    
    top_code_errors = [
        CodeErrorStats(error_type=error_type, count=count)
        for error_type, count in error_counts.most_common(3) # 최대 3개
    ]
    
    # 3. 접속 횟수 / 평균 접속 시간
    statement_logins = select(func.count(UserActivity.id)).where(
        UserActivity.user_id == user_id,
        UserActivity.event_type == "session_start"
    )
    total_logins_result = await session.exec(statement_logins)
    total_logins = total_logins_result.one_or_none()
    total_logins = total_logins if total_logins is not None else 0

    statement_duration = select(func.avg(UserActivity.duration_seconds)).where(
        UserActivity.user_id == user_id,
        UserActivity.event_type == "session_end",
        UserActivity.duration_seconds.is_not(None)
    )
    avg_duration_seconds_result = await session.exec(statement_duration)
    avg_duration_seconds = avg_duration_seconds_result.one_or_none()
    avg_duration_seconds = avg_duration_seconds if avg_duration_seconds is not None else 0.0


    average_session_duration_minutes = float(avg_duration_seconds) / 60.0 if avg_duration_seconds else 0.0

    return UserFeedbackStats(
        total_code_analysis=total_code_analysis,
        top_code_errors=top_code_errors,
        total_logins=total_logins,
        average_session_duration_minutes=average_session_duration_minutes
    )