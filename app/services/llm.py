# app/services/llm.py

import json
import pandas as pd
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException

from app.core.configuration import settings
from app.core.redis import get_redis_client # Redis 활용하여 최적화
from app.crud import conversation as crud_conv
from app.crud import message as crud_msg
from app.schemas.user import UserOut
from app.services.boj_llmrec.llmrec import LLMRec, Session

# For Debugging
from app.core.memory import print_memory_usage

# Global Session Dictionary -> Not Now!
# session_registry: dict[str, Session] = {}
SESSION_PREFIX = "llm_session:conv:"
REDIS_LLM_SESSION_TTL_SECONDS = 3600 # 1 Hours
_global_llmrec_instance: LLMRec | None = None

# For Redis
def _session_key(conv_id: str) -> str:
    return f"{SESSION_PREFIX}{conv_id}"

def initialize_llmrec_instance():
    global _global_llmrec_instance
    if _global_llmrec_instance is None:
        _global_llmrec_instance = LLMRec(api_key=settings.LLM_API_KEY)
        print("[LLM Service] Global LLMRec instance initialized.")
    return _global_llmrec_instance

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
    # 1. Redis에서 불러오기
    redis_client = get_redis_client()
    llm_session_key = _session_key(conv_id=conv_id)
    llmrec = initialize_llmrec_instance()

    cached_session_data_json = await redis_client.get(llm_session_key)
    if cached_session_data_json:
        try:
            cached_session_data = json.loads(cached_session_data_json)
            prev_msgs_from_cache = cached_session_data.get("prev_msgs", [])

            llm_session = llmrec.get_new_session(
                user_handle=cached_session_data.get("user_handle"),
                profile=cached_session_data.get("profile"),
                conv_id=cached_session_data.get("conv_id"),
                title=cached_session_data.get("title", "untitled"),
                history=prev_msgs_from_cache
            )
            await redis_client.expire(llm_session_key, REDIS_LLM_SESSION_TTL_SECONDS)
            print(f"[LLM Service] Redis: LLM session loaded for conv_id {conv_id} and TTL reset.")

            if llm_session.user_handle != user_handle.username:
                raise HTTPException(status_code=403, detail="Unauthorized session access: User mismatch for cached sesion.")

            # session_registry[conv_id] = llm_session
            return llm_session
        except json.JSONDecodeError as e:
            print(f"[LLM Service] Error decoding LLM session from Redis for {conv_id}: {e}. Falling back to DB.")
        except KeyError as e:
            print(f"[LLM Service] Missing data in cached LLM session for {conv_id}: {e}. Falling back to DB.")
        except Exception as e:
            print(f"[LLM Service] Error restoring LLM session for {conv_id}: {e}. Falling back to DB.")

    # 2. Redis에 없거나 복원 실패 시
    conversation = await crud_conv.get_conversation(db_session, conv_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

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

    # Profile 만들기
    profile = {
        "user_level": user_handle.user_level,
        "goal": user_handle.goal,
        "interested_tags": user_handle.interested_tags
    }

    # Session 생성
    llm_session = llmrec.get_new_session(
        user_handle=user_handle.username,
        profile=profile,
        conv_id=conv_id,
        title=conversation.title,
        history=prev_msgs
    )

    await save_session(conv_id, llm_session, db_session)
    # session_registry[conv_id] = llm_session
    return llm_session

async def get_stateless_llm_summary(
        user_handle: str,
        profile: dict,
        message_content: str
) -> str:
    """
    Feedback 세션을 위한 세션 생성 (Redis에 저장하지 않음)
    message_content는 통계 데이터가 포함된 텍스트
    """
    llmrec_instance = initialize_llmrec_instance()

    summary_system_prompt = """
    당신은 사용자 활동 통계 데이터를 분석하고, 사용자의 코딩 학습 경험에 대한 간결하고 통찰력있는 3줄 요약 또는 평가를 제공하는 도우미입니다.
    제공된 통계 정보를 바탕으로 사용자의 강점, 개선할 점, 학습 패턴, 흥미 분야 등을 종합적으로 평가해주세요.
    평가는 긍정적이고 격려하는 톤으로 작성하며, 반드시 3줄로 구성해주세요.
    """

    messages_for_llm = [
        {"role": "developer", "content": summary_system_prompt},
        {"role": "user", "content": f"사용자 프로필: {profile}\n\n사용자 통계 데이터:\n{message_content}\n\n위 통계를 바탕으로 3줄 요약을 생성해주세요."}
    ]
    print(messages_for_llm)

    try:
        summary_response_text, _, _, _ = llmrec_instance.llm.chat(
            user_input=messages_for_llm[1]["content"],
            prev_msgs=[messages_for_llm[0]],
            user_handle=user_handle,
            profile=profile
        )
        print("llm.chat 불러오기")

        lines = [line.strip() for line in summary_response_text.split('\n') if line.strip()]
        final_summary = "\n".join(lines[:3])
        if len(lines) > 3:
            final_summary += "..."
    
    except Exception as e:
        print(f"ERROR: LLM summary generation failed: {e}")
        final_summary = "대화 요약 생성 중 오류가 발생했습니다."
    
    return final_summary

async def save_session(
        conv_id: str,
        llm_session: Session,
        db_session: AsyncSession
):
    redis_client = get_redis_client()
    # session_registry[conv_id] = llm_session

    session_data = {
        "user_handle": llm_session.user_handle,
        "profile": llm_session.profile,
        "title": llm_session.title,
        "prev_msgs": llm_session.prev_msgs,
        "conv_id": llm_session.conv_id
    }
    try:
        await redis_client.setex(
            _session_key(conv_id),
            REDIS_LLM_SESSION_TTL_SECONDS,
            json.dumps(session_data)
        )
        print(f"[LLM Service] Redis: LLM session saved for conv_id {conv_id}. TTL: {REDIS_LLM_SESSION_TTL_SECONDS}s.")
    except Exception as e:
        print(f"[LLM Service] ERROR: Failed to save LLM session to Redis for {conv_id}: {e}")
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
    redis_client = get_redis_client()
    
    # session_registry.pop(conv_id, None)
    await redis_client.delete(_session_key(conv_id))
    print(f"[LLM Service] Redis and in-memory: LLM session deleted for conv_id {conv_id}.")

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
    text_response, speech_response, keywords = session.chat(message)
    
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

    return (text_response, speech_response, keywords)
