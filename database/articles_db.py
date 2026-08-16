"""Per-user storage for the articles offered by the Telegram bot."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
import sqlite3
from typing import Iterator, Optional

from Searcher.models import NewsItem


DB_PATH = Path(__file__).resolve().parent / "database.db"


@contextmanager
def _connection() -> Iterator[sqlite3.Connection]:
    """Yield a connection that commits on success and rolls back on failure."""
    connection = sqlite3.connect(DB_PATH, timeout=30)
    try:
        connection.execute("PRAGMA journal_mode=WAL")
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db() -> None:
    """Create the table used to store each user's current article batch."""
    with _connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS articles (
                user_id INTEGER NOT NULL,
                slot INTEGER NOT NULL,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                url TEXT NOT NULL,
                published_at TEXT NOT NULL,
                summary TEXT,
                thumbnail TEXT,
                score REAL NOT NULL,
                category TEXT NOT NULL,
                PRIMARY KEY (user_id, slot)
            )
            """
        )


def save_articles(user_id: int, items: list[NewsItem]) -> None:
    """Atomically replace only ``user_id``'s articles with up to five new slots."""
    rows = [
        (
            user_id,
            slot,
            item.title,
            item.source,
            item.url,
            item.published_at.isoformat(),
            item.summary,
            item.thumbnail,
            item.score,
            item.category,
        )
        for slot, item in enumerate(items[:5], start=1)
    ]

    with _connection() as connection:
        connection.execute("DELETE FROM articles WHERE user_id = ?", (user_id,))
        connection.executemany(
            """
            INSERT INTO articles (
                user_id, slot, title, source, url, published_at, summary,
                thumbnail, score, category
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )


def _to_news_item(row: sqlite3.Row) -> NewsItem:
    return NewsItem(
        title=row["title"],
        source=row["source"],
        url=row["url"],
        published_at=datetime.fromisoformat(row["published_at"]),
        summary=row["summary"],
        thumbnail=row["thumbnail"],
        score=row["score"],
        category=row["category"],
    )


def get_articles(user_id: int) -> list[NewsItem]:
    """Return the user's current articles in presentation-slot order."""
    with _connection() as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT * FROM articles WHERE user_id = ? ORDER BY slot", (user_id,)
        ).fetchall()
    return [_to_news_item(row) for row in rows]


def get_article(user_id: int, slot: int) -> Optional[NewsItem]:
    """Return one article from the user's current batch, if it exists."""
    with _connection() as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT * FROM articles WHERE user_id = ? AND slot = ?", (user_id, slot)
        ).fetchone()
    return _to_news_item(row) if row is not None else None


def clear_articles(user_id: int) -> None:
    """Remove a user's current article batch without affecting other users."""
    with _connection() as connection:
        connection.execute("DELETE FROM articles WHERE user_id = ?", (user_id,))
