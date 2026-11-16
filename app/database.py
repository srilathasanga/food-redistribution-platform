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

import psycopg2
from psycopg2 import pool

from app.config import APP_TIMEZONE, get_setting

_pool = None
_pool_lock = threading.Lock()


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
                # Never hand an open transaction to the next user.
                self._conn.rollback()
            except psycopg2.Error:
                broken = True
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
    # so check each one before use and replace it if it went stale.
    for _ in range(3):
        raw_connection = owner_pool.getconn()
        if _is_alive(raw_connection):
            return PooledConnection(raw_connection, owner_pool)
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
