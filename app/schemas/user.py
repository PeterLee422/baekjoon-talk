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
    class Config:
        from_attributes = True
    
class LoginIn(BaseModel):
    email: EmailStr
    password: str

class ProfileUpdate(BaseModel):
    username: str | None = None
    about: str | None = None

class Token(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"

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