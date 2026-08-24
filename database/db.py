import sqlite3
from datetime import date, timedelta

from werkzeug.security import generate_password_hash

DATABASE = "spendly.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()


def seed_db():
    conn = get_db()
    existing = conn.execute("SELECT 1 FROM users LIMIT 1").fetchone()
    if existing:
        conn.close()
        return

    password_hash = generate_password_hash("demo123")
    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", password_hash),
    )
    user_id = cursor.lastrowid

    today = date.today()
    sample_expenses = [
        (user_id, 12.50, "Food", (today - timedelta(days=1)).isoformat(), "Lunch"),
        (user_id, 45.00, "Transport", (today - timedelta(days=2)).isoformat(), "Fuel"),
        (user_id, 100.00, "Bills", (today - timedelta(days=3)).isoformat(), "Electricity bill"),
        (user_id, 30.00, "Health", (today - timedelta(days=4)).isoformat(), "Pharmacy"),
        (user_id, 20.00, "Entertainment", (today - timedelta(days=5)).isoformat(), "Movie tickets"),
        (user_id, 60.00, "Shopping", (today - timedelta(days=6)).isoformat(), "Clothes"),
        (user_id, 15.00, "Other", (today - timedelta(days=7)).isoformat(), "Misc"),
        (user_id, 8.75, "Food", (today - timedelta(days=8)).isoformat(), "Coffee"),
    ]
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        sample_expenses,
    )
    conn.commit()
    conn.close()
