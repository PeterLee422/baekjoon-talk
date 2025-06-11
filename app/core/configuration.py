# app/core/configuration.py

from pydantic import Field
from pydantic_settings import BaseSettings
import pytz
import datetime as dt

class Settings(BaseSettings):
    """
    프로젝트명, 토큰 알고리즘/키, DB 계정/정보, API key 등 중요 정보
    배포할 시 환경변수를 사용할 것
    """
    PROJECT_NAME: str = "Baekjoon Talk"
    PROJECT_VERSION: str = "0.0.1"
    DEBUG: bool = Field(default=False)
    DESCRIPTION: str = """
    대화로 문제를 풀다, 백준talk
    사용자와의 대화를 진행하면서 알고리즘 풀이에 도움을 줄 수 있는 서비스
    """
    TAGS_METADATA: list[dict] = [
        {
            "name": "Auth",
            "description": "회원가입, 로그인, 유저정보 반환, 유저 사진 업로드 기능",
        },
        {
            "name": "Chat",
            "description": "대화 관리",
        },
        {
            "name": "Oauth",
            "description": "Google을 통한 인증 관련"
        }
    ]
    # Timezone 관련 내용들
    TIMEZONE: str = "Asia/Seoul"
    @property
    def KST(self) -> dt.tzinfo:
        return pytz.timezone(self.TIMEZONE);

    # JWT Token 관련 내용들
    JWT_SECRET_KEY: str = Field(..., env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24# 1 Day
    ACCESS_TOKEN_REFRESH_MINUTES: int = 60 * 24 * 3 # 3 Day

    # OAuth Credentials (Google)
    GOOGLE_CLIENT_ID: str | None = Field(default="31068809223-lkauufv46udblivod5ojqdu5fttbk03b.apps.googleusercontent.com", env="GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str | None = Field(default="", env="GOOGLE_CLIENT_SECRET")

    POSTGRES_USER: str = Field(default="", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(default="", env="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field(default="", env="POSTGRES_DB")
    POSTGRES_HOST: str = Field(default="", env="POSTGRES_HOST")
    POSTGRES_PORT: str = Field(default="", env="POSTGRES_PORT")

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    LLM_API_KEY: str = Field(default="", env="LLM_API_KEY")

    class Config:
        # .env file을 사용할 때
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()