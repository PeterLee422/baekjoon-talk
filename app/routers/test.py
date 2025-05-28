# app/routers/test.py

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import HTMLResponse
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from html import escape

from app.db.database import get_session
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.friend import FriendRequest, Friend

router = APIRouter()

TEST_DB_ACCESS_KEY = "TESTDUMMYKEY"

@router.get("/test/db", response_class=HTMLResponse)
async def db_view(
    key: str = Query(..., description="Test Page Access Key"),
    session: AsyncSession = Depends(get_session)
):
    """
    DB 내용(Users, Conversations, Messages)을 HTML로 비동기 반환
    개발용 진단 페이지입니다. (운영 환경에서는 비활성화하세요)
    """
    if key != TEST_DB_ACCESS_KEY:
        raise HTTPException(status_code=403, detail="Access forbidden: invalid key")
    
    users_result = await session.exec(select(User))
    conversations_result = await session.exec(select(Conversation))
    messages_result = await session.exec(select(Message))

    users = users_result.all()
    conversations = conversations_result.all()
    messages = messages_result.all()

    html_content = "<html><body>"
    html_content += "<h1>📊 Database View (Development Only)</h1>"

    # Users
    html_content += "<h2>👤 Users</h2><table border='1'>"
    html_content += "<tr><th>ID</th><th>Username</th><th>Email</th><th>Photo URL</th></tr>"
    for user in users:
        html_content += (
            f"<tr><td>{escape(user.id)}</td><td>{escape(user.username)}</td>"
            f"<td>{escape(user.email)}</td><td>{escape(str(user.photo_url))}</td></tr>"
            f"<td>{escape(str(user.first_login_at) if user.first_login_at else '❌ Never')}</td></tr>"
        )
    html_content += "</table>" if users else "<p>No users found.</p>"

    # Conversations
    html_content += "<h2>💬 Conversations</h2><table border='1'>"
    html_content += "<tr><th>ID</th><th>Owner ID</th><th>Title</th><th>Last Modified</th></tr>"
    for conv in conversations:
        html_content += (
            f"<tr><td>{escape(conv.id)}</td><td>{escape(conv.owner_id)}</td>"
            f"<td>{escape(conv.title)}</td><td>{escape(str(conv.last_modified))}</td></tr>"
        )
    html_content += "</table>" if conversations else "<p>No conversations found.</p>"

    # Messages
    html_content += "<h2>✉️ Messages</h2><table border='1'>"
    html_content += (
        "<tr><th>ID</th><th>Conversation ID</th><th>Sender</th><th>Content</th><th>Created At</th></tr>"
    )
    for msg in messages:
        html_content += (
            f"<tr><td>{escape(msg.id)}</td><td>{escape(msg.conv_id)}</td>"
            f"<td>{escape(msg.sender)}</td><td>{escape(msg.content)}</td><td>{escape(str(msg.created_at))}</td></tr>"
        )
    html_content += "</table>" if messages else "<p>No messages found.</p>"
    
    # Friend Requests
    html_content += "<h2>👬 Friend Requests</h2><table border='1'>"
    html_content += "<tr><th>ID</th><th>Sender</th><th>Receiver</th><th>Status</th><th>Created At</th></tr>"
    friend_requests_result = await session.exec(select(FriendRequest))
    friend_requests = friend_requests_result.all()
    for req in friend_requests:
        html_content += (
            f"<tr><td>{escape(req.id)}</td><td>{escape(req.sender_id)}</td>"
            f"<td>{escape(req.receiver_id)}</td><td>{escape(req.status)}</td><td>{escape(str(req.created_at))}</td></tr>"
        )
    html_content += "</table>" if friend_requests else "<p>No friend requests found.</p>"

    # Friends
    html_content += "<h2>👬 Friends</h2><table border='1'>"
    html_content += "<tr><th>ID</th><th>User 1</th><th>User 2</th><th>Created At</th></tr>"
    friends_result = await session.exec(select(Friend)) 
    friends = friends_result.all()
    for friend in friends:
        html_content += (
            f"<tr><td>{escape(friend.id)}</td><td>{escape(friend.user1_id)}</td>"
            f"<td>{escape(friend.user2_id)}</td><td>{escape(str(friend.created_at))}</td></tr>"
        )
    html_content += "</table>" if friends else "<p>No friends found.</p>"

    html_content += "</body></html>"

    return HTMLResponse(content=html_content)
