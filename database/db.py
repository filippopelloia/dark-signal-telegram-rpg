from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from database.models import Base, Player
from config import DATABASE_URL
from typing import Optional

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_player(telegram_id: int) -> Optional[Player]:
    async with async_session() as session:
        result = await session.execute(
            select(Player).where(Player.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()


async def get_or_create_player(telegram_id: int, username: str = None) -> Player:
    async with async_session() as session:
        result = await session.execute(
            select(Player).where(Player.telegram_id == telegram_id)
        )
        player = result.scalar_one_or_none()
        if not player:
            player = Player(telegram_id=telegram_id, username=username)
            session.add(player)
            await session.commit()
            await session.refresh(player)
        return player


async def save_player(player: Player):
    from datetime import datetime
    async with async_session() as session:
        player.last_active = datetime.utcnow()
        merged = await session.merge(player)
        await session.commit()
        await session.refresh(merged)
        return merged


async def get_session():
    async with async_session() as session:
        yield session
