# app/schemas/user.py

from typing import Annotated

from pydantic import BaseModel, Field, HttpUrl, EmailStr

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

class RefreshToken(BaseModel):
    refresh_token: str

class TokenData(BaseModel):
    username: str | None = None