"""
SkyFlow Database Layer — SQLite 3
All tables, seed data, and helper functions live here.
"""

import sqlite3
import hashlib
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "skyflow.db")


def get_db():
    """Open a database connection with row-factory so rows behave like dicts."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")   # better concurrency
    return conn


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    """Create all tables and seed default data (idempotent)."""
    conn = get_db()
    c = conn.cursor()

    # ── USERS ──────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            email       TEXT    NOT NULL UNIQUE COLLATE NOCASE,
            password    TEXT    NOT NULL,
            role        TEXT    NOT NULL DEFAULT 'user'  CHECK(role IN ('user','admin')),
            phone       TEXT,
            address     TEXT,
            city        TEXT,
            state       TEXT,
            postal_code TEXT,
            preferred_airline   TEXT DEFAULT 'Air India',
            seat_preference     TEXT DEFAULT 'Window',
            meal_preference     TEXT DEFAULT 'Vegetarian',
            created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ── FLIGHTS ────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS flights (
            id          TEXT    PRIMARY KEY,          -- e.g. 'AI-101'
            airline     TEXT    NOT NULL,
            origin      TEXT    NOT NULL,             -- IATA code
            destination TEXT    NOT NULL,
            departure   TEXT    NOT NULL,             -- 'HH:MM'
            arrival     TEXT    NOT NULL,
            duration    TEXT    NOT NULL,
            total_seats INTEGER NOT NULL DEFAULT 180,
            available_seats INTEGER NOT NULL DEFAULT 180,
            fare        REAL    NOT NULL,
            status      TEXT    NOT NULL DEFAULT 'active' CHECK(status IN ('active','cancelled','full')),
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ── BOOKINGS ───────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id            TEXT    PRIMARY KEY,         -- '#BK12345678'
            user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            flight_id     TEXT    NOT NULL REFERENCES flights(id),
            booking_type  TEXT    NOT NULL DEFAULT 'regular' CHECK(booking_type IN ('regular','emergency','elder')),
            seat_pref     TEXT    DEFAULT 'Window',
            meal_pref     TEXT    DEFAULT 'Vegetarian',
            payment_method TEXT   DEFAULT 'Card',
            fare          REAL    NOT NULL,
            travel_date   TEXT    NOT NULL,
            status        TEXT    NOT NULL DEFAULT 'confirmed' CHECK(status IN ('confirmed','cancelled','pending')),
            passenger_name TEXT,                      -- used for emergency
            emergency_reason TEXT,
            document_path TEXT,
            created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ── REWARDS ────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS rewards (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            points      INTEGER NOT NULL DEFAULT 0,
            reason      TEXT,
            booking_id  TEXT    REFERENCES bookings(id),
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ── SESSIONS (token blacklist for logout) ──────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS revoked_tokens (
            jti         TEXT    PRIMARY KEY,
            revoked_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ── SEED DEFAULT ACCOUNTS ──────────────────────────────────────────────
    default_users = [
        ("AQIB MAJEED",  "user@skyflow.com",  hash_password("password123"), "user"),
        ("Admin",         "admin@skyflow.com", hash_password("admin123"),    "admin"),
    ]
    for name, email, pwd, role in default_users:
        c.execute("""
            INSERT OR IGNORE INTO users (name, email, password, role)
            VALUES (?, ?, ?, ?)
        """, (name, email, pwd, role))

    # ── SEED FLIGHTS ───────────────────────────────────────────────────────
    default_flights = [
        ("AI-101", "Air India",  "DEL", "BOM", "08:00", "10:30", "2h 30m", 180, 45,  2500.0),
        ("SG-205", "SpiceJet",   "DEL", "BOM", "14:15", "17:00", "2h 45m", 180, 32,  1950.0),
        ("6E-302", "IndiGo",     "BLR", "DEL", "19:30", "22:15", "2h 45m", 180, 2,   3100.0),
        ("UK-511", "Vistara",    "HYD", "BOM", "11:00", "12:45", "1h 45m", 180, 115, 2200.0),
        ("AI-202", "Air India",  "BOM", "HYD", "09:30", "11:15", "1h 45m", 180, 60,  2800.0),
        ("SG-310", "SpiceJet",   "MAA", "BLR", "07:00", "08:15", "1h 15m", 180, 78,  1200.0),
        ("6E-401", "IndiGo",     "DEL", "HYD", "16:00", "18:30", "2h 30m", 180, 20,  2650.0),
        ("AI-303", "Air India",  "BOM", "DEL", "06:00", "08:30", "2h 30m", 180, 90,  2750.0),
        ("UK-612", "Vistara",    "BLR", "HYD", "12:30", "13:45", "1h 15m", 180, 55,  1800.0),
        ("SG-420", "SpiceJet",   "HYD", "DEL", "15:00", "17:30", "2h 30m", 180, 40,  2100.0),
    ]
    for row in default_flights:
        c.execute("""
            INSERT OR IGNORE INTO flights
              (id, airline, origin, destination, departure, arrival, duration,
               total_seats, available_seats, fare)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, row)

    conn.commit()
    conn.close()
    print(f"[DB] Initialized → {DB_PATH}")


if __name__ == "__main__":
    init_db()