import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Searcher.models import NewsItem
from content.content_generator import generate_summary, generate_title
from content.post_generator import create_post
from database.articles_db import get_article
from database.user_service import get_user_settings


def run_pipeline_2(slot: int, user_id: int, article: NewsItem | None = None) -> None:
    """Generate a post from one article owned by ``user_id``."""
    settings = get_user_settings(user_id)
    article = article or get_article(user_id, slot)
    if article is None:
        raise ValueError(f"No article in slot {slot} for user {user_id}")

    article_data = {
        "title": article.title,
        "source": article.source,
        "url": article.url,
        "published_at": article.published_at.isoformat(),
        "summary": article.summary,
        "thumbnail": article.thumbnail,
        "score": article.score,
        "category": article.category,
    }
    final_title = generate_title(article_data, settings)
    final_summary = generate_summary(article_data, settings)

    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    summary_path = Path("output") / now / "description.txt"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as file:
        file.write(final_summary)

    article_data["title"] = final_title
    image = create_post(article_data, settings)
    image.save(summary_path.parent / "post.jpg")


if __name__ == "__main__":
    print("Use run_pipeline_2(slot, user_id) after fetching articles.")
