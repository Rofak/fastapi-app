from fastapi import FastAPI
from app.api.routes import router
from app.core.config import settings

app = FastAPI(title=settings.APP_NAME,debug=settings.DEBUG)

app.include_router(router, prefix="/api")