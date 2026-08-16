from Searcher.processing.scorer import fetch_data, score_articles
from Searcher.output.serializer import sorted_articles
from database.articles_db import save_articles


def run_pipeline_1(query: str, user_id: int):
    data = fetch_data(query)
    data = score_articles(data)
    # thumbnail_check marks unusable images with -1. Do not offer those articles,
    # even when there are fewer than five otherwise valid results.
    data = [article for article in data if article.score >= 0]
    data = sorted_articles(data)
    save_articles(user_id, data)

if __name__ == "__main__":
    print("Use run_pipeline_1(query, user_id) to store a user's articles.")
