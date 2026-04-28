from sqlalchemy import Column, Integer, String
from app.core.database import Base


class Videos(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(100), unique=True, index=True)