from sqlalchemy import Column, Integer, String, DateTime, func
from app.core.database import Base


class VideosDubbedModel(Base):
    __tablename__ = "videos_dubbed"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    file_name = Column(String)
    file_url = Column(String)
    thumbnail_url = Column(String)
    status = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(),
                        onupdate=func.now())
    deleted_at = Column(DateTime)
