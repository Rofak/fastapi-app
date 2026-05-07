from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.videos_dubbed import VideosDubbedModel
from app.schemas.video_dubbed import VideoDubbedCreate, VideoDubbedUpdate


class VideosDubbedRepo:

    async def get_all(self, db: AsyncSession):
        result = await db.execute(select(VideosDubbedModel))
        return result.scalars().all()

    async def get_by_video_id(self, db: AsyncSession, video_id: int):
        result = await db.execute(select(VideosDubbedModel).where(VideosDubbedModel.id == video_id))
        return result.scalar_one_or_none()

    async def get_by_user_id(self, db: AsyncSession, user_id: int):
        result = await db.execute(select(VideosDubbedModel).where(VideosDubbedModel.user_id == user_id))
        return result.scalars().all()

    async def create(self, db: AsyncSession, video_dubbed_create: VideoDubbedCreate):
        db_video_dubbed = VideosDubbedModel(**video_dubbed_create.model_dump())
        db.add(db_video_dubbed)
        await db.commit()
        await db.refresh(db_video_dubbed)
        return db_video_dubbed

    async def update(self, db: AsyncSession, user_id: int, video_dubbed_update: VideoDubbedUpdate):
        video_dubbed = await self.get_by_user_id(db=db, user_id=user_id)
        if not video_dubbed:
            return None

        for key, value in video_dubbed_update.dict(exclude_unset=True).items():
            setattr(video_dubbed, key, value)

        await db.commit()
        await db.refresh(video_dubbed)
        return video_dubbed

    async def delete(self, db: AsyncSession, user_id: int):
        video_dubbed = await self.get_by_user_id(db=db, user_id=user_id)
        if not video_dubbed:
            return None

        await db.delete(video_dubbed)
        await db.commit()
        return video_dubbed

    async def update_video_id(self, db: AsyncSession, video_id: int, video_dubbed_update: VideoDubbedUpdate):
        video_dubbed = await self.get_by_video_id(db, video_id)
        if not video_dubbed:
            return None

        for key, value in video_dubbed_update.model_dump(exclude_unset=True).items():
            setattr(video_dubbed, key, value)

        await db.commit()
        await db.refresh(video_dubbed)
        return video_dubbed
