"""Database connections.

Configure ONE of these (environment variables, .env, or Streamlit secrets):

  DATABASE_URL = "postgresql://user:password@host/dbname?sslmode=require"
      (the connection string Neon shows; use its "pooled" variant)

  or the older separate settings:
  DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

Connections are reused from a small pool instead of opening a new one for
every query. Service code keeps calling get_connection() and
connection.close() exactly as before; close() simply hands the
connection back to the pool.
"""

import threading
import time

import psycopg2
from psycopg2 import pool
from psycopg2.extensions import TRANSACTION_STATUS_IDLE

from app.config import APP_TIMEZONE, get_setting

_pool = None
_pool_lock = threading.Lock()

# Each check costs a round trip to the database (about 0.26 s from India to
# Neon in the US), so a connection is only checked when it has been idle
# long enough that Neon may have closed it.
CHECK_IF_IDLE_SECONDS = 30
_last_used = {}  # id(raw connection) -> time it was last handed back


def _connect_kwargs():
    options = f"-c timezone={APP_TIMEZONE}"
    url = get_setting("DATABASE_URL")
    if url:
        return {"dsn": url, "options": options}

    return {
        "host": get_setting("DB_HOST", "localhost"),
        "port": get_setting("DB_PORT", "5432"),
        "database": get_setting("DB_NAME"),
        "user": get_setting("DB_USER"),
        "password": get_setting("DB_PASSWORD"),
        "options": options,
    }


def is_configured():
    """True if any database setting exists (it may still be wrong)."""
    return bool(get_setting("DATABASE_URL") or get_setting("DB_NAME"))


def _get_pool():
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                _pool = pool.ThreadedConnectionPool(
                    minconn=1,
                    maxconn=int(get_setting("DB_POOL_SIZE", "10")),
                    connect_timeout=15,
                    **_connect_kwargs(),
                )
    return _pool


class PooledConnection:
    """Acts like a psycopg2 connection; close() returns it to the pool."""

    def __init__(self, raw_connection, owner_pool):
        self._conn = raw_connection
        self._pool = owner_pool
        self._returned = False

    def __getattr__(self, name):
        return getattr(self._conn, name)

    def close(self):
        if self._returned:
            return
        self._returned = True
        broken = bool(self._conn.closed)
        if not broken:
            try:
                # Never hand an open transaction to the next user. (After a
                # commit there is none, so skip the extra round trip.)
                if (self._conn.info.transaction_status
                        != TRANSACTION_STATUS_IDLE):
                    self._conn.rollback()
            except psycopg2.Error:
                broken = True
        if broken:
            _last_used.pop(id(self._conn), None)
        else:
            _last_used[id(self._conn)] = time.monotonic()
        self._pool.putconn(self._conn, close=broken)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def _is_alive(raw_connection):
    if raw_connection.closed:
        return False
    try:
        with raw_connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        raw_connection.rollback()
        return True
    except psycopg2.Error:
        return False


def get_connection():
    owner_pool = _get_pool()

    # A serverless database (Neon) drops idle connections when it sleeps,
    # so check a connection before use if it has been idle for a while (or
    # is new to us), and replace it if it went stale.
    for _ in range(3):
        raw_connection = owner_pool.getconn()
        last_used = _last_used.get(id(raw_connection))
        recently_used = (last_used is not None and time.monotonic() - last_used
                         < CHECK_IF_IDLE_SECONDS)
        if not raw_connection.closed and (recently_used
                                          or _is_alive(raw_connection)):
            return PooledConnection(raw_connection, owner_pool)
        _last_used.pop(id(raw_connection), None)
        owner_pool.putconn(raw_connection, close=True)

    raise psycopg2.OperationalError(
        "Could not get a working database connection."
    )


def reset_pool():
    """Close every pooled connection (used by tests)."""
    global _pool
    with _pool_lock:
        if _pool is not None:
            _pool.closeall()
            _pool = None
        _last_used.clear()
