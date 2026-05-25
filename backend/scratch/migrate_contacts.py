import asyncio
from sqlalchemy import text
from app.database import engine

async def migrate():
    print("Running migration to add 'name' and 'role' to company_contacts...")
    async with engine.begin() as conn:
        # Check existing columns by inspecting table or attempting ALTER
        # We can safely run try-except blocks or check table structure
        try:
            # PostgreSQL syntax
            await conn.execute(text("ALTER TABLE company_contacts ADD COLUMN name VARCHAR"))
            print("Added column 'name' successfully.")
        except Exception as e:
            if "already exists" in str(e) or "duplicate column" in str(e):
                print("Column 'name' already exists.")
            else:
                print(f"Failed to add column 'name' (may be SQLite or already exists): {e}")
                # Try SQLite syntax
                try:
                    await conn.execute(text("ALTER TABLE company_contacts ADD COLUMN name TEXT"))
                    print("Added column 'name' (SQLite) successfully.")
                except Exception as ex:
                    print(f"SQLite ALTER 'name' failed: {ex}")

        try:
            # PostgreSQL syntax
            await conn.execute(text("ALTER TABLE company_contacts ADD COLUMN role VARCHAR"))
            print("Added column 'role' successfully.")
        except Exception as e:
            if "already exists" in str(e) or "duplicate column" in str(e):
                print("Column 'role' already exists.")
            else:
                print(f"Failed to add column 'role' (may be SQLite or already exists): {e}")
                # Try SQLite syntax
                try:
                    await conn.execute(text("ALTER TABLE company_contacts ADD COLUMN role TEXT"))
                    print("Added column 'role' (SQLite) successfully.")
                except Exception as ex:
                    print(f"SQLite ALTER 'role' failed: {ex}")

    print("Migration finished!")

if __name__ == "__main__":
    asyncio.run(migrate())
