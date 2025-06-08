# app/schemas/user.py

from typing import Annotated

from pydantic import BaseModel, Field, HttpUrl, EmailStr
import datetime as dt

class UserBase(BaseModel):
    username: Annotated[str, Field(..., example="alice")]
    email: Annotated[EmailStr, Field(..., example="alpha@example.com")]
    photo_url: HttpUrl | None = Field(
        default=None,
        examples=["https://example.com/image.png"],
        description="사용자 프로필 사진 URL (Optional)"
        )

class UserCreate(UserBase):
    password: Annotated[str, Field(..., min_length=8, example="strong_password")]

class UserOut(UserBase):
    id: str
    first_login_at: dt.datetime | None = None
    user_level: str | None = None
    goal: str | None = None
    interested_tags: list[str] | None = None
    class Config:
        from_attributes = True
    
class LoginIn(BaseModel):
    email: EmailStr
    password: str

class UserProfileUpdateOnFirstLogin(BaseModel):
    user_level: str = Field(..., description="'very low', 'low', 'medium', 'high', 'very high'")
    goal: str = Field(..., description="'coding test', 'contestn', 'learning', 'hobby'")
    interested_tags: list[str] = Field(..., description="'DP', '그래프', '자료구조', '수학', '구현', '문자열', '탐욕법', '트리', '정렬'")

class ProfileUpdate(BaseModel):
    username: str | None = None
    about: str | None = None
    user_level: str | None = None
    goal: str | None = None
    interested_tags: list[str] | None = None

class Token(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    first_login: bool = True

class GoogleToken(BaseModel):
    id_token: str

class UserWithToken(UserBase):
    id: str
    access_token: str
    token_type: str = "bearer"
    class Config:
        from_attributes = True

class RefreshToken(BaseModel):
    refresh_token: str

class TokenData(BaseModel):
    username: str | None = None
    session_id: str | None = None