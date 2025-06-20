# app/routers/chat.py

import os
import datetime as dt

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from fastapi.responses import JSONResponse, StreamingResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.redis import get_redis_client
from app.schemas.chat import ConversationOutWithFirstMessage, ConversationOut, MessageIn, MessageOut, LatestProblemInfo
from app.schemas.user import UserOut
from app.dependencies import get_current_user
from app.db.database import get_session
from app.crud import message as crud_message
from app.crud import conversation as crud_conv
from app.crud import user as crud_user
from app.crud import user_keyword as crud_user_keyword
from app.crud import code_analysis_request as crud_code_analysis_request
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
    if not msg_in.content:
        raise HTTPException(status_code=400, detail="Please provide a text message to start a conversation.")

    title = "untitled"

    conversation = await crud_conv.create_conversation(session, owner_id=user.id, title=title)

    if msg_in.voice:
        content = stt.transcribe_audio(msg_in.voice)
    else:
        content = msg_in.content

    prompt = """
    당신은 Baekjoon Online Judge에 특화된 대화형 알고리즘 문제 풀이 도우미입니다.
    유저가 문제를 요청하면, 기계적으로 문제 목록만 나열하지 말고, 대화하며 추천해 주세요.
    만약 tool 호출의 결과가 비어있는 경우, 유저의 핸들이 존재하지 않거나, solved.ac 서버의 문제인 경우가 많습니다.
    이 경우, 유저에게 핸들을 확인해 달라고 요청하세요.

    문제의 난이도는 'Bronze 5'부터 'Ruby 1'까지의 범위로 설정되어 있습니다.
    예시는 다음과 같습니다: 'Bronze 5', 'Silver 2', 'Ruby 2', 'Platinum 1'.
    티어 뒤의 숫자는 1에서 5까지의 숫자로, 5는 해당 분류 내에서 가장 쉬운 문제를 의미합니다.

    문제를 제공할 때는 각 문제마다 아래의 형식을 따라 주세요:

    출력 형식:
    🔹 [{문제 제목} ({문제 번호}번)]({문제 링크}) - {문제 난이도}
    📌 {간단한 설명}

    문제 제목은 **그대로, 정확히** 전달하세요.

    조건:
    - 문제는 2~4개 정도 제공하며, 시각적으로 보기 좋게 이모지를 적절히 활용해 주세요.
    - 문제의 난이도 제한은 사용자의 요구가 있지 않은 한 설정하지 않습니다.
    """

    profile_prompt = "사용자 프로필 정보:\n"
    level_desc = {
        "very low": "사용자는 프로그래밍 경험이 거의 없으며, 기본 문법 정도만 알고 있습니다.",
        "low": "사용자는 간단한 입출력·자료형을 다룰 수 있지만 알고리즘 경험이 많지 않습니다.",
        "medium": "사용자는 정렬·구현·기초 자료구조 문제를 무리 없이 해결할 수 있습니다.",
        "high": "사용자는 그래프·DP·그리디 등 중급 알고리즘을 습득했고, 중~고난도 문제 경험이 있습니다.",
        "very high": "사용자는 복잡한 알고리즘/자료구조를 능숙히 사용하며, 대회 수준 문제도 해결 가능합니다.",
    }
    if (lvl := user.user_level) in level_desc:
        profile_prompt += level_desc[lvl] + "\n"
    goal_desc = {
        "coding test": "주요 목표는 취업 코딩 테스트 대비입니다.",
        "contest": "주요 목표는 알고리즘 대회(ICPC·PS 대회) 준비입니다.",
        "learning": "주요 목표는 알고리즘 지식 확장 및 실력 향상입니다.",
        "hobby": "주요 목표는 취미로 문제 풀이를 즐기는 것입니다.",
    }
    if (goal := user.goal) in goal_desc:
        profile_prompt += goal_desc[goal] + "\n"
    if tags := user.interested_tags:
        tag_list = ", ".join(tags)
        profile_prompt += f"사용자는 다음 주제에 특히 흥미가 있습니다: {tag_list}.\n"
    
    prompt = prompt + profile_prompt

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
    text_response, speech_response, keywords = await llm.generate_response(conversation.id, user, msg_in.content, session)

    # Keyword 저장
    if keywords:
        await crud_user_keyword.create_multiple_user_keywords(
            session=session,
            user_id=user.id,
            conversation_id=conversation.id,
            keywords=keywords
        )


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
            keywords=keywords
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
    # sender가 "developer"인 시스템 프롬프트는 제외
    filtered_messages = [m for m in messages if m.sender != "developer"]

    return [MessageOut(id=m.id, sender=m.sender, content=m.content) for m in filtered_messages]

