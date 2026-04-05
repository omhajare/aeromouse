"""
Database Initialization Script
Creates all required tables if they don't exist.
Safe to run multiple times (idempotent).
Handles offline/unavailable database gracefully.

Usage:
    python init_db.py
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from backend/.env
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from db import get_connection, is_connected


def create_tables():
    """
    Create all application tables if they don't exist.

    Returns:
        True if tables were created/verified, False if DB is unavailable.
    """
    if not is_connected():
        print("[DB] Database is not available. Skipping table initialization.")
        print("[DB] Cloud features (signatures, auth) will be unavailable.")
        return False

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:

                # ===== USERS TABLE =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(255) UNIQUE NOT NULL,
                        user_id VARCHAR(16) NOT NULL,
                        enrolled_date TIMESTAMP DEFAULT NOW(),
                        features JSONB NOT NULL,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW()
                    );
                """)
                print("[✓] Table 'users' ready")

                # ===== SIGNATURES TABLE =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS signatures (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                        filename VARCHAR(255) NOT NULL,
                        cloudinary_public_id VARCHAR(255),
                        cloudinary_url TEXT,
                        point_count INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT NOW()
                    );
                """)
                print("[✓] Table 'signatures' ready")

                # ===== AUTH THRESHOLDS TABLE =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS auth_thresholds (
                        id SERIAL PRIMARY KEY,
                        dtw_threshold FLOAT DEFAULT 150.0,
                        feature_threshold FLOAT DEFAULT 0.30,
                        min_signature_points INTEGER DEFAULT 20,
                        updated_at TIMESTAMP DEFAULT NOW()
                    );
                """)
                print("[✓] Table 'auth_thresholds' ready")

                # Seed default thresholds if table is empty
                cur.execute("SELECT COUNT(*) FROM auth_thresholds")
                count = cur.fetchone()[0]
                if count == 0:
                    cur.execute("""
                        INSERT INTO auth_thresholds (dtw_threshold, feature_threshold, min_signature_points)
                        VALUES (150.0, 0.30, 20)
                    """)
                    print("[✓] Default thresholds seeded")
                else:
                    print("[✓] Thresholds already configured")

                # Create index on username for fast lookups
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
                """)
                print("[✓] Indexes created")

        print("\n" + "=" * 50)
        print("Database initialization complete!")
        print("=" * 50)
        return True

    except (ConnectionError, Exception) as e:
        print(f"[DB] Could not initialize database: {e}")
        print("[DB] The app will still start, but cloud features may not work.")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("AERO MOUSE — Database Initialization")
    print("=" * 50)

    db_url = os.environ.get('DATABASE_URL', 'NOT SET')
    # Mask password in output
    display_url = db_url
    if '@' in db_url and ':' in db_url:
        try:
            prefix = db_url.split('://')[0]
            rest = db_url.split('://')[1]
            user = rest.split(':')[0]
            after_pass = rest.split('@')[1]
            display_url = f"{prefix}://{user}:****@{after_pass}"
        except (IndexError, ValueError):
            pass
    print(f"\nDatabase: {display_url}\n")

    success = create_tables()
    if not success:
        print("\n[!] Database initialization was not completed.")
        print("    The application can still run for local features.")
        print("\n    To fix, ensure:")
        print("      1. DATABASE_URL is set correctly in backend/.env")
        print("      2. The database server is reachable")
        print("      3. For Supabase: check your project is not paused")
