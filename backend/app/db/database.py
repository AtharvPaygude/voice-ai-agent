"""
Async SQLAlchemy database engine and session management.

Supports PostgreSQL via asyncpg and SQLite via aiosqlite.
Reads DATABASE_URL from settings (app/core/config.py / .env), and auto-converts
URLs into their async forms (postgresql+asyncpg://, sqlite+aiosqlite://).
"""
import re
import urllib.parse
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


def _to_async_url(url: str) -> str:
    """Convert supported database URLs to async SQLAlchemy URLs.

    Handles:
    - sqlite:/// -> sqlite+aiosqlite:///
    - postgresql:// and postgres:// -> postgresql+asyncpg://
    - Stripping bracket placeholders like [YOUR-PASSWORD]
    - Percent-encoding special characters in password (such as '@')
    - Removing incompatible query params like 'sslmode' that asyncpg rejects
    """
    if not url or not url.strip():
        return ""

    url = url.strip()

    match = re.match(r"^([a-zA-Z0-9+]+)://(.*)$", url)
    if not match:
        return url

    scheme, rest = match.groups()

    if scheme in ("postgresql", "postgres", "postgresql+asyncpg"):
        query_str = ""
        if "?" in rest:
            rest, query_str = rest.split("?", 1)

        if "@" in rest:
            userinfo, host_part = rest.rsplit("@", 1)
            if ":" in userinfo:
                user, password = userinfo.split(":", 1)
                # Strip square brackets if copied from Supabase placeholder [YOUR-PASSWORD]
                if password.startswith("[") and password.endswith("]"):
                    password = password[1:-1]
                # Unquote to avoid double encoding, then quote
                password = urllib.parse.unquote(password)
                password = urllib.parse.quote(password, safe="")
                rest = f"{user}:{password}@{host_part}"

        # Clean query parameters for asyncpg (remove sslmode and ssl to avoid conflicts with connect_args)
        if query_str:
            params = urllib.parse.parse_qs(query_str)
            params.pop("sslmode", None)
            params.pop("ssl", None)
            new_query = urllib.parse.urlencode(params, doseq=True)
            if new_query:
                rest = f"{rest}?{new_query}"

        return f"postgresql+asyncpg://{rest}"

    if scheme in ("sqlite", "sqlite+aiosqlite"):
        if not scheme.endswith("+aiosqlite"):
            return f"sqlite+aiosqlite://{rest}"
        return url

    return url


database_url: str = _to_async_url(settings.DATABASE_URL)

engine: Optional[AsyncEngine] = None
AsyncSessionLocal: Optional[async_sessionmaker[AsyncSession]] = None

if database_url:
    engine_options = {"echo": False, "pool_pre_ping": True, "pool_recycle": 300}
    if database_url.startswith("postgresql+asyncpg://"):
        engine_options["connect_args"] = {"ssl": "require"}

    engine = create_async_engine(database_url, **engine_options)
    AsyncSessionLocal = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )


async def init_db() -> None:
    """Create all tables if they don't exist yet. Call this on app startup."""
    if engine is None:
        raise RuntimeError(
            "Cannot initialize database: DATABASE_URL is empty or not configured. "
            "Please check backend/.env."
        )

    # Import models here so they're registered on Base.metadata before create_all
    from app.db import models  # noqa: F401
    from sqlalchemy import text

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Handle SQLite additive migrations only for SQLite dialect
        if engine.dialect.name == "sqlite":
            tables_cols = {
                "business_profiles": [
                    ("industry", "TEXT DEFAULT 'service_business'"),
                    ("capabilities", "JSON DEFAULT '[]'"),
                    ("knowledge_base", "JSON DEFAULT '[]'"),
                    ("tools", "JSON DEFAULT '[]'"),
                    ("workflows", "JSON DEFAULT '[]'"),
                    ("permissions", "JSON DEFAULT '{}'"),
                    ("policies", "JSON DEFAULT '{}'"),
                    ("category", "TEXT DEFAULT 'service_business'"),
                    ("address", "TEXT DEFAULT ''"),
                    ("city", "TEXT DEFAULT ''"),
                    ("timezone", "TEXT DEFAULT 'UTC'"),
                    ("contact_email", "TEXT DEFAULT ''"),
                    ("contact_phone", "TEXT DEFAULT ''"),
                    ("operating_hours", "JSON DEFAULT '{}'"),
                    ("breaks", "JSON DEFAULT '[]'"),
                    ("slot_duration_minutes", "INTEGER DEFAULT 30"),
                    ("specialties", "JSON DEFAULT '[]'"),
                    ("practitioners", "JSON DEFAULT '[]'"),
                    ("inventory", "JSON DEFAULT '[]'"),
                    ("holidays", "JSON DEFAULT '[]'"),
                    ("onboarding_status", "TEXT DEFAULT 'completed'"),
                    ("onboarding_step", "TEXT DEFAULT 'done'"),
                    ("onboarding_answers", "JSON DEFAULT '{}'"),
                    ("is_published", "BOOLEAN DEFAULT 1"),
                ],
                "appointments": [
                    ("business_profile_id", "TEXT"),
                    ("notes", "TEXT DEFAULT ''"),
                    ("reminder_enabled", "BOOLEAN DEFAULT 0"),
                    ("reminder_offset", "TEXT DEFAULT '1_day'"),
                    ("reminder_sent", "BOOLEAN DEFAULT 0"),
                    ("reminder_status", "TEXT DEFAULT 'pending'"),
                    ("practitioner_name", "TEXT"),
                    ("customer_name", "TEXT"),
                    ("customer_phone", "TEXT"),
                    ("duration_minutes", "INTEGER DEFAULT 30"),
                ],
                "bookings": [
                    ("reminder_status", "TEXT DEFAULT 'pending'"),
                ],
                "calls": [
                    ("business_profile_id", "TEXT"),
                    ("customer_id", "TEXT"),
                ],
                "users": [
                    ("full_name", "TEXT DEFAULT ''"),
                    ("business_profile_id", "TEXT"),
                    ("session_token_hash", "TEXT"),
                    ("is_active", "BOOLEAN DEFAULT 1"),
                    ("last_login_at", "DATETIME"),
                ],
                "customers": [
                    ("email", "TEXT DEFAULT ''"),
                ],
                "escalations": [
                    ("issues", "JSON DEFAULT '[]'"),
                    ("caller_email", "TEXT DEFAULT ''"),
                    ("confirm_token", "TEXT DEFAULT ''"),
                    ("user_confirmation", "TEXT DEFAULT 'pending'"),
                    ("user_note", "TEXT DEFAULT ''"),
                    ("email_status", "TEXT DEFAULT 'not_sent'"),
                ],
                "appointments": [
                    ("reminder_status", "TEXT DEFAULT 'pending'"),
                ],
                "bookings": [
                    ("reminder_status", "TEXT DEFAULT 'pending'"),
                ],
            }
            for table, cols in tables_cols.items():
                try:
                    res = await conn.execute(text(f"PRAGMA table_info({table})"))
                    existing = {row[1] for row in res.fetchall()}
                    for col_name, col_def in cols:
                        if col_name not in existing:
                            await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}"))
                except Exception:
                    pass
        elif engine.dialect.name == "postgresql":
            pg_cols = {
                "customers": [("email", "VARCHAR DEFAULT ''")],
                "escalations": [
                    ("issues", "JSON DEFAULT '[]'"),
                    ("caller_email", "VARCHAR DEFAULT ''"),
                    ("confirm_token", "VARCHAR DEFAULT ''"),
                    ("user_confirmation", "VARCHAR DEFAULT 'pending'"),
                    ("user_note", "TEXT DEFAULT ''"),
                    ("email_status", "VARCHAR DEFAULT 'not_sent'"),
                ],
                "appointments": [
                    ("reminder_status", "VARCHAR DEFAULT 'pending'"),
                ],
                "bookings": [
                    ("reminder_status", "VARCHAR DEFAULT 'pending'"),
                ],
            }
            for table, cols in pg_cols.items():
                for col_name, col_def in cols:
                    try:
                        await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col_name} {col_def}"))
                    except Exception:
                        pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields a request-scoped DB session."""
    if AsyncSessionLocal is None:
        raise RuntimeError(
            "Database session is not available because DATABASE_URL is not configured. "
            "Please configure DATABASE_URL in backend/.env."
        )
    async with AsyncSessionLocal() as session:
        yield session