@router.post("/conversations/{conv_id}/messages", response_model=MessageOut)
async def post_message(
    conv_id: str,
    msg_in: MessageIn,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[UserOut, Depends(get_current_user)],
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
    content = ""

    if msg_in.voice:
        content = stt.transcribe_audio(msg_in.voice)
    elif msg_in.code:
        # TODO: System prompt 추가하기
        current_request_type = msg_in.request_type if msg_in.request_type else "general"
        await crud_code_analysis_request.create_code_analysis_request(session, user.id, current_request_type, dt.date.today())

        request_type_instructions = ""
        if msg_in.request_type:
            if msg_in.request_type.lower() == "hint":
                #request_type_instructions = "다음 코드에 대한 힌트를 제공해주세요. 직접적인 정답보다는 문제 해결의 방향성을 제시하는 데 초점을 맞춰주세요.\n\n"
                request_type_instructions = (
                    "당신은 국제 알고리즘 대회에서 수상 경력을 가진 멘토입니다."
                    "학생이 **스스로** 문제를 풀 수 있도록 '계단식 힌트'를 제공합니다."
                    "힌트는 총 3단계로, 난이도가 낮은 힌트 -> 중간 힌트 -> 거의 풀이 직전 단계 힌트 순서입니다."
                    "정답이나 완전한 코드를 제공하는 정말 더 이상 줄 수 있는 힌트가 없을 때 사용자에게 힌트 요청 습관에 대한 가볍고 짧은 경고를 한 후 사용자가 동의하면 그 때 제공합니다."
                )
            elif msg_in.request_type.lower() == "review":
                #request_type_instructions = "다음 코드에 대한 상세한 코드 리뷰를 수행해주세요. 가독성, 효율성, 버그 가능성, 모범 사례 등을 평가해주세요.\n\n"
                request_type_instructions = (
                    "당신은 ICPC World Finals 출신 알고리즘 심사위원입니다.\n"
                    "리뷰는 '알고리즘 사고 과정과 복잡도 최적성' 위주로 진행합니다.\n"
                    "답변은 반드시 다음 6개 섹션을 포함하세요.\n"
                    "1. 알고리즘 요약 - 제출 코드에서 추론한 핵심 아이디어 한 줄 요약\n"
                    "2. 강점 - 설계·복잡도 측면에서 잘한 점\n"
                    "3. 잠재적 오류 - 논리·경계조건·무한루프 등 **버그 가능성** (Severity: S/M/L)\n"
                    "4. 복잡도&한계 - 시간·공간 Big-O 표기, 병목 지점 분석\n"
                    "5. 대안/개선 - 이론적으로 더 우수한 알고리즘이나 데이터 구조 제안\n"
                    "6. 참고 구현 - 핵심 로직만 간결히 보여주는 리팩터 예시 (필수 아님. 30줄 이내)\n\n"
                    "코드 스타일/패키징 언급은 최소화하고, 알고리즘적 통찰에 집중하세요."
                    "정답 전체 구현이나 최종 출력은 제공하지 마십시오."
                )
            elif msg_in.request_type.lower() == "complexity":
                #request_type_instructions = "다음 코드의 시간 복잡도와 공간 복잡도를 분석하여 설명해주세요.\n\n"
                request_type_instructions = (
                    "당신은 컴퓨터과학 교수이며, 시간·공간 복잡도 분석을 엄밀히 수행합니다.\n"
                    "분석 결과는 'O(·) 표기', '주요 연산 설명', '최악·평균·최선' 3단계로 나누어 서술합니다.\n"
                    "증명 스케치는 꼭 포함해 주세요.\n\n"
                )
            elif msg_in.request_type.lower() == "optimize":
                #request_type_instructions = "다음 코드를 최적화하는 방법을 제안해주세요. 성능 개선, 코드 간결화, 자원 효율성 등에 초점을 맞춰주세요.\n\n"
                request_type_instructions = (
                    "당신은 고성능 알고리즘 튜너입니다.\n"
                    "제안 시 '변경 이유 -> 개선된 코드 -> 기대 효율' 순서로 답하고, 동작은 원본과 동일해야 합니다.\n"
                    "가능하다면 **알고리즘적 개선**을 우선 고려하고, 이후에 **언어·컴파일러 수준 최적화**를 추가로 제안합니다.\n"
                )
            else:
                request_type_instructions = f"사용자 질문에 따라 다음 코드를 분석하고 답변해주세요.\n\n"

        code_block = (
            f"사용자가 입력한 코드는 다음과 같습니다. (언어: {msg_in.language or 'unknown'}):\n"
            f"```\n{msg_in.code}\n```"
        )
        user_question = msg_in.content if msg_in.content else "위의 코드에 대해 설명하거나 오류를 찾고 힌트를 주세요."

        if msg_in.problem_info:
            content += (
                f"{request_type_instructions}"
                f"문제 정보: {msg_in.problem_info}\n"
            )
        if msg_in.problem_num:
            content += (
                f"문제 번호: {msg_in.problem_num}\n"
            )
        content += (
            f"{code_block}\n\n"
            f"사용자 질문: {user_question}"
        )
    else:
        request_type_instructions = ""
        if msg_in.problem_info and msg_in.request_type.lower() == "hint":
            request_type_instructions = (
                "당신은 국제 알고리즘 대회에서 수상 경력을 가진 멘토입니다.\n"
                "학생이 **스스로** 문제를 풀 수 있도록 '계단식 힌트'를 제공합니다."
                "힌트는 총 3단계로, 난이도가 낮은 힌트 -> 중간 힌트 -> 거의 풀이 직전 단계 힌트 순서입니다."
                "다음 문제 정보에 대한 힌트를 제공해주세요. 일반적인 문제 해결의 방향성, 사람들이 자주 틀리는 부분 등을 언급해주세요."
            )
            content = (
                f"{request_type_instructions}\n"
                f"문제 정보: 
                {msg_in.problem_info}\n"
            )
        if msg_in.problem_num:
            content += (
                f"문제 번호: {msg_in.problem_num}\n"
            )
        content += (
            f"사용자 질문: {msg_in.content}"
        )

    if not content.strip():
        raise HTTPException(status_code=400, detail="Message content required.")

    # User의 message 저장

    user_message = await crud_message.create_message(
        session,
        conv_id=conv_id,
        sender=user.username,
        content=msg_in.content
    )

    # LLM 호출 후 response 생성
    print(content)
    text_response, speech_response, keywords = await llm.generate_response(conversation.id, user, content, session)

    # Keyword 저장
    if keywords:
        await crud_user_keyword.create_multiple_user_keywords(
            session=session,
            user_id=user.id,
            conversation_id=conversation.id,
            keywords=keywords
        )

    # Assistant(bot) Message 저장
    assistant_message = await crud_message.create_message(
        session=session,
        conv_id=conv_id,
        sender="assistant",
        content=text_response
    )

    # 대화방 마지막 수정시간 갱신
    await crud_conv.update_last_modified(session, conv_id)

    # 대화 세션에 최신 문제 정보 업데이트
    if msg_in.code is not None or msg_in.problem_num is not None or msg_in.problem_info is not None:
        await crud_conv.update_latest_problem_info(
            session,
            conv_id,
            msg_in.problem_num,
            msg_in.problem_info,
            msg_in.code,
            msg_in.language
        )

    # TTS
    redis_client = get_redis_client()
    await redis_client.setex(f"tts:{assistant_message.id}", 300, speech_response)

    return MessageOut(
        id=assistant_message.id,
        sender=assistant_message.sender,
        content=assistant_message.content,
        keywords=keywords
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
    
    # Conversation과 관련된 모든 Keyword 삭제
    await crud_user_keyword.delete_user_keywords_by_conversation(session, conv_id)

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

@router.get("/conversations/{conv_id}/latest-problem", response_model=LatestProblemInfo)
async def get_latest_problem_info_in_conversation(
    conv_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[UserOut, Depends(get_current_user)]
):
    """
    특정 대화 세션에서 가장 최근에 입력된 문제 번호와 문제 정보를 조회
    """
    conversation = await crud_conv.get_conversation(session, conv_id)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conversation.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this conversation")
    
    return LatestProblemInfo(
        problem_number=conversation.last_problem_number,
        problem_info=conversation.last_problem_info,
        code=conversation.last_code_content,
        language=conversation.last_code_language
    )