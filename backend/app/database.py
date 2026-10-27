import os
from urllib.parse import quote_plus

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


def database_url() -> str:
    user = quote_plus(os.environ["POSTGRES_USER"])
    password = quote_plus(os.environ["POSTGRES_PASSWORD"])
    host = os.environ.get("POSTGRES_HOST", "localhost")
    database = quote_plus(os.environ["POSTGRES_DB"])
    return f"postgresql+asyncpg://{user}:{password}@{host}:5432/{database}"


engine = create_async_engine(database_url(), pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    async with SessionLocal() as session:
        yield session
