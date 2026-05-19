import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
sync_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
engine = create_engine(sync_url)

def check_all_users_tables():
    with engine.connect() as conn:
        res = conn.execute(text("""
            SELECT schemaname, tablename, tableowner 
            FROM pg_tables 
            WHERE tablename = 'users'
        """))
        print("pg_tables matches for 'users':")
        for row in res:
            print(f"Schema: {row[0]}, Table: {row[1]}, Owner: {row[2]}")
            
        # Check all tables in public schema
        res_public = conn.execute(text("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
        """))
        print("\nAll tables in public schema:")
        for row in res_public:
            print(f"  - {row[0]}")

if __name__ == "__main__":
    check_all_users_tables()
