import os

from dotenv import load_dotenv

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine
)

from sqlalchemy.orm import DeclarativeBase



load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise RuntimeError("DATABASE_URL is not set")

#old
#engine = create_async_engine(DATABASE_URL)

engine = create_async_engine(
    DATABASE_URL,
    #pool_size=50,
    #max_overflow=50,
    #pool_timeout=120
)



SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)




class Base(DeclarativeBase):
    pass


async def get_db():
    async with SessionLocal() as db:
        yield db