"""
Database adapter — Supabase (supabase-py via HTTPS) + SQLite (aiosqlite).

Backend selection:
  - SUPABASE_URL + SUPABASE_SERVICE_KEY set → supabase-py async client (HTTPS/REST)
  - Neither set                             → aiosqlite (local development only)

Why supabase-py instead of psycopg2 / asyncpg?
  Render's free tier cannot make outbound TCP connections on port 5432 to
  Supabase's IPv6-only host. supabase-py talks over HTTPS (port 443) via the
  PostgREST REST API, which works on any host that can reach the internet.

Interface contract (both wrappers implement the same methods):
  fetchone(sql, params) → Optional[tuple]
  fetchall(sql, params) → list[tuple]
  execute(sql, params)  → None          (UPDATE / DELETE / etc.)
  insert(sql, params)   → int           (returns new row id)
  commit()              → None          (no-op for Supabase — auto-commit via REST)
  close()               → None
"""
from __future__ import annotations

import re
import logging
from contextlib import asynccontextmanager
from typing import Any, Iterable, Optional

import aiosqlite

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
#
# supabase-py exposes a query-builder (PostgREST) rather than raw SQL.
# We only need to support the specific queries used in this codebase, so we
# parse each statement by pattern rather than building a full SQL parser.
# ─────────────────────────────────────────────────────────────────────────────

# Regex helpers (case-insensitive, compiled once at import time)
_RE_SELECT_FROM  = re.compile(
    r"SELECT\s+(.+?)\s+FROM\s+(\w+)(.*)",
    re.IGNORECASE | re.DOTALL,
)
_RE_INSERT_INTO  = re.compile(
    r"INSERT\s+INTO\s+(\w+)\s*\(([^)]+)\)\s*VALUES\s*\(([^)]+)\)",
    re.IGNORECASE,
)
_RE_UPDATE       = re.compile(
    r"UPDATE\s+(\w+)\s+SET\s+(.+?)\s+WHERE\s+(.+)",
    re.IGNORECASE | re.DOTALL,
)
_RE_DELETE       = re.compile(
    r"DELETE\s+FROM\s+(\w+)\s+WHERE\s+(.+)",
    re.IGNORECASE | re.DOTALL,
)
_RE_COUNT        = re.compile(r"COUNT\s*\(\s*\*\s*\)", re.IGNORECASE)
_RE_WHERE        = re.compile(r"\bWHERE\b\s*(.+?)(?:\s+ORDER BY|\s+LIMIT|\s+OFFSET|$)",
                               re.IGNORECASE | re.DOTALL)
_RE_ORDER        = re.compile(r"ORDER\s+BY\s+(\S+)(?:\s+(ASC|DESC))?", re.IGNORECASE)
_RE_LIMIT        = re.compile(r"LIMIT\s+\?", re.IGNORECASE)
_RE_OFFSET       = re.compile(r"OFFSET\s+\?", re.IGNORECASE)


def _substitute_placeholders(text: str, params: list) -> tuple[str, list]:
    """
    Replace the first `?` in *text* with each successive value from *params*.
    Returns (text_with_no_more_placeholders, remaining_params).
    This lets callers process tokens one-by-one.
    """
    remaining = list(params)
    result = text
    while "?" in result and remaining:
        result = result.replace("?", str(remaining.pop(0)), 1)
    return result, remaining


