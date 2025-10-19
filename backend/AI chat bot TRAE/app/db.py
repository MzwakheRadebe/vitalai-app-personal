"""
SQLite database initialization and helpers.

- Creates tables for `appointments` and `faq` on app startup.
- Provides simple DDL definitions and a utility initializer.
- Uses ISO8601 strings for datetime fields to keep comparisons simple.

Note: We open connections per request using `aiosqlite.connect` rather than
sharing one global connection, which keeps concurrency straightforward.
"""

from __future__ import annotations

import aiosqlite
from .config import get_settings


# -- DDL definitions (kept simple; adjust as schema evolves) --
CREATE_APPOINTMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_name TEXT NOT NULL,
    clinician TEXT NOT NULL,
    starts_at TEXT NOT NULL,  -- ISO8601 datetime string
    ends_at TEXT NOT NULL,    -- ISO8601 datetime string
    CHECK (starts_at < ends_at)
);
"""

CREATE_APPOINTMENTS_INDEX = """
CREATE INDEX IF NOT EXISTS idx_appointments_clinician_start_end
ON appointments (clinician, starts_at, ends_at);
"""

CREATE_FAQ_TABLE = """
CREATE TABLE IF NOT EXISTS faq (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL UNIQUE,
    answer TEXT NOT NULL
);
"""

CREATE_FAQ_UNIQUE_INDEX = """
CREATE UNIQUE INDEX IF NOT EXISTS idx_faq_question_unique
ON faq (question);
"""

async def init_db() -> None:
    """Initialize the SQLite database with required tables.

    This runs at application startup to ensure tables exist.
    """
    settings = get_settings()
    async with aiosqlite.connect(settings.sqlite_path) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        await db.execute("PRAGMA journal_mode = WAL;")
        await db.execute("PRAGMA synchronous = NORMAL;")
        await db.execute(CREATE_APPOINTMENTS_TABLE)
        await db.execute(CREATE_APPOINTMENTS_INDEX)
        await db.execute(CREATE_FAQ_TABLE)
        try:
            await db.execute(CREATE_FAQ_UNIQUE_INDEX)
        except Exception:
            # If duplicates already exist, this will fail; leave as-is.
            pass
        await db.commit()

        # Seed FAQ entries on first run for developer visibility.
        try:
            async with db.execute("SELECT COUNT(*) FROM faq") as cur:
                (count,) = await cur.fetchone()
            if count == 0:
                await db.executemany(
                    "INSERT INTO faq (question, answer) VALUES (?, ?)",
                    [
                        ("Clinic hours?", "Mon–Fri 08:00–16:00"),
                        ("Do I need my ID?", "Bring SA ID or passport and any referral notes."),
                    ],
                )
                await db.commit()
        except Exception:
            # Non-fatal: if seed fails, continue; FAQ can be added via API.
            pass