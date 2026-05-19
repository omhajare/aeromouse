"""
Database Connection Module
Provides SQLite connection management for the application.
Local, zero-configuration database — no network dependency.
"""

import os
import sys
import sqlite3
from contextlib import contextmanager


# ── Determine database file path ────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    # PyInstaller: store DB next to the executable (persistent & writable)
    _DB_DIR = os.path.join(os.path.dirname(sys.executable), 'data')
else:
    # Development: store in project_root/data/
    _DB_DIR = os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
    )

os.makedirs(_DB_DIR, exist_ok=True)
DB_PATH = os.path.join(_DB_DIR, 'aeromouse.db')


# ── Wrappers to keep the same `with conn.cursor() as cur:` interface ────────

class _CursorWrapper:
    """Wraps sqlite3.Cursor to support `with conn.cursor() as cur:` syntax."""

    def __init__(self, cursor):
        self._cur = cursor

    def __enter__(self):
        return self._cur

    def __exit__(self, *args):
        self._cur.close()


class _ConnectionWrapper:
    """Wraps sqlite3.Connection so .cursor() returns a context-manager cursor."""

    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return _CursorWrapper(self._conn.cursor())

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()


# ── Public API (same interface as the old PostgreSQL module) ────────────────

def is_connected():
    """SQLite is always available locally — returns True."""
    return True


@contextmanager
def get_connection():
    """
    Context manager for database connections.

    Usage:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users")
                rows = cur.fetchall()
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    wrapper = _ConnectionWrapper(conn)
    try:
        yield wrapper
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def reset_pool():
    """No-op for SQLite (no connection pool)."""
    pass


def close_pool():
    """No-op for SQLite (no connection pool)."""
    pass
