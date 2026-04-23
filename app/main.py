from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="FastAPI UV Starter")

app.include_router(router, prefix="/api")