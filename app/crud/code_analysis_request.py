# app/crud/code_analysis_request.py

import datetime as dt
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.code_analysis_request import CodeAnalysisRequest
from uuid import uuid4
from app.core.configuration import settings

async def create_code_analysis_request(
        session: AsyncSession,
        user_id: str,
        request_date: dt.date | None = None
) -> CodeAnalysisRequest:
    """
    새로운 코드 분석 요청을 DB에 저장
    """
    if request_date is None:
        request_date = dt.date.today()
    
    log_entry = CodeAnalysisRequest(
        id=str(uuid4()),
        user_id=user_id,
        request_date=request_date,
        timestamp=dt.datetime.now(settings.KST)
    )
    session.add(log_entry)
    await session.commit()
    await session.refresh(log_entry)
    return log_entry

async def get_code_analysis_request_dates_by_user(
        session: AsyncSession,
        user_id: str
) -> list[dt.date]:
    """
    특정 사용자의 모든 코드 분석 요청 일자를 리스트로 반환
    """
    statement = select(CodeAnalysisRequest.request_date).where(
        CodeAnalysisRequest.user_id == user_id
    ).order_by(CodeAnalysisRequest.request_date.asc())
    result = await session.exec(statement)
    return result.all()

async def delete_code_analysis_request_logs_by_user(
        session: AsyncSession,
        user_id: str
) -> None:
    """
    특정 유저와 관련된 모든 코드 분석 요청 로그 삭제
    """
    statement = select(CodeAnalysisRequest).where(CodeAnalysisRequest.user_id == user_id)
    result = await session.exec(statement)
    logs = result.all()
    for log in logs:
        await session.delete(log)
    await session.commit()