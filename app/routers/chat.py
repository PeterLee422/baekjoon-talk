# app/routers/chat.py

import os

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from fastapi.responses import JSONResponse, StreamingResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.redis import get_redis_client
from app.schemas.chat import ConversationOutWithFirstMessage, ConversationOut, MessageIn, MessageOut
from app.schemas.user import UserOut
from app.dependencies import get_current_user
from app.db.database import get_session
from app.crud import message as crud_message
from app.crud import conversation as crud_conv
from app.services import stt, llm, tts

router = APIRouter()

@router.get("/conversations", response_model=list[ConversationOut])
async def list_conversation(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[UserOut, Depends(get_current_user)]
):
    """
    현재 user의 모든 대화 목록 가져오기
    """
    conversations = await crud_conv.list_user_conversation(session, user.id)

    if not conversations:
        raise HTTPException(status_code=404, detail=f"Conversations not found")

    return conversations


@router.get("/conversations/{conv_id}", response_model=ConversationOut)
async def get_conversation(
    conv_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[UserOut, Depends(get_current_user)]
):
    """
    특정 대화 세션을 조회
    """
    conversation = await crud_conv.get_conversation(session, conv_id)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if conversation.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this conversation")

    return ConversationOut.model_validate(conversation)


@router.post("/conversations", response_model=ConversationOutWithFirstMessage, status_code=status.HTTP_201_CREATED)
async def start_conversation(
    msg_in: MessageIn,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[UserOut, Depends(get_current_user)],
    background_tasks: BackgroundTasks
):
    """
    새로운 대화 세션 생성
    """
    title = "untitled"

    conversation = await crud_conv.create_conversation(session, owner_id=user.id, title=title)

    if msg_in.voice:
        content = stt.transcribe_audio(msg_in.voice)
    else:
        content = msg_in.content

    prompt = """
    당신은 Baekjoon Online Judge의 알고리즘 문제를 추천해주는 친절한 대화형 추천 시스템입니다.
    유저가 문제를 요청하면, 기계적으로 문제 목록만 나열하지 말고, 대화하며 추천해 주세요.
    또한 당신은 문제의 구체적인 내용은 알지 못하므로, 유저가 이를 묻는다면 알지 못한다고 답변해 주세요.

    문제의 난이도는 'Bronze 5'부터 'Ruby 1'까지의 범위로 설정되어 있습니다.
    예시는 다음과 같습니다: 'Bronze 5', 'Silver 2', 'Ruby 2', 'Platinum 1'.
    티어 뒤의 숫자는 1에서 5까지의 숫자로, 5는 해당 분류 내에서 가장 쉬운 문제를 의미합니다.

    추천할 때는 각 문제마다 아래의 형식을 따라 주세요:

    출력 형식:
    🔹 [{문제 제목} ({문제 번호}번)]({문제 링크}) - {문제 난이도}
    📌 {간단한 설명}

    문제 제목은 **그대로, 정확히** 전달하세요.

    조건:
    - 문제는 2~4개 정도 추천하며, 시각적으로 보기 좋게 이모지를 적절히 활용해 주세요.
    - 문제의 난이도 제한은 사용자의 요구가 있지 않은 한 설정하지 않습니다.
    """

    developer_prompt = await crud_message.create_message(
        session=session,
        conv_id=conversation.id,
        sender="developer",
        content=prompt
    )

    first_message = await crud_message.create_message(
        session=session,
        conv_id=conversation.id,
        sender=user.username,
        content=content
    )

    # LLM 답변
    # -> 여기서 제목 생성됨
    text_response, speech_response = await llm.generate_response(conversation.id, user, msg_in.content, session)

    # Assistant(bot) Message 저장
    assistant_message = await crud_message.create_message(
        session=session,
        conv_id=conversation.id,
        sender="assistant",
        content=text_response
    )

    await crud_conv.update_last_modified(session, conversation.id)

    # TTS
    redis_client = get_redis_client()
    await redis_client.setex(f"tts:{assistant_message.id}", 300, speech_response)

    return ConversationOutWithFirstMessage(
        id=conversation.id,
        title=conversation.title,
        last_modified=conversation.last_modified,
        first_message=MessageOut(
            id=assistant_message.id,
            sender=assistant_message.sender,
            content=assistant_message.content,
            audio_base64=None,
        )
    )


@router.get("/conversations/{conv_id}/messages", response_model=list[MessageOut])
async def list_messages(
    conv_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[UserOut, Depends(get_current_user)]
):
    """
    특정 대화에 포함된 모든 Message 조회
    """
    conversation = await crud_conv.get_conversation(session, conv_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conversation.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this conversation")
    
    messages = await crud_message.list_messages_by_conversation(session, conv_id)
    filtered_messages = [m for m in messages if m.sender != "developer"]

    return [MessageOut(id=m.id, sender=m.sender, content=m.content) for m in filtered_messages]

@router.post("/conversations/{conv_id}/messages", response_model=MessageOut)
async def post_message(
    conv_id: str,
    msg_in: MessageIn,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[UserOut, Depends(get_current_user)],
    background_tasks: BackgroundTasks
):
    """
    기존 대화에 메시지를 추가하고, LLM으로부터 답변을 받아 저장
    """
    conversation = await crud_conv.get_conversation(session, conv_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conversation.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this conversation")
    
    # 음성 입력이 있으면 STT로 변환한다.
    if msg_in.voice:
        content = stt.transcribe_audio(msg_in.voice)
        voice_input = True
    else:
        content = msg_in.content
        voice_input = False

    # User의 message 저장
    user_message = await crud_message.create_message(
        session,
        conv_id=conv_id,
        sender=user.username,
        content=content
    )

    # LLM 호출 후 response 생성
    text_response, speech_response = await llm.generate_response(conversation.id, user, msg_in.content, session)

    # Assistant(bot) Message 저장
    assistant_message = await crud_message.create_message(
        session=session,
        conv_id=conv_id,
        sender="assistant",
        content=text_response
    )

    # 대화방 마지막 수정시간 갱신
    await crud_conv.update_last_modified(session, conv_id)

    # TTS
    redis_client = get_redis_client()
    await redis_client.setex(f"tts:{assistant_message.id}", 300, speech_response)

    return MessageOut(
        id=assistant_message.id,
        sender=assistant_message.sender,
        content=assistant_message.content,
        audio_base64=None,
    )

@router.delete("/conversations/{conv_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conv_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    user = Depends(get_current_user)
):
    """
    Conversation과 대화 내부의 모든 message 삭제
    """
    conversation = await crud_conv.get_conversation(session, conv_id)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conversation.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Message 삭제
    await crud_message.delete_messages_by_conversation(session, conv_id)

    # Conversation 삭제
    await crud_conv.delete_conversation(session, conv_id)

    return JSONResponse(
        status_code=200,
        content={
            "detail": "Conversation/Messages have successfully deleted."
        }
    )

@router.get("/tts", response_class=StreamingResponse)
async def get_tts_stream(
    message_id: str
):
    """
    입력된 텍스트를 음성으로 변환 (MP3 Streaming)
    """
    redis_client = get_redis_client()
    key = f"tts:{message_id}"
    speech_text = await redis_client.get(key)

    if not speech_text:
        raise HTTPException(status_code=404, detail="No cached summary for this message")

    return tts.generate_speech(speech_text)
