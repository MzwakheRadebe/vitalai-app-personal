"""
Database initialization and helpers.

Supports two backends:
- PostgreSQL via DATABASE_URL (Supabase or any Postgres — used in production)
- SQLite fallback via SQLITE_PATH (local development only)

Tables: users, appointments, faq
"""

from __future__ import annotations

import logging
from app.config import get_settings

logger = logging.getLogger("db")


# -- DDL for PostgreSQL --
PG_CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'patient',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

PG_CREATE_APPOINTMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS appointments (
    id SERIAL PRIMARY KEY,
    patient_name TEXT NOT NULL,
    clinician TEXT NOT NULL,
    department TEXT,
    starts_at TEXT NOT NULL,
    ends_at TEXT NOT NULL,
    reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (starts_at < ends_at)
);
"""

PG_CREATE_APPOINTMENTS_INDEX = """
CREATE INDEX IF NOT EXISTS idx_appointments_clinician_start_end
ON appointments (clinician, starts_at, ends_at);
"""

PG_CREATE_FAQ_TABLE = """
CREATE TABLE IF NOT EXISTS faq (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL UNIQUE,
    answer TEXT NOT NULL
);
"""

PG_FAQ_SEED = [
    ("Clinic hours?", "Mon–Fri 08:00–16:00"),
    ("Do I need my ID?", "Bring your SA ID or passport and any referral notes."),
    ("How do I book an appointment?", "Use the Patient Portal to book online, or call reception."),
    ("What languages are supported?", "VitalAI supports English, Zulu, Xhosa, Sotho, Tswana, and more."),
]


# -- DDL for SQLite (local dev) --
SQLITE_CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'patient',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

SQLITE_CREATE_APPOINTMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_name TEXT NOT NULL,
    clinician TEXT NOT NULL,
    department TEXT,
    starts_at TEXT NOT NULL,
    ends_at TEXT NOT NULL,
    reason TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (starts_at < ends_at)
);
"""

SQLITE_CREATE_APPOINTMENTS_INDEX = """
CREATE INDEX IF NOT EXISTS idx_appointments_clinician_start_end
ON appointments (clinician, starts_at, ends_at);
"""

SQLITE_CREATE_FAQ_TABLE = """
CREATE TABLE IF NOT EXISTS faq (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL UNIQUE,
    answer TEXT NOT NULL
);
"""


async def init_db() -> None:
    """Initialize the database on application startup."""
    settings = get_settings()

    if settings.database_url:
        await _init_postgres(settings.database_url)
    else:
        logger.warning("DATABASE_URL not set — using SQLite fallback (local dev only)")
        await _init_sqlite(settings.sqlite_path)


async def _init_postgres(database_url: str) -> None:
    """Set up PostgreSQL tables using asyncpg."""
    try:
        import asyncpg
    except ImportError:
        logger.error("asyncpg not installed. Run: pip install asyncpg")
        return

    try:
        conn = await asyncpg.connect(database_url)
        await conn.execute(PG_CREATE_USERS_TABLE)
        await conn.execute(PG_CREATE_APPOINTMENTS_TABLE)
        await conn.execute(PG_CREATE_APPOINTMENTS_INDEX)
        await conn.execute(PG_CREATE_FAQ_TABLE)

        # Seed FAQ on first run
        count = await conn.fetchval("SELECT COUNT(*) FROM faq")
        if count == 0:
            await conn.executemany(
                "INSERT INTO faq (question, answer) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                PG_FAQ_SEED,
            )

        await conn.close()
        logger.info("PostgreSQL database initialized successfully")
    except Exception as e:
        logger.error(f"PostgreSQL initialization failed: {e}")


async def _init_sqlite(sqlite_path: str) -> None:
    """Set up SQLite tables for local development."""
    try:
        import aiosqlite
    except ImportError:
        logger.error("aiosqlite not installed. Run: pip install aiosqlite")
        return

    try:
        async with aiosqlite.connect(sqlite_path) as db:
            await db.execute("PRAGMA foreign_keys = ON;")
            await db.execute("PRAGMA journal_mode = WAL;")
            await db.execute("PRAGMA synchronous = NORMAL;")
            await db.execute(SQLITE_CREATE_USERS_TABLE)
            await db.execute(SQLITE_CREATE_APPOINTMENTS_TABLE)
            try:
                await db.execute(SQLITE_CREATE_APPOINTMENTS_INDEX)
            except Exception:
                pass
            await db.execute(SQLITE_CREATE_FAQ_TABLE)
            await db.commit()

            # Seed FAQ
            async with db.execute("SELECT COUNT(*) FROM faq") as cur:
                (count,) = await cur.fetchone()
            if count == 0:
                await db.executemany(
                    "INSERT OR IGNORE INTO faq (question, answer) VALUES (?, ?)",
                    PG_FAQ_SEED,
                )
                await db.commit()

        logger.info("SQLite database initialized successfully")
    except Exception as e:
        logger.error(f"SQLite initialization failed: {e}")
