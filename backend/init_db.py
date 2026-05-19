"""
Database Initialization Script
Creates all required SQLite tables if they don't exist.
Safe to run multiple times (idempotent).

Usage:
    python init_db.py
"""

from db import get_connection, DB_PATH


def create_tables():
    """
    Create all application tables if they don't exist.

    Returns:
        True if tables were created/verified.
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:

                # ===== USERS TABLE =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        user_id TEXT NOT NULL,
                        enrolled_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        features TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                print("[OK] Table 'users' ready")

                # ===== SIGNATURES TABLE =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS signatures (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                        filename TEXT NOT NULL,
                        cloudinary_public_id TEXT,
                        cloudinary_url TEXT,
                        point_count INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                print("[OK] Table 'signatures' ready")

                # ===== AUTH THRESHOLDS TABLE =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS auth_thresholds (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        dtw_threshold REAL DEFAULT 150.0,
                        feature_threshold REAL DEFAULT 0.30,
                        min_signature_points INTEGER DEFAULT 20,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                print("[OK] Table 'auth_thresholds' ready")

                # Seed default thresholds if table is empty
                cur.execute("SELECT COUNT(*) FROM auth_thresholds")
                count = cur.fetchone()[0]
                if count == 0:
                    cur.execute("""
                        INSERT INTO auth_thresholds (dtw_threshold, feature_threshold, min_signature_points)
                        VALUES (150.0, 0.30, 20)
                    """)
                    print("[OK] Default thresholds seeded")
                else:
                    print("[OK] Thresholds already configured")

                # Create index on username for fast lookups
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
                """)
                print("[OK] Indexes created")

        print("\n" + "=" * 50)
        print("Database initialization complete!")
        print(f"Database file: {DB_PATH}")
        print("=" * 50)
        return True

    except Exception as e:
        print(f"[DB] Could not initialize database: {e}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("AERO MOUSE — Database Initialization (SQLite)")
    print("=" * 50)
    print(f"\nDatabase: {DB_PATH}\n")

    success = create_tables()
    if not success:
        print("\n[!] Database initialization was not completed.")
