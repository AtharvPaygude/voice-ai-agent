import asyncio
import sys
from pathlib import Path

# Ensure backend root is on sys.path so app imports work from any working directory
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.db.database import _to_async_url


async def main():
    raw_url = settings.DATABASE_URL
    if not raw_url or not raw_url.strip():
        print("CONFIGURATION ERROR: DATABASE_URL is not set or empty.")
        print("Please configure DATABASE_URL in C:\\DEMO\\backend\\.env.")
        sys.exit(1)

    database_url = _to_async_url(raw_url)
    scheme = database_url.split("://")[0] if "://" in database_url else "unknown"

    if database_url.startswith("sqlite"):
        print(f"CONFIGURATION ERROR: DATABASE_URL is configured for SQLite ({scheme}). Expected PostgreSQL.")
        print("Please configure your Supabase PostgreSQL URI in C:\\DEMO\\backend\\.env.")
        sys.exit(1)

    if not database_url.startswith("postgresql+asyncpg://"):
        print(f"CONFIGURATION ERROR: Unsupported or invalid database scheme '{scheme}'. Expected PostgreSQL.")
        sys.exit(1)

    engine_options = {"echo": False, "connect_args": {"ssl": "require"}}
    engine = create_async_engine(database_url, **engine_options)

    try:
        async with engine.connect() as connection:
            result = await connection.execute(
                text("SELECT current_database(), current_user;")
            )
            database, user = result.one()

            print("SUCCESS: Connected to PostgreSQL!")
            print("Database:", database)
            print("Connected user:", user)
            print("Database scheme:", scheme)

    except Exception as error:
        print("PostgreSQL connection failed:")
        print(type(error).__name__, str(error))
        sys.exit(1)

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
