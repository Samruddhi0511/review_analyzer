import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).parent.parent / "reviews.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the reviews table if it doesn't exist, and add agent columns
    if they're missing (safe to run on an existing database)."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            review_text     TEXT    NOT NULL,
            sentiment       TEXT    NOT NULL,
            score           INTEGER NOT NULL CHECK(score BETWEEN 1 AND 5),
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            flagged         INTEGER DEFAULT 0,
            urgency         TEXT,
            flag_reason     TEXT,
            draft_response  TEXT,
            response_tone   TEXT
        )
    """)
    conn.commit()

    # Migration: if reviews.db already existed before the agent columns
    # were added, ALTER TABLE to add whichever ones are missing.
    existing_columns = {
        row["name"] for row in conn.execute("PRAGMA table_info(reviews)").fetchall()
    }
    agent_columns = {
        "flagged": "INTEGER DEFAULT 0",
        "urgency": "TEXT",
        "flag_reason": "TEXT",
        "draft_response": "TEXT",
        "response_tone": "TEXT",
    }
    for column, col_type in agent_columns.items():
        if column not in existing_columns:
            conn.execute(f"ALTER TABLE reviews ADD COLUMN {column} {col_type}")
    conn.commit()
    conn.close()


def insert_review(review_text: str, sentiment: str, score: int) -> int:
    """Insert a new review and return its id."""
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO reviews (review_text, sentiment, score) VALUES (?, ?, ?)",
        (review_text, sentiment, score),
    )
    conn.commit()
    review_id = cursor.lastrowid
    conn.close()
    return review_id


def get_all_reviews() -> list[dict]:
    """Return all reviews ordered newest first."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM reviews ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_stats() -> dict:
    """Return aggregate stats across all reviews."""
    conn = get_connection()
    row = conn.execute("""
        SELECT
            COUNT(*)                                             AS total,
            SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) AS positive_count,
            SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) AS negative_count,
            ROUND(AVG(score), 2)                                 AS avg_score
        FROM reviews
    """).fetchone()
    conn.close()
    return dict(row)