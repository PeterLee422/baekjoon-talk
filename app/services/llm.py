# app/services/llm.py

import json
import pandas as pd
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException

from app.dependencies import get_current_user
from app.db.database import get_session
from app.core.configuration import settings
# from app.core.redis import redis_client
from app.crud import conversation as crud_conv
from app.crud import message as crud_msg
from app.schemas.user import UserOut
from app.services.boj_llmrec.llmrec import LLMRec, Session

# For Debugging
from app.core.memory import print_memory_usage

# Global Session Dictionary
session_registry: dict[str, Session] = {}
SESSION_PREFIX = "session:conv:"

def _session_key(conv_id: str) -> str:
    return f"{SESSION_PREFIX}{conv_id}"

async def get_llm_session(
        conv_id: str,
        user_handle: UserOut,
        db_session: AsyncSession
) -> Session:
    """
    LLM session 반환하는 함수
        - 이미 세션이 존재할 경우 반환
        - 세션이 없을 경우 세션 생성
    """
    #1. Session이 registry에 있을 때
    llm_session = session_registry.get(conv_id)
    if llm_session is not None:
        if llm_session.user_handle != user_handle.username:
            raise HTTPException(status_code=403, detail="Unauthorized session access")
        return llm_session

    #2. 대화 불러오기
    conversation = await crud_conv.get_conversation(db_session, conv_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    #3. Session이 registry에 없고, 대화 내역이 DB에 있을 때
    messages = await crud_msg.list_messages_by_conversation(db_session, conv_id)
    
    prev_msgs = []
    for m in messages:
        role = "user" if m.sender == user_handle.username else (
            "assistant" if m.sender == "assistant" else "developer"
        )
        prev_msgs.append({
            "role": role,
            "content": m.content
        })

    # Session 생성
    llmrec = LLMRec(settings.LLM_API_KEY, prev_msgs)
    llm_session = llmrec.get_new_session(
        user_handle.username,
        conv_id=conv_id,
        title=conversation.title
    )

    session_registry[conv_id] = llm_session
    return llm_session

async def save_session(
        conv_id: str,
        llm_session: Session,
        db_session: AsyncSession
):
    session_registry[conv_id] = llm_session

    # redis_data = {
    #     "username": llm_session.user_handle,
    #     "prev_msgs": llm_session.prev_msgs,
    #     "recommendations": llm_session.recommendations.to_dict(orient="records")
    # }
    # await redis_client.set(_session_key(conv_id), json.dumps(redis_data))
    await crud_conv.update_last_modified(db_session, conv_id)

async def delete_session(
        conv_id: str
):
    # await redis_client.delete(_session_key(conv_id))
    session_registry.pop(conv_id, None)

async def generate_response(
        conv_id: str,
        user_handle: UserOut,
        message: str,
        db_session: AsyncSession
) -> tuple[str, str]:
    """
    LLM 응답 생성 및 반환, 세션 갱신(dict)
    """
    session = await get_llm_session(conv_id, user_handle, db_session)
    text_response, speech_response = session.chat(message)
    
    # 대화 제목 생성
    conversation = await crud_conv.get_conversation(db_session, conv_id)
    if (
        conversation and # Conversation이 DB에 존재하고
        conversation.title.strip().lower() == "untitled" and # DB에 저장된 conversation 제목이 untitled
        session.title and # session에 title이 존재하고
        session.title.strip().lower() != "untitled" # session의 title 값이 untitled 일 때
    ):
        conversation.title = session.title
        db_session.add(conversation)
        await db_session.commit()

    await save_session(conv_id, session, db_session)

    return (text_response, speech_response)