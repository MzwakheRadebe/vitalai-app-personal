"""
Database initialization and helpers.

Supports two backends:
- Supabase via supabase-py (HTTPS/REST) — production on Render
- SQLite via aiosqlite                  — local development only

Tables: users, appointments, faq

For Supabase (production):
  Table creation via the Management API or psql is required before first run
  because PostgREST (which supabase-py uses) cannot execute DDL statements.
  On startup this module will:
    1. Check whether the tables already exist by querying them.
    2. If they do not exist, log the DDL that must be run manually in the
       Supabase SQL Editor (https://supabase.com/dashboard/project/<ref>/sql).
  The app will continue to start regardless — it does NOT crash on missing tables.
"""

from __future__ import annotations

import logging
from app.config import get_settings

logger = logging.getLogger("db")


# ---------------------------------------------------------------------------
# DDL — PostgreSQL (Supabase)
# ---------------------------------------------------------------------------

PG_DDL = """
-- Run this in the Supabase SQL Editor:
-- https://supabase.com/dashboard/project/{ref}/sql/new

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'patient',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

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

CREATE INDEX IF NOT EXISTS idx_appointments_clinician_start_end
ON appointments (clinician, starts_at, ends_at);

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


# ---------------------------------------------------------------------------
# DDL — SQLite (local dev)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Entry point called from main.py on startup
# ---------------------------------------------------------------------------

async def init_db() -> None:
    """Initialize the database on application startup."""
    settings = get_settings()

    if settings.supabase_url and settings.supabase_service_key:
        await _init_supabase(settings.supabase_url, settings.supabase_service_key)
    else:
        logger.warning(
            "SUPABASE_URL / SUPABASE_SERVICE_KEY not set — "
            "using SQLite fallback (local dev only)"
        )
        await _init_sqlite(settings.sqlite_path)


# ---------------------------------------------------------------------------
# Supabase initialisation
# ---------------------------------------------------------------------------

async def _init_supabase(supabase_url: str, service_key: str) -> None:
    """
    Check that the required tables exist in Supabase and seed FAQ if empty.

    DDL cannot be run via PostgREST; if tables are missing we log the SQL and
    continue — the tables must be created manually in the Supabase SQL Editor.
    """
    try:
        from supabase import acreate_client, AsyncClientOptions
    except ImportError:
        logger.error(
            "supabase package not installed. Run: pip install 'supabase==2.15.2'"
        )
        return

    try:
        client = await acreate_client(
            supabase_url,
            service_key,
            options=AsyncClientOptions(
                postgrest_client_timeout=15,
                storage_client_timeout=15,
            ),
        )
    except Exception as e:
        logger.error("Failed to create Supabase async client: %s", e)
        return

    ref = supabase_url.replace("https://", "").split(".")[0]
    tables_ok = True

    # --- Check each table exists by doing a lightweight query ---
    for table in ("users", "appointments", "faq"):
        try:
            await client.table(table).select("id").limit(1).execute()
            logger.debug("Supabase: table %r exists.", table)
        except Exception as e:
            err = str(e)
            logger.warning(
                "Supabase: table %r does not exist or is inaccessible: %s",
                table, err,
            )
            tables_ok = False

    if not tables_ok:
        ddl = PG_DDL.format(ref=ref)
        logger.warning(
            "\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "  ACTION REQUIRED — Supabase tables are missing.\n"
            "  Open the Supabase SQL Editor and run the following DDL:\n"
            "  https://supabase.com/dashboard/project/%s/sql/new\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "%s\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            ref, ddl,
        )
        # Try the Supabase Management API as a last resort (may not be available
        # on all plans / keys, but worth attempting).
        await _try_management_api_ddl(ref, service_key, ddl)
    else:
        # Tables exist — seed FAQ if empty
        await _seed_faq_supabase(client)

    try:
        await client.auth.close()
    except Exception:
        pass

    logger.info("Supabase database check complete.")


async def _try_management_api_ddl(ref: str, service_key: str, ddl: str) -> None:
    """
    Attempt to run DDL via the Supabase Management API.

    This uses:  POST https://api.supabase.com/v1/projects/{ref}/database/query
    This endpoint requires a Supabase Management API token (not the service_role
    JWT) in the Authorization header.  We try with the service_role key anyway —
    it will likely return a 401/403 on the free tier, but we log the outcome.
    """
    import httpx

    url = f"https://api.supabase.com/v1/projects/{ref}/database/query"
    headers = {
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
    }
    payload = {"query": ddl}

    try:
        async with httpx.AsyncClient(timeout=15) as http:
            resp = await http.post(url, json=payload, headers=headers)
        if resp.status_code in (200, 201):
            logger.info(
                "Supabase Management API: DDL executed successfully (status %s).",
                resp.status_code,
            )
        else:
            logger.warning(
                "Supabase Management API: DDL attempt returned %s — %s. "
                "Please run the DDL manually in the SQL Editor.",
                resp.status_code, resp.text[:200],
            )
    except Exception as e:
        logger.warning(
            "Supabase Management API: DDL attempt failed (%s). "
            "Please run the DDL manually in the SQL Editor.",
            e,
        )


async def _seed_faq_supabase(client) -> None:
    """Seed the FAQ table if it is empty."""
    try:
        resp = await client.table("faq").select("*", count="exact").execute()
        count = resp.count if resp.count is not None else len(resp.data or [])

        if count == 0:
            rows = [{"question": q, "answer": a} for q, a in PG_FAQ_SEED]
            # upsert with on_conflict to handle duplicates gracefully
            await (
                client.table("faq")
                .upsert(rows, on_conflict="question")
                .execute()
            )
            logger.info("FAQ table seeded with %d entries.", len(rows))
    except Exception as e:
        logger.warning("FAQ seeding failed (non-fatal): %s", e)


# ---------------------------------------------------------------------------
# SQLite initialisation (local dev)
# ---------------------------------------------------------------------------

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
                pass  # index may already exist
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
        logger.error("SQLite initialization failed: %s", e)
