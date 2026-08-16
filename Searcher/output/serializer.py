def sorted_articles(articles: list) -> list:
    return sorted(articles, key=lambda article: article.score, reverse=True)

if __name__ == '__main__':
    print("Use Searcher.main.run_pipeline_1(query, user_id) to store articles.")
