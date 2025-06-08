# app/routers/test.py

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import HTMLResponse, Response
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from html import escape

from app.db.database import get_session
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.friend import FriendRequest, Friend
from app.models.user_keyword import UserKeyword
from app.models.user_activity import UserActivity

router = APIRouter()

TEST_DB_ACCESS_KEY = "TESTDUMMYKEY"

@router.get("/test/db", response_class=HTMLResponse)
async def db_view(
    key: str = Query(..., description="Test Page Access Key"),
    session: AsyncSession = Depends(get_session)
):
    """
    DB 내용(Users, Conversations, Messages, Friends, Friend Requests, User Keywords, User Activities)을 HTML로 비동기 반환.
    개발용 진단 페이지입니다. (운영 환경에서는 비활성화하거나 삭제하세요.)
    """
    if key != TEST_DB_ACCESS_KEY:
        raise HTTPException(status_code=403, detail="Access forbidden: invalid key")
    
    users_result = await session.exec(select(User))
    conversations_result = await session.exec(select(Conversation))
    messages_result = await session.exec(select(Message))
    friend_requests_result = await session.exec(select(FriendRequest))
    friends_result = await session.exec(select(Friend))
    user_keywords_result = await session.exec(select(UserKeyword))
    user_activities_result = await session.exec(select(UserActivity)) # <-- UserActivity 조회 추가

    users = users_result.all()
    conversations = conversations_result.all()
    messages = messages_result.all()
    friend_requests = friend_requests_result.all()
    friends = friends_result.all()
    user_keywords = user_keywords_result.all()
    user_activities = user_activities_result.all() # <-- UserActivity 결과 저장

    html_content = "<html><head><title>DB View</title><style>table {width: 100%; border-collapse: collapse; margin-bottom: 20px;} th, td {border: 1px solid #ddd; padding: 8px; text-align: left;} th {background-color: #f2f2f2;}</style></head><body>"
    html_content += "<h1>📊 Database View (Development Only)</h1>"

    # Users Table
    html_content += "<h2>👤 Users</h2>"
    if users:
        html_content += "<table><tr><th>ID</th><th>Username</th><th>Email</th><th>Photo URL</th><th>First Login At</th><th>User Level</th><th>Goal</th><th>Interested Tags</th></tr>"
        for user in users:
            tags_str = ", ".join(user.interested_tags) if user.interested_tags else "None"
            html_content += (
                f"<tr><td>{escape(user.id)}</td><td>{escape(user.username)}</td>"
                f"<td>{escape(user.email)}</td><td>{escape(str(user.photo_url) if user.photo_url else 'None')}</td>"
                f"<td>{escape(str(user.first_login_at) if user.first_login_at else 'Never')}</td>"
                f"<td>{escape(user.user_level if user.user_level else 'None')}</td>"
                f"<td>{escape(user.goal if user.goal else 'None')}</td>"
                f"<td>{escape(tags_str)}</td></tr>"
            )
        html_content += "</table>"
    else:
        html_content += "<p>No users found.</p>"

    # Conversations Table
    html_content += "<h2>💬 Conversations</h2>"
    if conversations:
        html_content += "<table><tr><th>ID</th><th>Owner ID</th><th>Title</th><th>Last Modified</th></tr>"
        for conv in conversations:
            html_content += (
                f"<tr><td>{escape(conv.id)}</td><td>{escape(conv.owner_id)}</td>"
                f"<td>{escape(conv.title)}</td><td>{escape(str(conv.last_modified))}</td></tr>"
            )
        html_content += "</table>"
    else:
        html_content += "<p>No conversations found.</p>"

    # Messages Table
    html_content += "<h2>✉️ Messages</h2>"
    if messages:
        html_content += "<table><tr><th>ID</th><th>Conversation ID</th><th>Sender</th><th>Content</th><th>Created At</th></tr>"
        for msg in messages:
            html_content += (
                f"<tr><td>{escape(msg.id)}</td><td>{escape(msg.conv_id)}</td>"
                f"<td>{escape(msg.sender)}</td><td>{escape(msg.content)}</td><td>{escape(str(msg.created_at))}</td></tr>"
            )
        html_content += "</table>"
    else:
        html_content += "<p>No messages found.</p>"
    
    # Friend Requests Table
    html_content += "<h2>👬 Friend Requests</h2>"
    if friend_requests:
        html_content += "<table><tr><th>ID</th><th>Sender</th><th>Receiver</th><th>Status</th><th>Created At</th></tr>"
        for req in friend_requests:
            html_content += (
                f"<tr><td>{escape(req.id)}</td><td>{escape(req.sender_id)}</td>"
                f"<td>{escape(req.receiver_id)}</td><td>{escape(req.status)}</td><td>{escape(str(req.created_at))}</td></tr>"
            )
        html_content += "</table>"
    else:
        html_content += "<p>No friend requests found.</p>"

    # Friends Table
    html_content += "<h2>🤝 Friends</h2>"
    if friends:
        html_content += "<table><tr><th>ID</th><th>User ID</th><th>Friend ID</th><th>Created At</th></tr>"
        for friend in friends:
            html_content += (
                f"<tr><td>{escape(friend.id)}</td><td>{escape(friend.user_id)}</td>"
                f"<td>{escape(friend.friend_id)}</td><td>{escape(str(friend.created_at))}</td></tr>"
            )
        html_content += "</table>"
    else:
        html_content += "<p>No friends found.</p>"

    # User Keywords Table
    html_content += "<h2>🔑 User Keywords</h2>"
    if user_keywords:
        html_content += "<table><tr><th>ID</th><th>User ID</th><th>Conversation ID</th><th>Keyword</th><th>Created At</th></tr>"
        for ukw in user_keywords:
            html_content += (
                f"<tr><td>{escape(ukw.id)}</td><td>{escape(ukw.user_id)}</td>"
                f"<td>{escape(ukw.conversation_id)}</td><td>{escape(ukw.keyword)}</td><td>{escape(str(ukw.created_at))}</td></tr>"
            )
        html_content += "</table>"
    else:
        html_content += "<p>No user keywords found.</p>"

    # User Activities Table <-- 새로 추가된 섹션
    html_content += "<h2>⏱️ User Activities</h2>"
    if user_activities:
        html_content += "<table><tr><th>ID</th><th>User ID</th><th>Event Type</th><th>Timestamp</th><th>Session ID</th><th>Duration (s)</th></tr>"
        for act in user_activities:
            html_content += (
                f"<tr><td>{escape(act.id)}</td><td>{escape(act.user_id)}</td>"
                f"<td>{escape(act.event_type)}</td><td>{escape(str(act.timestamp))}</td>"
                f"<td>{escape(act.session_id if act.session_id else 'None')}</td>" # None 처리
                f"<td>{escape(str(act.duration_seconds) if act.duration_seconds is not None else 'N/A')}</td></tr>" # None 처리
            )
        html_content += "</table>"
    else:
        html_content += "<p>No user activities found.</p>"

    html_content += "</body></html>"

    return HTMLResponse(content=html_content)