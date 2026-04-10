"""
Database adapter — Supabase PostgREST (httpx over HTTPS) + SQLite (aiosqlite).

Backend selection:
  - SUPABASE_URL + SUPABASE_SERVICE_KEY set → httpx PostgREST client (HTTPS port 443)
  - Neither set                             → aiosqlite (local development only)

Why httpx instead of psycopg2 / asyncpg?
  Render free tier cannot reach Supabase's IPv6-only PostgreSQL host on port 5432.
  The PostgREST REST API runs over HTTPS (port 443) and works from any environment.
  We call it directly with httpx — no extra packages required beyond what FastAPI
  already needs.

Interface contract (both wrappers implement the same methods):
  fetchone(sql, params) -> Optional[tuple]
  fetchall(sql, params) -> list[tuple]
  execute(sql, params)  -> None          (UPDATE / DELETE)
  insert(sql, params)   -> int           (returns new row id)
  commit()              -> None          (no-op for Supabase — auto-commit via REST)
  close()               -> None
"""
from __future__ import annotations

import re
import logging
from contextlib import asynccontextmanager
from typing import Any, Iterable, Optional

import aiosqlite
import httpx

from app.config import get_settings

logger = logging.getLogger("db_adapter")


# ─────────────────────────────────────────────────────────────────────────────
# SQLite wrapper  (local development fallback)
# ─────────────────────────────────────────────────────────────────────────────

class SQLiteConnection:
    """Thin async wrapper around an aiosqlite connection."""

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
            return cur.lastrowid  # type: ignore[return-value]

    async def commit(self) -> None:
        await self.conn.commit()

    async def close(self) -> None:
        await self.conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# SQL → PostgREST translator helpers
# ─────────────────────────────────────────────────────────────────────────────

_RE_SELECT_FROM = re.compile(
    r"SELECT\s+(.+?)\s+FROM\s+(\w+)(.*)",
    re.IGNORECASE | re.DOTALL,
)
_RE_INSERT_INTO = re.compile(
    r"INSERT\s+(?:OR\s+IGNORE\s+)?INTO\s+(\w+)\s*\(([^)]+)\)\s*VALUES\s*\(([^)]+)\)",
    re.IGNORECASE,
)
_RE_UPDATE = re.compile(
    r"UPDATE\s+(\w+)\s+SET\s+(.+?)\s+WHERE\s+(.+)",
    re.IGNORECASE | re.DOTALL,
)
_RE_DELETE = re.compile(
    r"DELETE\s+FROM\s+(\w+)\s+WHERE\s+(.+)",
    re.IGNORECASE | re.DOTALL,
)
_RE_COUNT   = re.compile(r"COUNT\s*\(\s*\*\s*\)", re.IGNORECASE)
_RE_WHERE   = re.compile(r"\bWHERE\b\s*(.+?)(?:\s+ORDER BY|\s+LIMIT|\s+OFFSET|$)",
                          re.IGNORECASE | re.DOTALL)
_RE_ORDER   = re.compile(r"ORDER\s+BY\s+(\S+)(?:\s+(ASC|DESC))?", re.IGNORECASE)
_RE_LIMIT   = re.compile(r"LIMIT\s+\?", re.IGNORECASE)
_RE_OFFSET  = re.compile(r"OFFSET\s+\?", re.IGNORECASE)

# Column order for each table — converts dicts back to tuples so routes can
# index columns by position (matching the SQL SELECT column list).
_TABLE_COLUMNS: dict[str, list[str]] = {
    "users":        ["id", "email", "password_hash", "role", "created_at"],
    "appointments": ["id", "patient_name", "clinician", "department",
                     "starts_at", "ends_at", "reason", "created_at"],
    "faq":          ["id", "question", "answer"],
}


