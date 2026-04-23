from fastapi import FastAPI
from app.api.routes import router
from app.core.config import Settings

app = FastAPI(title=Settings.APP_NAME,debug=Settings.DEBUG)

app.include_router(router, prefix="/api")