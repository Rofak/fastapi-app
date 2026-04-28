from pydantic_settings import BaseSettings
from pydantic import computed_field
from urllib.parse import quote_plus

class Settings(BaseSettings):
    APP_NAME: str = "FastAPI UV Starter"
    DEBUG: bool = True
    AZURE_TTS_KEY:str
    AZURE_TTS_REGION:str
    GEMINI_API_KEY:str
    DB_HOST: str 
    DB_PORT: int 
    DB_USER: str 
    DB_PASSWORD: str 
    DB_NAME: str 

    class Config:
        env_file = ".env"

    @computed_field(return_type=str)
    @property
    def DATABASE_URL(self):
        password = quote_plus(self.DB_PASSWORD)
        return (
            f"mysql+asyncmy://{self.DB_USER}:{password}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

settings = Settings()