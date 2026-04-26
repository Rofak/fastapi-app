from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "FastAPI UV Starter"
    DEBUG: bool = True
    AZURE_TTS_KEY:str
    AZURE_TTS_REGION:str

    class Config:
        env_file = ".env"

settings = Settings()