import sqlite3
from pathlib import Path

# DB lives at project root
DB_PATH = Path(__file__).parent.parent / "reviews.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the reviews table if it doesn't exist."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            review_text TEXT    NOT NULL,
            sentiment   TEXT    NOT NULL,
            score       INTEGER NOT NULL CHECK(score BETWEEN 1 AND 5),
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
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
