# app/main.py

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.redis import get_redis_client
from app.core.configuration import settings
from app.routers import auth, chat, google_auth, test, friend
from app.db.database import init_db, reset_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        redis = get_redis_client()
        await redis.ping()
        print("연결 성공!")
    except Exception as e:
        print("Redis 연결 실패!", e)
        raise

    await reset_db()
    # await init_db()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description=settings.DESCRIPTION,
    summary="AI assistant for programming practice",
    openapi_tags=settings.TAGS_METADATA,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static File 등록
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Router 등록하기
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(google_auth.router, prefix="/oauth", tags=["Oauth"])
app.include_router(test.router, prefix="/test", tags=["Test"])
app.include_router(friend.router, prefix="/friend", tags=["Friend"])

@app.get("/")
async def root():
    return {"message": "Main Page"}