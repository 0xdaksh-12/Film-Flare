from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from typing import AsyncGenerator
from src.config import Config


engine: AsyncEngine = create_async_engine(Config.DB_URL, echo=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        # await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
