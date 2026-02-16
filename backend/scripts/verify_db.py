import asyncio
from sqlalchemy import text
from app.core.db import engine

async def verify_tables():
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        )
        tables = [row[0] for row in result.fetchall()]
        print(f"Tables found: {tables}")
        
        required = {'users', 'api_keys', 'qr_codes', 'alembic_version'}
        missing = required - set(tables)
        
        if missing:
            print(f"MISSING TABLES: {missing}")
            exit(1)
        else:
            print("All required tables present.")

if __name__ == "__main__":
    asyncio.run(verify_tables())
