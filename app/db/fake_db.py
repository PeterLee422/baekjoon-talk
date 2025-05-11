from uuid import uuid4
import datetime as dt

_DB: dict[str, dict] = {
    "users": {},
    "conversations": {},
    "messages": {},
}
# conversations -> id, owner, title, messages
# messages -> id, conv_id, sender, content

def add_user(
        email: str,
        username: str,
        hashed_password: str,
        photo_url: str | None = None
):
    """
    User 추가하기
    """
    if username in _DB["users"]:
        raise ValueError("User already exists")
    user_id = str(uuid4())
    _DB["users"][email] = {
        "id": user_id,
        "email": email,
        "username": username,
        "hashed_password": hashed_password,
        "photo_url": photo_url,
        "about": None,
    }
    return _DB["users"][email]

def get_user(
        email: str
):
    return _DB["users"].get(email)

def update_profile(email:str, **kwargs):
    user = _DB["users"].get(email)
    if not user:
        raise KeyError("user")
    user.update({k:v for k, v in kwargs.items() if v is not None})
    return user

def update_user_photo(
        username: str,
        url: str
):
    if username in _DB["users"]:
        _DB["users"][username]["photo_url"] = url
        return _DB["users"][username]
    raise KeyError("User not found")

def _now():
    return dt.datetime.now().isoformat()

def create_conversation(
        owner: str,
        title: str | None = None
):
    conv_id = str(uuid4())
    _DB["conversations"][conv_id] = {
        "id": conv_id,
        "owner": owner,
        "title": title or "Untitled",
        "messages": [],
        "last_modified": _now(),
    }
    return _DB["conversations"][conv_id]

def get_conversation(
        conv_id: str
):
    return _DB["conversations"].get(conv_id)

def add_message(
        conv_id: str,
        sender: str,
        content: str,
):
    conversation = _DB["conversations"].get(conv_id)
    if conv_id not in _DB["conversations"]:
        raise KeyError("Conversation not found")
    msg_id = str(uuid4())
    _DB["messages"][msg_id] = {
        "id": msg_id,
        "conv_id": conv_id,
        "sender": sender,
        "content": content,
    }
    conversation["messages"].append(msg_id)
    conversation["last_modified"] = _now()
    # message = {
    #     "id": msg_id,
    #     "conv_id": conv_id,
    #     "sender": sender,
    #     "content": content,
    # }
    #_DB["messages"][msg_id] = message
    #_DB["conversations"][conv_id]["messages"].append(msg_id)
    return _DB["messages"][msg_id]

def list_messages(
        conv_id: str
):
    conv = get_conversation(conv_id)
    if not conv:
        return []
    return [_DB["messages"][mid] for mid in conv["messages"]]