def _parse_where_conditions(
    where_clause: str,
    params: list,
) -> tuple[dict[str, Any], list]:
    """
    Very narrowly parse the WHERE clauses actually used in this app into a
    dict of PostgREST filter kwargs understood by supabase-py's .filter() or
    column-named eq/gte/lte helpers.

    Returns (filters_dict, remaining_params) where filters_dict maps the
    PostgREST filter string (e.g. "clinician,eq,Smith") to None (just a list
    that we apply in order).

    Actually returns a list of (column, operator, value) triples to be applied
    as successive .filter() calls on the supabase query builder.
    """
    # Normalise whitespace
    clause = where_clause.strip()
    remaining = list(params)
    filters: list[tuple[str, str, Any]] = []

    # Split on AND (simple — no nested parens / OR in our queries)
    # We handle the complex NOT (...) pattern for conflict checks specially.
    parts = re.split(r"\bAND\b", clause, flags=re.IGNORECASE)

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Handle: NOT (ends_at <= ? OR starts_at >= ?)
        # PostgREST equivalent: starts_at < ? AND ends_at > ?
        not_match = re.match(
            r"NOT\s*\(\s*ends_at\s*<=\s*\?\s+OR\s+starts_at\s*>=\s*\?\s*\)",
            part, re.IGNORECASE,
        )
        if not_match:
            # Consumes two params: first is ends_at bound, second is starts_at bound
            val_ends = remaining.pop(0) if remaining else None
            val_starts = remaining.pop(0) if remaining else None
            # NOT (ends_at <= X OR starts_at >= Y)
            #  ≡  ends_at > X AND starts_at < Y
            filters.append(("ends_at", "gt", val_ends))
            filters.append(("starts_at", "lt", val_starts))
            continue

        # Standard equality / comparison: col op ?
        cmp_match = re.match(
            r"([\w.]+)\s*(=|!=|<>|>=|<=|>|<|LIKE|ILIKE)\s*\?",
            part, re.IGNORECASE,
        )
        if cmp_match:
            col = cmp_match.group(1)
            op_raw = cmp_match.group(2).upper()
            val = remaining.pop(0) if remaining else None
            op_map = {
                "=":    "eq",
                "!=":   "neq",
                "<>":   "neq",
                ">":    "gt",
                ">=":   "gte",
                "<":    "lt",
                "<=":   "lte",
                "LIKE": "like",
                "ILIKE":"ilike",
            }
            filters.append((col, op_map.get(op_raw, "eq"), val))
            continue

        # id <> ? (exclusion used in update conflict check)
        neq_match = re.match(r"([\w.]+)\s*<>\s*\?", part, re.IGNORECASE)
        if neq_match:
            col = neq_match.group(1)
            val = remaining.pop(0) if remaining else None
            filters.append((col, "neq", val))
            continue

        # (question LIKE ? OR answer LIKE ?) — FAQ search
        or_like_match = re.match(
            r"\(\s*([\w.]+)\s+LIKE\s+\?\s+OR\s+([\w.]+)\s+LIKE\s+\?\s*\)",
            part, re.IGNORECASE,
        )
        if or_like_match:
            col1 = or_like_match.group(1)
            col2 = or_like_match.group(2)
            val1 = remaining.pop(0) if remaining else None
            val2 = remaining.pop(0) if remaining else None
            # PostgREST: use `or` filter.  We encode as a special marker.
            filters.append(("__or__", f"{col1}.like.{val1},{col2}.like.{val2}", None))
            continue

        # SELECT 1 pseudo-condition produced by health check — skip
        logger.debug("db_adapter: unrecognised WHERE part, skipping: %r", part)

    return filters, remaining


def _apply_filters(query, filters: list[tuple[str, str, Any]]):
    """Apply a list of (col, op, val) triples to a supabase-py query builder."""
    for col, op, val in filters:
        if col == "__or__":
            # val is the full PostgREST or-string, e.g. "question.like.%x%,answer.like.%x%"
            query = query.or_(op)
        else:
            query = query.filter(col, op, val)
    return query


# ─────────────────────────────────────────────────────────────────────────────
# Supabase wrapper (production)
# ─────────────────────────────────────────────────────────────────────────────

# Column order for each table — used to convert dicts back to tuples so that
# the routes (which index rows by position) keep working unchanged.
_TABLE_COLUMNS: dict[str, list[str]] = {
    "users":        ["id", "email", "password_hash", "role", "created_at"],
    "appointments": ["id", "patient_name", "clinician", "department",
                     "starts_at", "ends_at", "reason", "created_at"],
    "faq":          ["id", "question", "answer"],
}

# Columns actually SELECTed by each query pattern (derived from the SQL).
# When the SQL specifies explicit columns we project only those; otherwise we
# use the full table column list.

def _dict_to_tuple(row: dict, columns: list[str]) -> tuple:
    """Convert a PostgREST response dict to a positional tuple."""
    return tuple(row.get(col) for col in columns)


def _rows_to_tuples(rows: list[dict], columns: list[str]) -> list[tuple]:
    return [_dict_to_tuple(r, columns) for r in rows]


