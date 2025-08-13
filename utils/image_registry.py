import os
import sqlite3
from typing import Optional
import hashlib


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
        # Таблица для уже сохранённых локальных файлов (по имени)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS saved_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL UNIQUE,
                file_hash TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
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


def is_file_saved(filename: str) -> bool:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "SELECT 1 FROM saved_files WHERE filename=? LIMIT 1", (filename,)
        )
        return cur.fetchone() is not None


def mark_file_saved(filename: str) -> None:
    _ensure_db()
    # Опционально считаем хэш, чтобы при совпадении содержимого можно анализировать
    file_hash = None
    try:
        with open(filename, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
    except Exception:
        pass
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO saved_files(filename, file_hash) VALUES(?, ?)",
            (filename, file_hash),
        )
        conn.commit()