def _parse_where_conditions(where_clause: str, params: list) -> tuple[list, list]:
    """
    Parse the narrow set of WHERE clauses used in this app into
    (filters_list, remaining_params).

    filters_list contains (column, postgrest_op, value) triples or
    ('__or__', or_string, None) for OR expressions.
    """
    clause = where_clause.strip()
    remaining = list(params)
    filters: list[tuple[str, str, Any]] = []

    parts = re.split(r"\bAND\b", clause, flags=re.IGNORECASE)

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # NOT (ends_at <= ? OR starts_at >= ?) — appointment conflict check
        not_match = re.match(
            r"NOT\s*\(\s*ends_at\s*<=\s*\?\s+OR\s+starts_at\s*>=\s*\?\s*\)",
            part, re.IGNORECASE,
        )
        if not_match:
            val_ends   = remaining.pop(0) if remaining else None
            val_starts = remaining.pop(0) if remaining else None
            filters.append(("ends_at", "gt", val_ends))
            filters.append(("starts_at", "lt", val_starts))
            continue

        # col op ?  (standard comparison)
        cmp = re.match(
            r"([\w.]+)\s*(=|!=|<>|>=|<=|>|<|LIKE|ILIKE)\s*\?",
            part, re.IGNORECASE,
        )
        if cmp:
            col, op_raw = cmp.group(1), cmp.group(2).upper()
            val = remaining.pop(0) if remaining else None
            op_map = {"=": "eq", "!=": "neq", "<>": "neq",
                      ">": "gt", ">=": "gte", "<": "lt", "<=": "lte",
                      "LIKE": "like", "ILIKE": "ilike"}
            filters.append((col, op_map.get(op_raw, "eq"), val))
            continue

        # (question LIKE ? OR answer LIKE ?) — FAQ search
        or_like = re.match(
            r"\(\s*([\w.]+)\s+LIKE\s+\?\s+OR\s+([\w.]+)\s+LIKE\s+\?\s*\)",
            part, re.IGNORECASE,
        )
        if or_like:
            col1, col2 = or_like.group(1), or_like.group(2)
            val1 = remaining.pop(0) if remaining else None
            val2 = remaining.pop(0) if remaining else None
            filters.append(("__or__", f"{col1}.like.{val1},{col2}.like.{val2}", None))
            continue

        logger.debug("db_adapter: unrecognised WHERE part, skipping: %r", part)

    return filters, remaining


def _build_postgrest_params(filters: list, order_col=None, order_asc=True,
                             limit=None, offset=None) -> dict:
    """Build PostgREST query string params from parsed filter list."""
    params: dict[str, Any] = {}
    for col, op, val in filters:
        if col == "__or__":
            params["or"] = f"({op})"
        else:
            params[col] = f"{op}.{val}"
    if order_col:
        direction = "asc" if order_asc else "desc"
        params["order"] = f"{order_col}.{direction}"
    if limit is not None:
        params["limit"] = str(limit)
    if offset is not None:
        params["offset"] = str(offset)
    return params


# ─────────────────────────────────────────────────────────────────────────────
# Supabase / PostgREST wrapper (production)
# ─────────────────────────────────────────────────────────────────────────────

