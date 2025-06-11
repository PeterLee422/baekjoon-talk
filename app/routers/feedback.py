# app/routers/feedback.py

import datetime as dt
from typing import Annotated
from uuid import uuid4
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.database import get_session
from app.schemas.user import UserOut
from app.schemas.feedback import UserFeedbackStats, RecommendedTagStats, CodeErrorStats
from app.core.security import create_access_token, create_refresh_token, get_password_hash, verify_password, decode_access_token
from app.core.redis import get_redis_client
from app.crud import user as crud_user
from app.crud import conversation as crud_conv
from app.crud import message as crud_msg
from app.crud import friend as crud_friend
from app.crud import user_keyword as crud_user_keyword
from app.crud import user_activity as crud_user_activity
from app.crud import code_analysis_request as crud_code_analysis_request
from app.dependencies import get_current_user
from app.models.user_activity import UserActivity
from app.models.user_keyword import UserKeyword
from app.models.code_analysis_request import CodeAnalysisRequest

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
    db_user = await crud_user.get_user_by_email(session, user.email)

    # 1. 힌트 요청 횟수 (code_analysis)
    #all_request_dates = await crud_code_analysis_request.get_code_analysis_request_dates_by_user(session, user_id=user_id)
    statement_code_analysis = (
        select(
            CodeAnalysisRequest.request_date,
            func.count(CodeAnalysisRequest.id)
        )
        .where(CodeAnalysisRequest.user_id == user_id)
        .group_by(CodeAnalysisRequest.request_date)
        .order_by(CodeAnalysisRequest.request_date.asc())
    )
    result_code_analysis = await session.exec(statement_code_analysis)
    all_request_dates = []
    for date_object, count in result_code_analysis.all():
        for _ in range(count):
            all_request_dates.append(date_object)

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
        for error_type, count in error_counts.most_common(5) # 최대 3개
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

    # 4. LLM이 가장 많이 추천한 문제 태그 (top_recommended_tags)
    recommended_tag_counts = Counter()
    RECOMMENDED_TAG_PREFIX = "_recommended"

    for keyword_record in all_user_keywords_records:
        if keyword_record.keyword.endswith(RECOMMENDED_TAG_PREFIX):
            tag = keyword_record.keyword[:-len(RECOMMENDED_TAG_PREFIX)]
            recommended_tag_counts[tag] += 1
    
    top_recommended_tags = [
        RecommendedTagStats(tag=tag, count=count)
        for tag, count in recommended_tag_counts.most_common(5)
    ]

    return UserFeedbackStats(
        code_analysis_requests=all_request_dates,
        top_code_errors=top_code_errors,
        total_logins=total_logins,
        average_session_duration_minutes=average_session_duration_minutes,
        top_recommended_tags=top_recommended_tags
    )