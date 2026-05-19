from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

# Use SQLite or PostgreSQL based on env.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./job_outreach.db")

connect_args = {}
if DATABASE_URL.startswith("postgresql"):
    connect_args = {
        "prepared_statement_cache_size": 0,
        "statement_cache_size": 0
    }
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, connect_args=connect_args, echo=False)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
