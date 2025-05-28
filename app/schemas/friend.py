from typing import Annotated
from pydantic import BaseModel
from enum import Enum
import datetime as dt

class FriendRequestCreate(BaseModel):
    receiver_id: str

class FriendRequestStatus(str, Enum):
    accepted = "accepted"
    rejected = "rejected"

class FriendRequestUpdate(BaseModel):
    status: FriendRequestStatus

class FriendRequestOut(BaseModel):
    id: str
    sender_id: str
    receiver_id: str
    created_at: dt.datetime
    status: str
    
class FriendOut(BaseModel):
    id: str
    user_id: str
    friend_id: str
    created_at: dt.datetime
    
    class Config:
        from_attributes = True