class SupabaseConnection:
    """
    Translates the SQL-like interface into direct httpx calls against the
    Supabase PostgREST REST API (HTTPS port 443).

    Only the query patterns used in this application are supported.
    """

    def __init__(self, base_url: str, service_key: str):
        self._base = base_url.rstrip("/") + "/rest/v1"
        self._headers = {
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def _url(self, table: str) -> str:
        return f"{self._base}/{table}"

    def _parse_select(self, sql: str, params: list):
        m = _RE_SELECT_FROM.match(sql.strip())
        if not m:
            raise RuntimeError(f"db_adapter: cannot parse SELECT: {sql!r}")

        raw_cols  = m.group(1).strip()
        table     = m.group(2).strip()
        rest      = m.group(3).strip()

        is_count     = bool(_RE_COUNT.search(raw_cols))
        is_existence = (raw_cols == "1")

        if is_count:
            select_str = "*"
            select_cols = ["count"]
        elif is_existence:
            select_str  = "id"
            select_cols = ["id"]
        else:
            select_cols = [c.strip() for c in raw_cols.split(",")]
            select_str  = ",".join(select_cols)

        remaining = list(params)
        filters   = []
        where_m   = _RE_WHERE.search(rest)
        if where_m:
            filters, remaining = _parse_where_conditions(where_m.group(1), remaining)

        order_col = None
        order_asc = True
        order_m   = _RE_ORDER.search(rest)
        if order_m:
            order_col = order_m.group(1)
            order_asc = (order_m.group(2) or "ASC").upper() == "ASC"

        limit  = None
        offset = None
        if _RE_LIMIT.search(rest) and remaining:
            limit  = int(remaining.pop(0))
        if _RE_OFFSET.search(rest) and remaining:
            offset = int(remaining.pop(0))

        return (table, select_str, select_cols, filters,
                order_col, order_asc, limit, offset, is_count, is_existence)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def fetchone(self, sql: str, params: Iterable[Any] = ()) -> Optional[tuple]:
        sql = sql.strip()

        # Health check shortcut — no network call needed
        if re.match(r"SELECT\s+1\s*$", sql, re.IGNORECASE):
            return (1,)

        (table, select_str, select_cols, filters,
         order_col, order_asc, limit, offset,
         is_count, is_existence) = self._parse_select(sql, list(params))

        qs = _build_postgrest_params(filters, order_col, order_asc, 1, None)
        qs["select"] = select_str

        if is_count:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(
                    self._url(table), headers={**self._headers,
                    "Prefer": "count=exact"},
                    params=qs,
                )
            r.raise_for_status()
            count_header = r.headers.get("content-range", "0/0").split("/")[-1]
            try:
                count = int(count_header)
            except ValueError:
                count = len(r.json()) if r.json() else 0
            return (count,)

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(self._url(table), headers=self._headers, params=qs)
        r.raise_for_status()
        rows = r.json()
        if not rows:
            return None
        if is_existence:
            return (1,)
        return tuple(rows[0].get(c) for c in select_cols)

    async def fetchall(self, sql: str, params: Iterable[Any] = ()) -> list[tuple]:
        sql = sql.strip()

        (table, select_str, select_cols, filters,
         order_col, order_asc, limit, offset,
         is_count, is_existence) = self._parse_select(sql, list(params))

        if is_count:
            qs = _build_postgrest_params(filters)
            qs["select"] = select_str
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(
                    self._url(table),
                    headers={**self._headers, "Prefer": "count=exact"},
                    params=qs,
                )
            r.raise_for_status()
            count_header = r.headers.get("content-range", "0/0").split("/")[-1]
            try:
                count = int(count_header)
            except ValueError:
                count = 0
            return [(count,)]

        qs = _build_postgrest_params(filters, order_col, order_asc, limit, offset)
        qs["select"] = select_str

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(self._url(table), headers=self._headers, params=qs)
        r.raise_for_status()
        rows = r.json()
        return [tuple(row.get(c) for c in select_cols) for row in rows]

    async def execute(self, sql: str, params: Iterable[Any] = ()) -> None:
        sql_s     = sql.strip()
        params_l  = list(params)

        # UPDATE
        upd = _RE_UPDATE.match(sql_s)
        if upd:
            table, set_part, where_part = upd.group(1), upd.group(2), upd.group(3)
            set_cols   = re.findall(r"(\w+)\s*=\s*\?", set_part)
            set_values = params_l[:len(set_cols)]
            remaining  = params_l[len(set_cols):]
            data       = dict(zip(set_cols, set_values))
            filters, _ = _parse_where_conditions(where_part, remaining)
            qs         = _build_postgrest_params(filters)
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.patch(
                    self._url(table), headers=self._headers,
                    params=qs, json=data,
                )
            r.raise_for_status()
            return

        # DELETE
        dlt = _RE_DELETE.match(sql_s)
        if dlt:
            table, where_part = dlt.group(1), dlt.group(2)
            filters, _ = _parse_where_conditions(where_part, params_l)
            qs         = _build_postgrest_params(filters)
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.delete(
                    self._url(table), headers=self._headers, params=qs,
                )
            r.raise_for_status()
            return

        # Fallthrough to insert
        if re.match(r"INSERT\s+", sql_s, re.IGNORECASE):
            await self.insert(sql_s, params_l)
            return

        raise RuntimeError(f"db_adapter: unsupported SQL in execute(): {sql_s!r}")

    async def insert(self, sql: str, params: Iterable[Any] = ()) -> int:
        sql_s    = sql.strip()
        params_l = list(params)

        m = _RE_INSERT_INTO.match(sql_s)
        if not m:
            raise RuntimeError(f"db_adapter: cannot parse INSERT: {sql_s!r}")

        table   = m.group(1)
        columns = [c.strip() for c in m.group(2).split(",")]
        values  = params_l[:len(columns)]
        data    = dict(zip(columns, values))

        # ON CONFLICT DO NOTHING → upsert with ignoreDuplicates
        on_conflict = "ON CONFLICT" in sql_s.upper()
        headers     = {**self._headers}
        if on_conflict:
            # Deduplicate on 'question' column (FAQ seed only)
            headers["Prefer"] = "return=representation,resolution=ignore-duplicates"

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                self._url(table), headers=headers, json=data,
            )

        # 409 Conflict is OK for upsert-with-ignore
        if on_conflict and r.status_code == 409:
            return 0

        r.raise_for_status()
        result = r.json()
        if isinstance(result, list) and result:
            return result[0].get("id", 0)
        return 0

    async def commit(self) -> None:
        """No-op: PostgREST is auto-commit."""

    async def close(self) -> None:
        """No-op: httpx clients are created per-request."""


# ─────────────────────────────────────────────────────────────────────────────
# Context manager — picks Supabase or SQLite based on env vars
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def get_db():
    """
    Async context manager that yields a database connection wrapper.

    Priority:
      1. SUPABASE_URL + SUPABASE_SERVICE_KEY → SupabaseConnection (HTTPS/PostgREST)
      2. (fallback)                           → SQLiteConnection (local dev)
    """
    settings = get_settings()

    if settings.supabase_url and settings.supabase_service_key:
        wrapper = SupabaseConnection(settings.supabase_url, settings.supabase_service_key)
        yield wrapper
        # No close needed — httpx clients are per-request
    else:
        conn = await aiosqlite.connect(settings.sqlite_path)
        wrapper = SQLiteConnection(conn)
        try:
            yield wrapper
        finally:
            await wrapper.close()
