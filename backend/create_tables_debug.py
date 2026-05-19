import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.database import Base
from app.models import User, JobListing, CompanyProfile, OutreachEmail, TrackingEvent

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, connect_args={"prepared_statement_cache_size": 0, "statement_cache_size": 0})

async def debug_create():
    print("Registered tables in Base.metadata:")
    for name in Base.metadata.tables.keys():
        print(f"  - {name}")
        
    async with engine.begin() as conn:
        # Set search path
        await conn.execute(text("SET search_path TO public"))
        
        # Check if users table already exists in public schema
        res = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM pg_tables 
                WHERE schemaname = 'public' AND tablename = 'users'
            )
        """))
        exists = res.scalar()
        print(f"\nDoes public.users exist? {exists}")
        
        # Let's try to create users table first explicitly
        if not exists:
            print("\nAttempting to create public.users table...")
            try:
                # We can construct the DDL for the users table from its metadata
                # Or just run create_all on just the 'users' table
                await conn.run_sync(lambda connection: Base.metadata.tables['users'].create(connection))
                print("✓ Successfully created public.users table!")
            except Exception as e:
                print(f"✗ Failed to create public.users table: {e}")
        
        # Now let's try to create the rest of the tables
        print("\nAttempting to create all other tables...")
        try:
            await conn.run_sync(Base.metadata.create_all)
            print("✓ Successfully created all tables!")
        except Exception as e:
            print(f"✗ Failed to create all tables: {e}")

if __name__ == "__main__":
    asyncio.run(debug_create())