class SupabaseConnection:
    """
    Translates the generic SQL-like interface into supabase-py PostgREST calls.

    Only the query patterns actually used in this application are supported.
    For anything unknown the method raises RuntimeError with the offending SQL
    so it's easy to add support later.
    """

    def __init__(self, client):
        # client is a supabase AsyncClient
        self._sb = client

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_select(self, sql: str, params: list):
        """
        Return (table, select_columns, filters, order_col, order_dir, limit, offset)
        from a SELECT statement.
        """
        m = _RE_SELECT_FROM.match(sql.strip())
        if not m:
            raise RuntimeError(f"db_adapter: cannot parse SELECT: {sql!r}")

        raw_cols = m.group(1).strip()   # e.g. "id, question, answer" or "COUNT(*)" or "1"
        table    = m.group(2).strip()
        rest     = m.group(3).strip()   # everything after table name

        # Resolve SELECT columns into a list (what PostgREST will return)
        if _RE_COUNT.search(raw_cols):
            select_cols = ["count"]   # PostgREST returns {"count": N}
        elif raw_cols == "1":
            # Health check / existence check: SELECT 1 FROM table WHERE ...
            select_cols = ["id"]      # just fetch id; we'll return (1,) manually
        else:
            select_cols = [c.strip() for c in raw_cols.split(",")]

        # Parse WHERE clause
        where_match = _RE_WHERE.search(rest)
        filters = []
        remaining_params = list(params)
        if where_match:
            filters, remaining_params = _parse_where_conditions(
                where_match.group(1), remaining_params
            )

        # Parse ORDER BY
        order_col = None
        order_asc = True
        order_match = _RE_ORDER.search(rest)
        if order_match:
            order_col = order_match.group(1)
            order_asc = (order_match.group(2) or "ASC").upper() == "ASC"

        # Parse LIMIT / OFFSET — they consume remaining params in order
        limit  = None
        offset = None
        if _RE_LIMIT.search(rest) and remaining_params:
            limit = int(remaining_params.pop(0))
        if _RE_OFFSET.search(rest) and remaining_params:
            offset = int(remaining_params.pop(0))

        return table, select_cols, filters, order_col, order_asc, limit, offset

    def _build_select_query(self, sql: str, params: list):
        """
        Build a supabase-py async query for a SELECT statement.
        Returns (query_builder, result_columns, is_count, is_existence_check).
        """
        table, select_cols, filters, order_col, order_asc, limit, offset = \
            self._parse_select(sql, params)

        is_count      = select_cols == ["count"]
        is_existence  = select_cols == ["id"] and "1" in sql.split("FROM")[0]

        if is_count:
            # PostgREST count via head=True is the idiomatic approach but
            # supabase-py also supports .select("*", count="exact") and then
            # reading response.count.  We use the latter.
            query = self._sb.table(table).select("*", count="exact")
        elif is_existence:
            query = self._sb.table(table).select("id").limit(1)
        else:
            query = self._sb.table(table).select(",".join(select_cols))

        query = _apply_filters(query, filters)

        if order_col:
            query = query.order(order_col, desc=not order_asc)
        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)

        return query, select_cols, is_count, is_existence

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def fetchone(self, sql: str, params: Iterable[Any] = ()) -> Optional[tuple]:
        sql = sql.strip()
        params_list = list(params)

        # Special-case: "SELECT 1" (health check — no table)
        if re.match(r"SELECT\s+1\s*$", sql, re.IGNORECASE):
            return (1,)

        query, select_cols, is_count, is_existence = \
            self._build_select_query(sql, params_list)

        if is_count:
            resp = await query.execute()
            count = resp.count if resp.count is not None else (len(resp.data) if resp.data else 0)
            return (count,)

        resp = await query.limit(1).execute()

        if not resp.data:
            return None

        row_dict = resp.data[0]

        if is_existence:
            return (1,)

        # Determine canonical column list for the table
        table_m = _RE_SELECT_FROM.match(sql)
        table_name = table_m.group(2) if table_m else ""
        col_order = select_cols if select_cols != ["id"] else \
                    _TABLE_COLUMNS.get(table_name, list(row_dict.keys()))

        return _dict_to_tuple(row_dict, col_order)

    async def fetchall(self, sql: str, params: Iterable[Any] = ()) -> list[tuple]:
        sql = sql.strip()
        params_list = list(params)

        query, select_cols, is_count, is_existence = \
            self._build_select_query(sql, params_list)

        if is_count:
            resp = await query.execute()
            count = resp.count if resp.count is not None else 0
            return [(count,)]

        resp = await query.execute()

        if not resp.data:
            return []

        return _rows_to_tuples(resp.data, select_cols)

    async def execute(self, sql: str, params: Iterable[Any] = ()) -> None:
        """Handle UPDATE and DELETE statements."""
        sql_s = sql.strip()
        params_list = list(params)

        # ---- UPDATE ----
        upd = _RE_UPDATE.match(sql_s)
        if upd:
            table     = upd.group(1)
            set_part  = upd.group(2)
            where_part = upd.group(3).strip()

            # Parse SET clause: "col = ?, col2 = ?, ..."
            set_pairs = re.findall(r"(\w+)\s*=\s*\?", set_part)
            set_values = params_list[:len(set_pairs)]
            remaining  = params_list[len(set_pairs):]
            data_dict  = dict(zip(set_pairs, set_values))

            filters, _ = _parse_where_conditions(where_part, remaining)
            query = self._sb.table(table).update(data_dict)
            query = _apply_filters(query, filters)
            await query.execute()
            return

        # ---- DELETE ----
        dlt = _RE_DELETE.match(sql_s)
        if dlt:
            table      = dlt.group(1)
            where_part = dlt.group(2).strip()
            filters, _ = _parse_where_conditions(where_part, params_list)
            query = self._sb.table(table).delete()
            query = _apply_filters(query, filters)
            await query.execute()
            return

        # ---- INSERT (called via execute, not insert) ----
        if re.match(r"INSERT\s+INTO", sql_s, re.IGNORECASE):
            await self.insert(sql_s, params_list)
            return

        raise RuntimeError(f"db_adapter: unsupported SQL in execute(): {sql_s!r}")

    async def insert(self, sql: str, params: Iterable[Any] = ()) -> int:
        """
        Execute an INSERT and return the new row's id.

        PostgREST inserts return the full inserted row (with `upsert` or plain
        `.insert(data)`).  We ask for `returning="representation"` (the default
        in supabase-py) so we can read back the generated primary key.
        """
        sql_s = sql.strip()
        params_list = list(params)

        m = _RE_INSERT_INTO.match(sql_s)
        if not m:
            raise RuntimeError(f"db_adapter: cannot parse INSERT: {sql_s!r}")

        table   = m.group(1)
        columns = [c.strip() for c in m.group(2).split(",")]
        # number of placeholders in VALUES clause == len(columns)
        values  = params_list[:len(columns)]
        data    = dict(zip(columns, values))

        resp = await self._sb.table(table).insert(data).execute()

        if resp.data:
            return resp.data[0].get("id", 0)
        return 0

    async def commit(self) -> None:
        """No-op: Supabase REST API is auto-commit (each request is a transaction)."""

    async def close(self) -> None:
        """No-op: the async client manages its own HTTP session lifecycle."""


