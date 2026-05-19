import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
sync_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
engine = create_engine(sync_url)

def check_emails():
    with engine.connect() as conn:
        res = conn.execute(text("""
            SELECT table_schema, table_name 
            FROM information_schema.tables 
            WHERE table_name = 'emails'
        """))
        for row in res:
            print(f"Table 'emails' belongs to schema: {row[0]}")

if __name__ == "__main__":
    check_emails()
