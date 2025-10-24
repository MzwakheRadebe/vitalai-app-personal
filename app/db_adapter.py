"""
Database adapter providing a unified async interface for SQLite and MySQL.

- Uses `aiosqlite` for local development (SQLite)
- Uses `aiomysql` for MySQL when `Settings.mysql_url` is configured
- Accepts SQL with `?` placeholders; translates to `%s` for MySQL automatically
- Exposes simple `fetchone`, `fetchall`, `execute`, `executemany`, `insert`, `commit`

This lets route handlers remain mostly database-agnostic.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Iterable, Optional
from urllib.parse import urlparse

import aiosqlite
import aiomysql

from .config import get_settings


def _parse_mysql_url(url: str) -> dict[str, Any]:
    """Parse a SQLAlchemy-style MySQL URL into connection kwargs for aiomysql.

    Supports schemes like `mysql+pymysql://user:pass@host:port/db` or
    `mysql+aiomysql://user:pass@host:port/db`. We normalize to `mysql://` for
    parsing and return dict with keys: host, port, user, password, db.
    """
    if not url:
        raise ValueError("MySQL URL is empty")
    normalized = url.replace("mysql+pymysql://", "mysql://").replace("mysql+aiomysql://", "mysql://")
    parsed = urlparse(normalized)
    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 3306,
        "user": parsed.username or "",
        "password": parsed.password or "",
        "db": (parsed.path or "/").lstrip("/") or "",
        "autocommit": False,
        "charset": "utf8mb4",
    }


class SQLiteConnection:
    """Async SQLite wrapper providing a unified interface for FastAPI routes.

    Returns tuple rows; route code maps to dicts for responses.
    """
    def __init__(self, conn: aiosqlite.Connection):
        self.conn = conn
        # tuple-like rows by default; route code converts explicitly

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


class MySQLConnection:
    """Async MySQL wrapper normalizing SQLite-style `?` placeholders to `%s`.

    Exposes fetchone, fetchall, execute, executemany, insert, commit, close.
    """
    def __init__(self, conn: aiomysql.Connection):
        self.conn = conn

    @staticmethod
    def _conv(sql: str) -> str:
        # replace SQLite-style placeholders with MySQL `%s`
        return sql.replace("?", "%s")

    async def fetchone(self, sql: str, params: Iterable[Any] = ()) -> Optional[tuple]:
        async with self.conn.cursor() as cur:
            await cur.execute(self._conv(sql), tuple(params))
            return await cur.fetchone()

    async def fetchall(self, sql: str, params: Iterable[Any] = ()) -> list[tuple]:
        async with self.conn.cursor() as cur:
            await cur.execute(self._conv(sql), tuple(params))
            return await cur.fetchall()

    async def execute(self, sql: str, params: Iterable[Any] = ()) -> None:
        async with self.conn.cursor() as cur:
            await cur.execute(self._conv(sql), tuple(params))

    async def executemany(self, sql: str, seq_params: Iterable[Iterable[Any]]) -> None:
        async with self.conn.cursor() as cur:
            await cur.executemany(self._conv(sql), list(map(tuple, seq_params)))

    async def insert(self, sql: str, params: Iterable[Any] = ()) -> int:
        async with self.conn.cursor() as cur:
            await cur.execute(self._conv(sql), tuple(params))
            return cur.lastrowid or 0

    async def commit(self) -> None:
        await self.conn.commit()

    async def close(self) -> None:
        self.conn.close()


@asynccontextmanager
async def get_db():
    """Yield an async DB connection (MySQL when configured, otherwise SQLite).

    Selection:
    - When `Settings.mysql_url` is non-empty and starts with `mysql`, use aiomysql.
    - Otherwise, use aiosqlite at `Settings.sqlite_path`.

    Behavior:
    - Provides a thin wrapper (`MySQLConnection` or `SQLiteConnection`) with consistent API.
    - MySQL mode converts `?` placeholders to `%s` automatically.
    - Connections are closed after the context exits.
    """
    settings = get_settings()
    mysql_url = (settings.mysql_url or "").strip()
    use_mysql = mysql_url.lower().startswith("mysql")

    if use_mysql:
        kwargs = _parse_mysql_url(mysql_url)
        conn = await aiomysql.connect(**kwargs)
        wrapper = MySQLConnection(conn)
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