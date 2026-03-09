from configure import config
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase

engine = create_async_engine(
    url=config.DATABASE_URL,
    echo=True
)

SessionLocal = sessionmaker(
    bind=engine,
    class_= AsyncSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with SessionLocal() as db:
        yield db

async def creat_table():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)