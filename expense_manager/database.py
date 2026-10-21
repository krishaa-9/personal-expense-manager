"""SQLite persistence layer."""
import sqlite3
from pathlib import Path

DEFAULT_DB = Path.home() / ".expense_manager" / "expenses.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS expenses (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
    category     TEXT    NOT NULL,
    description  TEXT    NOT NULL DEFAULT '',
    date         TEXT    NOT NULL,              -- ISO format YYYY-MM-DD
    created_at   TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date);
CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category);

CREATE TABLE IF NOT EXISTS budgets (
    category            TEXT PRIMARY KEY,
    monthly_limit_cents INTEGER NOT NULL CHECK (monthly_limit_cents > 0)
);
"""


def connect(path=None):
    """Open (and initialise) the database. Pass ':memory:' for tests."""
    path = str(path) if path is not None else str(DEFAULT_DB)
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn
