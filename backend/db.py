"""
Database Connection Module
Provides PostgreSQL connection pooling for the application.
Reads DATABASE_URL from environment variables.
"""

import os
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable is not set. "
        "Please set it in backend/.env file. "
        "Example: postgresql://postgres:password@localhost:5432/aeromouse"
    )

# Connection pool (min 1, max 10 connections)
_connection_pool = None


def _get_pool():
    """Get or create the connection pool (lazy initialization)."""
    global _connection_pool
    if _connection_pool is None:
        try:
            _connection_pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=DATABASE_URL
            )
        except psycopg2.OperationalError as e:
            raise ConnectionError(
                f"Could not connect to PostgreSQL database. "
                f"Check your DATABASE_URL in backend/.env. Error: {e}"
            )
    return _connection_pool


@contextmanager
def get_connection():
    """
    Context manager for database connections.
    Automatically returns connection to pool after use.

    Usage:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users")
                rows = cur.fetchall()
    """
    conn = None
    try:
        conn = _get_pool().getconn()
        yield conn
        conn.commit()
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            _get_pool().putconn(conn)


def close_pool():
    """Close all connections in the pool. Call on app shutdown."""
    global _connection_pool
    if _connection_pool:
        _connection_pool.closeall()
        _connection_pool = None
