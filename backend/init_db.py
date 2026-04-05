"""
Database Initialization Script
Creates all required tables if they don't exist.
Safe to run multiple times (idempotent).

Usage:
    python init_db.py
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from backend/.env
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from db import get_connection


def create_tables():
    """Create all application tables if they don't exist."""

    with get_connection() as conn:
        with conn.cursor() as cur:

            # ===== USERS TABLE =====
            # Stores enrolled signature profiles
            # features is JSONB containing trajectory, velocity, curvature data
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
            # Stores Cloudinary image references for saved signatures
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
            # Single-row config table for authentication thresholds
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

    try:
        create_tables()
    except ConnectionError as e:
        print(f"\n[✗] Connection failed: {e}")
        print("\nMake sure:")
        print("  1. PostgreSQL is running locally")
        print("  2. Database 'aeromouse' exists")
        print("     → Run: CREATE DATABASE aeromouse;")
        print("  3. DATABASE_URL in backend/.env is correct")
        sys.exit(1)
    except Exception as e:
        print(f"\n[✗] Error: {e}")
        sys.exit(1)
