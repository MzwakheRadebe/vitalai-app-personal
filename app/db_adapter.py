"""
Database adapter — PostgreSQL (psycopg2-binary) + SQLite (aiosqlite).

psycopg2-binary ships pre-built wheels (no C compilation on Render/Heroku).
asyncpg requires gcc which is unavailable on many free-tier hosts.

PostgreSQL is used in production (DATABASE_URL set).
SQLite is used for local development (no DATABASE_URL).
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from functools import partial
from typing import Any, Iterable, Optional

import aiosqlite

from app.config import get_settings


# ─────────────────────────────────────────────────────────────────────────────
# SQLite wrapper (local dev)
# ─────────────────────────────────────────────────────────────────────────────

class SQLiteConnection:
    def __init__(self, conn: aiosqlite.Connection):
        self.conn = conn

    async def fetchone(self, sql: str, params: Iterable[Any] = ()) -> Optional[tuple]:
        async with self.conn.execute(sql, tuple(params)) as cur:
            return await cur.fetchone()

    async def fetchall(self, sql: str, params: Iterable[Any] = ()) -> list[tuple]:
        async with self.conn.execute(sql, tuple(params)) as cur:
            return await cur.fetchall()

    async def execute(self, sql: str, params: Iterable[Any] = ()) -> None:
        await self.conn.execute(sql, tuple(params))

    async def executemany(self, sql: str, seq_params: Iterable[Iterable[Any]]) -> None:
        await self.conn.executemany(sql, list(map(tuple, seq_params)))

    async def insert(self, sql: str, params: Iterable[Any] = ()) -> int:
        async with self.conn.execute(sql, tuple(params)) as cur:
            return cur.lastrowid

    async def commit(self) -> None:
        await self.conn.commit()

    async def close(self) -> None:
        await self.conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# PostgreSQL wrapper (production) — psycopg2 run in thread executor
# ─────────────────────────────────────────────────────────────────────────────

class PostgresConnection:
    """Wraps a psycopg2 connection, running sync calls in a thread pool
    so they don't block the asyncio event loop."""

    def __init__(self, conn):
        self.conn = conn

    @staticmethod
    def _to_pg(sql: str) -> str:
        """Convert SQLite ? placeholders to psycopg2 %s placeholders."""
        return sql.replace("?", "%s")

    async def _run(self, fn):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, fn)

    async def fetchone(self, sql: str, params: Iterable[Any] = ()) -> Optional[tuple]:
        def _():
            with self.conn.cursor() as cur:
                cur.execute(self._to_pg(sql), tuple(params))
                return cur.fetchone()
        return await self._run(_)

    async def fetchall(self, sql: str, params: Iterable[Any] = ()) -> list[tuple]:
        def _():
            with self.conn.cursor() as cur:
                cur.execute(self._to_pg(sql), tuple(params))
                return cur.fetchall()
        return await self._run(_)

    async def execute(self, sql: str, params: Iterable[Any] = ()) -> None:
        def _():
            with self.conn.cursor() as cur:
                cur.execute(self._to_pg(sql), tuple(params))
        await self._run(_)

    async def executemany(self, sql: str, seq_params: Iterable[Iterable[Any]]) -> None:
        rows = list(map(tuple, seq_params))
        def _():
            with self.conn.cursor() as cur:
                cur.executemany(self._to_pg(sql), rows)
        await self._run(_)

    async def insert(self, sql: str, params: Iterable[Any] = ()) -> int:
        pg_sql = self._to_pg(sql)
        if "returning" not in pg_sql.lower():
            pg_sql += " RETURNING id"
        def _():
            with self.conn.cursor() as cur:
                cur.execute(pg_sql, tuple(params))
                row = cur.fetchone()
                return row[0] if row else 0
        return await self._run(_)

    async def commit(self) -> None:
        await self._run(self.conn.commit)

    async def close(self) -> None:
        await self._run(self.conn.close)


# ─────────────────────────────────────────────────────────────────────────────
# Context manager — picks PostgreSQL or SQLite based on DATABASE_URL
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def get_db():
    settings = get_settings()

    if settings.database_url:
        try:
            import psycopg2
        except ImportError:
            raise RuntimeError("psycopg2-binary not installed. Run: pip install psycopg2-binary")

        loop = asyncio.get_event_loop()
        conn = await loop.run_in_executor(
            None, partial(psycopg2.connect, settings.database_url)
        )
        conn.autocommit = False
        wrapper = PostgresConnection(conn)
        try:
            yield wrapper
        except Exception:
            await loop.run_in_executor(None, conn.rollback)
            raise
        finally:
            await wrapper.close()
    else:
        conn = await aiosqlite.connect(settings.sqlite_path)
        wrapper = SQLiteConnection(conn)
        try:
            yield wrapper
        finally:
            await wrapper.close()
