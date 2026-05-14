from fastapi import FastAPI
from app.api.video_dubber_ai import router
from app.core.config import settings
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine
from sqlalchemy import text
from app.core.config import settings
import asyncio
import sys

is_prod = settings.APP_ENV == "prod"

app = FastAPI(title=settings.APP_NAME,
              debug=settings.DEBUG,
              docs_url=None if is_prod else "/docs",
              redoc_url=None if is_prod else "/redoc",
              openapi_url=None if is_prod else "/openapi.json")

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://similartoolz.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,   # or ["*"] for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
