# app/routers/feedback.py

import datetime as dt
from typing import Annotated
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.database import get_session
from app.schemas.user import UserOut
from app.schemas.feedback import UserFeedbackStats, RecommendedTagStats, CodeErrorStats, RequestTypeDates
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
from app.services.llm import get_stateless_llm_summary

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
    code_analysis_dates = await crud_code_analysis_request.get_code_analysis_request_dates_by_user(session, user_id=user_id)
    request_type_counts = []
    for req_type, dates_list in code_analysis_dates:
        request_type_counts.append(RequestTypeDates(request_type=req_type, dates=dates_list))

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
    
    # 5. LLM의 유저 평가 (3줄평)
    llm_conversation_summary = None
    stats_text_summary = [
        f"총 코드 분석/힌트 요청 횟수: {sum(len(rtc.dates) for rtc in request_type_counts)}회"
    ]
    if request_type_counts:
        stats_text_summary.append("요청 종류별 횟수: ")
        for rtc in request_type_counts:
            stats_text_summary.append(f"   - {rtc.request_type if rtc.request_type else '일반 요청'}: {len(rtc.dates)}회")
    
    if top_code_errors:
        stats_text_summary.append("가장 흔한 코드 오류 유형: ")
        for error_stat in top_code_errors:
            stats_text_summary.append(f"   - {error_stat.error_type}: {error_stat.count}회")
    
    stats_text_summary.append(f"총 로그인 횟수: {total_logins}회")
    stats_text_summary.append(f"평균 접속 시간: {average_session_duration_minutes:.2f}분")

    if top_recommended_tags:
        stats_text_summary.append("주로 추천받은 문제 태그: ")
        for tag_stat in top_recommended_tags:
            stats_text_summary.append(f"   - {tag_stat.tag}: {tag_stat.count}회")
    
    stats_text_for_llm = "\n".join(stats_text_summary)

    if stats_text_for_llm.strip():
        profile_for_llm = {
            "user_level": user.user_level,
            "goal": user.goal,
            "interested_tags": ", ".join(user.interested_tags) if user.interested_tags else ""
        }

        llm_conversation_summary = await get_stateless_llm_summary(
            user_handle=user.username,
            profile=profile_for_llm,
            message_content=stats_text_for_llm
        )

    return UserFeedbackStats(
        code_analysis_requests=request_type_counts,
        top_code_errors=top_code_errors,
        total_logins=total_logins,
        average_session_duration_minutes=average_session_duration_minutes,
        top_recommended_tags=top_recommended_tags,
        llm_conversation_summary=llm_conversation_summary
    )