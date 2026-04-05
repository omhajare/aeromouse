"""
Database Connection Module
Provides PostgreSQL connection pooling for the application.
Reads DATABASE_URL from environment variables.
Gracefully handles offline/unavailable database scenarios.
"""

import os
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

DATABASE_URL = os.environ.get('DATABASE_URL')

# Connection pool (min 1, max 10 connections)
_connection_pool = None
_db_available = None  # None = unknown, True = connected, False = unreachable


def _get_pool():
    """Get or create the connection pool (lazy initialization)."""
    global _connection_pool, _db_available

    if not DATABASE_URL:
        _db_available = False
        return None

    if _connection_pool is None:
        try:
            _connection_pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=DATABASE_URL
            )
            _db_available = True
        except psycopg2.OperationalError as e:
            print(
                f"[DB] Could not connect to PostgreSQL database. "
                f"Cloud features will be unavailable. Error: {e}"
            )
            _db_available = False
            return None
    return _connection_pool


def is_connected():
    """Check if the database is reachable. Returns True/False."""
    global _db_available
    if _db_available is not None:
        return _db_available

    p = _get_pool()
    return p is not None


@contextmanager
def get_connection():
    """
    Context manager for database connections.
    Automatically returns connection to pool after use.

    Raises ConnectionError if database is unavailable so callers
    can show a meaningful offline message.

    Usage:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users")
                rows = cur.fetchall()
    """
    p = _get_pool()
    if p is None:
        raise ConnectionError(
            "Database is unavailable. Check your DATABASE_URL or internet connection."
        )

    conn = None
    try:
        conn = p.getconn()
        yield conn
        conn.commit()
    except psycopg2.OperationalError as e:
        global _db_available, _connection_pool
        _db_available = False
        _connection_pool = None  # Force re-init on next attempt
        if conn:
            conn.rollback()
        raise ConnectionError(f"Database connection lost: {e}")
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn and _connection_pool:
            try:
                _connection_pool.putconn(conn)
            except Exception:
                pass


def reset_pool():
    """Reset the connection pool to force re-connection on next use."""
    global _connection_pool, _db_available
    if _connection_pool:
        try:
            _connection_pool.closeall()
        except Exception:
            pass
    _connection_pool = None
    _db_available = None


def close_pool():
    """Close all connections in the pool. Call on app shutdown."""
    global _connection_pool
    if _connection_pool:
        _connection_pool.closeall()
        _connection_pool = None
