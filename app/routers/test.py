# app/routers/test.py

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import HTMLResponse, Response # Response 임포트 추가 (delete_conversation 때문에)
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from html import escape

from app.db.database import get_session
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.friend import FriendRequest, Friend
# from app.models.code import CodeSnippet # 더 이상 사용하지 않으므로 삭제

router = APIRouter()

TEST_DB_ACCESS_KEY = "TESTDUMMYKEY"

@router.get("/test/db", response_class=HTMLResponse)
async def db_view(
    key: str = Query(..., description="Test Page Access Key"),
    session: AsyncSession = Depends(get_session)
):
    """
    DB 내용(Users, Conversations, Messages, Friends, Friend Requests)을 HTML로 비동기 반환.
    개발용 진단 페이지입니다. (운영 환경에서는 비활성화하거나 삭제하세요.)
    """
    if key != TEST_DB_ACCESS_KEY:
        raise HTTPException(status_code=403, detail="Access forbidden: invalid key")
    
    users_result = await session.exec(select(User))
    conversations_result = await session.exec(select(Conversation))
    messages_result = await session.exec(select(Message))
    friend_requests_result = await session.exec(select(FriendRequest))
    friends_result = await session.exec(select(Friend))

    users = users_result.all()
    conversations = conversations_result.all()
    messages = messages_result.all()
    friend_requests = friend_requests_result.all()
    friends = friends_result.all()

    html_content = "<html><head><title>DB View</title><style>table {width: 100%; border-collapse: collapse; margin-bottom: 20px;} th, td {border: 1px solid #ddd; padding: 8px; text-align: left;} th {background-color: #f2f2f2;}</style></head><body>"
    html_content += "<h1>📊 Database View (Development Only)</h1>"

    # Users Table
    html_content += "<h2>👤 Users</h2>"
    if users:
        html_content += "<table><tr><th>ID</th><th>Username</th><th>Email</th><th>Photo URL</th><th>First Login At</th><th>User Level</th><th>Goal</th><th>Interested Tags</th></tr>"
        for user in users:
            # interested_tags는 리스트이므로 문자열로 변환하여 출력
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
    html_content += "<h2>🤝 Friends</h2>" # 이모지 및 제목 변경
    if friends:
        html_content += "<table><tr><th>ID</th><th>User ID</th><th>Friend ID</th><th>Created At</th></tr>"
        for friend in friends:
            html_content += (
                f"<tr><td>{escape(friend.id)}</td><td>{escape(friend.user_id)}</td>" # user_id로 수정
                f"<td>{escape(friend.friend_id)}</td><td>{escape(str(friend.created_at))}</td></tr>" # friend_id로 수정
            )
        html_content += "</table>"
    else:
        html_content += "<p>No friends found.</p>"

    html_content += "</body></html>"

    return HTMLResponse(content=html_content)