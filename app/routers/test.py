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
from app.models.code_analysis_request import CodeAnalysisRequest

router = APIRouter()

TEST_DB_ACCESS_KEY = "TESTDUMMYKEY"

@router.get("/test/db", response_class=HTMLResponse)
async def db_view(
    key: str = Query(..., description="Test Page Access Key"),
    session: AsyncSession = Depends(get_session)
):
    """
    DB 내용(Users, Conversations, Messages, Friends, Friend Requests, User Keywords, User Activities, Code Analysis Request Logs)을 HTML로 비동기 반환.
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
    user_activities_result = await session.exec(select(UserActivity))
    code_analysis_logs_result = await session.exec(select(CodeAnalysisRequest)) # <-- CodeAnalysisRequestLog 조회 추가

    users = users_result.all()
    conversations = conversations_result.all()
    messages = messages_result.all()
    friend_requests = friend_requests_result.all()
    friends = friends_result.all()
    user_keywords = user_keywords_result.all()
    user_activities = user_activities_result.all()
    code_analysis_logs = code_analysis_logs_result.all() # <-- CodeAnalysisRequestLog 결과 저장

    html_content = """
    <html>
    <head>
        <title>DB View (Development)</title>
        <style>
            body { font-family: -apple-system, BlinkMacMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"; margin: 20px; background-color: #f7f7f7; color: #333; }
            h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; margin-bottom: 30px; }
            h2 { color: #34495e; border-bottom: 1px dashed #ccc; padding-bottom: 5px; margin-top: 40px; margin-bottom: 20px; }
            table { width: 100%; border-collapse: collapse; margin-bottom: 30px; background-color: #fff; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            th, td { border: 1px solid #e0e0e0; padding: 12px 15px; text-align: left; vertical-align: top; }
            th { background-color: #ecf0f1; font-weight: bold; color: #34495e; }
            tr:nth-child(even) { background-color: #f9f9f9; }
            tr:hover { background-color: #f1f1f1; }
            p { color: #7f8c8d; font-style: italic; }
            .section-header { display: flex; align-items: center; gap: 10px; }
            .section-header h2 { margin: 0; border: none; padding: 0; }
        </style>
    </head>
    <body>
        <h1>📊 Database View (Development Only)</h1>
    """

    # Users Table
    html_content += """
        <div class="section-header"><h2>👤 Users</h2></div>
    """
    if users:
        html_content += """
        <table>
            <tr>
                <th>ID</th><th>Username</th><th>Email</th><th>Photo URL</th><th>First Login At</th>
                <th>User Level</th><th>Goal</th><th>Interested Tags</th>
            </tr>
        """
        for user_obj in users: # 'user'는 키워드이므로 'user_obj'로 변경
            tags_str = ", ".join(user_obj.interested_tags) if user_obj.interested_tags else "None"
            html_content += f"""
            <tr>
                <td>{escape(user_obj.id)}</td>
                <td>{escape(user_obj.username)}</td>
                <td>{escape(user_obj.email)}</td>
                <td>{escape(str(user_obj.photo_url) if user_obj.photo_url else 'None')}</td>
                <td>{escape(str(user_obj.first_login_at) if user_obj.first_login_at else 'Never')}</td>
                <td>{escape(user_obj.user_level if user_obj.user_level else 'None')}</td>
                <td>{escape(user_obj.goal if user_obj.goal else 'None')}</td>
                <td>{escape(tags_str)}</td>
            </tr>
            """
        html_content += "</table>"
    else:
        html_content += "<p>No users found.</p>"

    # Conversations Table
    html_content += """
        <div class="section-header"><h2>💬 Conversations</h2></div>
    """
    if conversations:
        html_content += """
        <table>
            <tr>
                <th>ID</th><th>Owner ID</th><th>Title</th><th>Last Modified</th>
                <th>Last Problem Number</th><th>Last Problem Info</th><th>Last Code Content</th>
            </tr>
        """
        for conv in conversations:
            html_content += f"""
            <tr>
                <td>{escape(conv.id)}</td>
                <td>{escape(conv.owner_id)}</td>
                <td>{escape(conv.title)}</td>
                <td>{escape(str(conv.last_modified))}</td>
                <td>{escape(str(conv.last_problem_number) if conv.last_problem_number is not None else 'None')}</td>
                <td>{escape(conv.last_problem_info if conv.last_problem_info else 'None')}</td>
                <td>{escape(conv.last_code_content if conv.last_code_content else 'None')}</td>
            </tr>
            """
        html_content += "</table>"
    else:
        html_content += "<p>No conversations found.</p>"

    # Messages Table
    html_content += """
        <div class="section-header"><h2>✉️ Messages</h2></div>
    """
    if messages:
        html_content += """
        <table>
            <tr>
                <th>ID</th><th>Conversation ID</th><th>Sender</th><th>Content</th><th>Created At</th>
            </tr>
        """
        for msg in messages:
            html_content += f"""
            <tr>
                <td>{escape(msg.id)}</td>
                <td>{escape(msg.conv_id)}</td>
                <td>{escape(msg.sender)}</td>
                <td>{escape(msg.content)}</td>
                <td>{escape(str(msg.created_at))}</td>
            </tr>
            """
        html_content += "</table>"
    else:
        html_content += "<p>No messages found.</p>"
    
    # Friend Requests Table
    html_content += """
        <div class="section-header"><h2>👬 Friend Requests</h2></div>
    """
    if friend_requests:
        html_content += """
        <table>
            <tr>
                <th>ID</th><th>Sender</th><th>Receiver</th><th>Status</th><th>Created At</th>
            </tr>
        """
        for req in friend_requests:
            html_content += f"""
            <tr>
                <td>{escape(req.id)}</td>
                <td>{escape(req.sender_id)}</td>
                <td>{escape(req.receiver_id)}</td>
                <td>{escape(req.status)}</td>
                <td>{escape(str(req.created_at))}</td>
            </tr>
            """
        html_content += "</table>"
    else:
        html_content += "<p>No friend requests found.</p>"

    # Friends Table
    html_content += """
        <div class="section-header"><h2>🤝 Friends</h2></div>
    """
    if friends:
        html_content += """
        <table>
            <tr>
                <th>ID</th><th>User ID</th><th>Friend ID</th><th>Created At</th>
            </tr>
        """
        for friend_obj in friends: # 'friend'는 키워드이므로 'friend_obj'로 변경
            html_content += f"""
            <tr>
                <td>{escape(friend_obj.id)}</td>
                <td>{escape(friend_obj.user_id)}</td>
                <td>{escape(friend_obj.friend_id)}</td>
                <td>{escape(str(friend_obj.created_at))}</td>
            </tr>
            """
        html_content += "</table>"
    else:
        html_content += "<p>No friends found.</p>"

    # User Keywords Table
    html_content += """
        <div class="section-header"><h2>🔑 User Keywords</h2></div>
    """
    if user_keywords:
        html_content += """
        <table>
            <tr>
                <th>ID</th><th>User ID</th><th>Conversation ID</th><th>Keyword</th><th>Created At</th>
            </tr>
        """
        for ukw in user_keywords:
            html_content += f"""
            <tr>
                <td>{escape(ukw.id)}</td>
                <td>{escape(ukw.user_id)}</td>
                <td>{escape(ukw.conversation_id)}</td>
                <td>{escape(ukw.keyword)}</td>
                <td>{escape(str(ukw.created_at))}</td>
            </tr>
            """
        html_content += "</table>"
    else:
        html_content += "<p>No user keywords found.</p>"

    # User Activities Table
    html_content += """
        <div class="section-header"><h2>⏱️ User Activities</h2></div>
    """
    if user_activities:
        html_content += """
        <table>
            <tr>
                <th>ID</th><th>User ID</th><th>Event Type</th><th>Timestamp</th><th>Session ID</th><th>Duration (s)</th>
            </tr>
        """
        for act in user_activities:
            html_content += f"""
            <tr>
                <td>{escape(act.id)}</td>
                <td>{escape(act.user_id)}</td>
                <td>{escape(act.event_type)}</td>
                <td>{escape(str(act.timestamp))}</td>
                <td>{escape(act.session_id if act.session_id else 'None')}</td>
                <td>{escape(str(act.duration_seconds) if act.duration_seconds is not None else 'N/A')}</td>
            </tr>
            """
        html_content += "</table>"
    else:
        html_content += "<p>No user activities found.</p>"

    # Code Analysis Request Logs Table
    html_content += """
        <div class="section-header"><h2>📈 Code Analysis Request Logs</h2></div>
    """
    if code_analysis_logs:
        html_content += """
        <table>
            <tr>
                <th>ID</th><th>User ID</th><th>Request Date</th><th>Timestamp</th><th>Request Type</th>
            </tr>
        """
        for log in code_analysis_logs:
            html_content += f"""
            <tr>
                <td>{escape(log.id)}</td>
                <td>{escape(log.user_id)}</td>
                <td>{escape(str(log.request_date))}</td>
                <td>{escape(str(log.timestamp))}</td>
                <td>{escape(log.request_type if log.request_type else 'None')}</td>
            </tr>
            """
        html_content += "</table>"
    else:
        html_content += "<p>No code analysis request logs found.</p>"

    html_content += """
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)