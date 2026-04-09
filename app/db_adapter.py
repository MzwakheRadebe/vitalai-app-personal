"""
Database adapter providing a unified async interface for PostgreSQL and SQLite.

- Uses asyncpg for PostgreSQL (production / Supabase)
- Uses aiosqlite for SQLite (local development)
- Accepts SQL with `?` placeholders; translates to `$1, $2...` for PostgreSQL
- Exposes simple fetchone, fetchall, execute, executemany, insert, commit
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Iterable, Optional

import aiosqlite

from app.config import get_settings


class SQLiteConnection:
    """Async SQLite wrapper."""
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


class PostgresConnection:
    """Async PostgreSQL wrapper normalizing SQLite `?` placeholders to `$1, $2...`"""
    def __init__(self, conn):
        self.conn = conn

    @staticmethod
    def _conv(sql: str) -> str:
        """Convert ? placeholders to $1, $2... for asyncpg."""
        result = []
        count = 0
        for ch in sql:
            if ch == "?":
                count += 1
                result.append(f"${count}")
            else:
                result.append(ch)
        return "".join(result)

    async def fetchone(self, sql: str, params: Iterable[Any] = ()) -> Optional[tuple]:
        row = await self.conn.fetchrow(self._conv(sql), *tuple(params))
        return tuple(row.values()) if row else None

    async def fetchall(self, sql: str, params: Iterable[Any] = ()) -> list[tuple]:
        rows = await self.conn.fetch(self._conv(sql), *tuple(params))
        return [tuple(r.values()) for r in rows]

    async def execute(self, sql: str, params: Iterable[Any] = ()) -> None:
        await self.conn.execute(self._conv(sql), *tuple(params))

    async def executemany(self, sql: str, seq_params: Iterable[Iterable[Any]]) -> None:
        converted = self._conv(sql)
        await self.conn.executemany(converted, [tuple(p) for p in seq_params])

    async def insert(self, sql: str, params: Iterable[Any] = ()) -> int:
        # For PostgreSQL, append RETURNING id to get the new row id
        returning_sql = self._conv(sql)
        if "returning" not in returning_sql.lower():
            returning_sql += " RETURNING id"
        row = await self.conn.fetchrow(returning_sql, *tuple(params))
        return row["id"] if row else 0

    async def commit(self) -> None:
        pass  # asyncpg uses auto-commit by default per statement

    async def close(self) -> None:
        await self.conn.close()


@asynccontextmanager
async def get_db():
    """Yield an async DB connection.

    Uses PostgreSQL (asyncpg) when DATABASE_URL is set, otherwise SQLite.
    """
    settings = get_settings()

    if settings.database_url:
        try:
            import asyncpg
        except ImportError:
            raise RuntimeError("asyncpg not installed. Run: pip install asyncpg")
        conn = await asyncpg.connect(settings.database_url)
        wrapper = PostgresConnection(conn)
        try:
            yield wrapper
        finally:
            await wrapper.close()
    else:
        conn = await aiosqlite.connect(settings.sqlite_path)
        wrapper = SQLiteConnection(conn)
        try:
            yield wrapper
        finally:
            await wrapper.close()