# ─────────────────────────────────────────────────────────────────────────────
# Context manager — picks Supabase or SQLite based on env vars
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def get_db():
    """
    Async context manager that yields a database connection wrapper.

    Priority:
      1. SUPABASE_URL + SUPABASE_SERVICE_KEY → SupabaseConnection (HTTPS)
      2. (fallback)                           → SQLiteConnection (local dev)
    """
    settings = get_settings()

    if settings.supabase_url and settings.supabase_service_key:
        # --- Supabase path ---
        try:
            from supabase import acreate_client, AsyncClientOptions  # supabase-py 2.x
        except ImportError:
            raise RuntimeError(
                "supabase package not installed. "
                "Run: pip install 'supabase==2.15.2'"
            )

        client = await acreate_client(
            settings.supabase_url,
            settings.supabase_service_key,
            options=AsyncClientOptions(
                postgrest_client_timeout=30,
                storage_client_timeout=30,
            ),
        )
        wrapper = SupabaseConnection(client)
        try:
            yield wrapper
        finally:
            # supabase-py async client: close the underlying httpx session
            try:
                await client.auth.close()
            except Exception:
                pass
    else:
        # --- SQLite fallback path ---
        conn = await aiosqlite.connect(settings.sqlite_path)
        wrapper = SQLiteConnection(conn)
        try:
            yield wrapper
        finally:
            await wrapper.close()
