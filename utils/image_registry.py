import os
import sqlite3
from typing import Optional


DB_PATH = os.path.join("data", "processed.db")


def _ensure_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS used_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                image_id TEXT NOT NULL,
                image_url TEXT,
                query TEXT,
                used_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(provider, image_id)
            );
            """
        )
        conn.commit()


def is_used(provider: str, image_id: str) -> bool:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            (
                "SELECT 1 FROM used_images "
                "WHERE provider=? AND image_id=? LIMIT 1"
            ),
            (provider, image_id),
        )
        return cur.fetchone() is not None


def mark_used(
    provider: str,
    image_id: str,
    image_url: Optional[str],
    query: Optional[str],
) -> None:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            (
                "INSERT OR IGNORE INTO used_images("
                "provider, image_id, image_url, query) VALUES(?, ?, ?, ?)"
            ),
            (provider, image_id, image_url, query),
        )
        conn.commit()
