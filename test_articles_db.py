"""Regression test for per-user article isolation in SQLite storage."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from Searcher.models import NewsItem
import database.articles_db as articles_db


def make_item(user_id: int, number: int) -> NewsItem:
    return NewsItem(
        title=f"User {user_id} article {number}",
        source="Test source",
        url=f"https://example.test/{user_id}/{number}",
        published_at=datetime.now(timezone.utc),
        summary="Test summary",
        thumbnail=None,
        score=float(number),
        category="Test",
    )


class ArticlesDatabaseTest(unittest.TestCase):
    def test_concurrent_users_only_see_their_own_batches(self) -> None:
        original_path = articles_db.DB_PATH
        with tempfile.TemporaryDirectory() as directory:
            articles_db.DB_PATH = Path(directory) / "articles.db"
            try:
                articles_db.init_db()
                user_one, user_two = 101, 202
                batch_one = [make_item(user_one, number) for number in range(1, 6)]
                batch_two = [make_item(user_two, number) for number in range(1, 6)]
                start_writes = Barrier(2)

                def save_batch(user_id: int, batch: list[NewsItem]) -> None:
                    start_writes.wait()
                    articles_db.save_articles(user_id, batch)

                with ThreadPoolExecutor(max_workers=2) as executor:
                    futures = [
                        executor.submit(save_batch, user_one, batch_one),
                        executor.submit(save_batch, user_two, batch_two),
                    ]
                    for future in futures:
                        future.result()

                self.assertEqual(
                    [item.title for item in articles_db.get_articles(user_one)],
                    [item.title for item in batch_one],
                )
                self.assertEqual(
                    [item.title for item in articles_db.get_articles(user_two)],
                    [item.title for item in batch_two],
                )
                self.assertEqual(articles_db.get_article(user_one, 1).title, batch_one[0].title)
                self.assertIsNone(articles_db.get_article(user_one, 6))
            finally:
                articles_db.DB_PATH = original_path


if __name__ == "__main__":
    unittest.main()
