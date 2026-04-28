from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.videos import Videos

class VideoRepositiry:

    async def get_all(self, db: AsyncSession):
        result = await db.execute(select(Videos))
        return result.scalars().all()