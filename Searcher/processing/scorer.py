import sys
import os
import nltk
import string, requests
from nltk.stem import PorterStemmer
from datetime import datetime, timezone

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
nltk.download('punkt_tab', quiet=True)

from connectors.gnews_connector import GnewsConnector
from connectors.newsapi_connector import newsAPI_connector
from connectors.rss_connector import RSS_Connector

from config import *

connect = [GnewsConnector(), newsAPI_connector(), RSS_Connector()]
stemmer = PorterStemmer()

def fetch_data(query: str):
    results = []
    for connection in connect:
        results = results + [article for article in connection.fetch_news(query)]
    return results

def handle_keywords(keywords: list):
    words = set()

    for word in keywords:
        words.add(stemmer.stem(word))
    return words

rooted_high = handle_keywords(HIGH_WEIGHT)
rooted_medium = handle_keywords(MEDIUM_WEIGHT)

def clean_text(text: str):
    if text is None:
        return ""
    text = text.translate(str.maketrans('', '', string.punctuation))
    words = text.lower().split()

    clean_words= [stemmer.stem(word) for word in words]
    return clean_words

def keyword_score(articles: list):
    for article in articles:
        text = clean_text(article.title)
        for word in rooted_high:
            if word in text:
                article.score += 10
        for word in rooted_medium:
            if word in text:
                article.score += 5

def source_score(articles: list):
    for article in articles:
        artSrc = article.source
        
        if isinstance(artSrc, tuple):
            raw_str = str(artSrc[-1])
        else:
            raw_str = str(artSrc)
            
        if ":" in raw_str:
            clean_src_str = raw_str.split(":")[-1].lower().strip()
        else:
            clean_src_str = raw_str.lower().strip()

        if any(tier_name in clean_src_str for tier_name in TIER_1):
            article.score += 20
        elif any(tier_name in clean_src_str for tier_name in TIER_2):
            article.score += 15
        elif any(tier_name in clean_src_str for tier_name in TIER_3):
            article.score += 10
            
        article.source = clean_src_str

def age_score(articles: list):
    current_time = datetime.now(timezone.utc)

    for article in articles:
        pub_at = article.published_at
        #to make sure no problem hapen while subtract
        if isinstance(pub_at, str):
            pub_datetime = datetime.fromisoformat(pub_at.replace('Z', '+00:00'))
        else:
            pub_datetime = pub_at

        if pub_datetime.tzinfo is None:
            pub_datetime = pub_datetime.replace(tzinfo= timezone.utc)

        time_diffrence = current_time - pub_datetime
        age_in_hours = time_diffrence.total_seconds() / 3600

        if age_in_hours < 2:
            article.score += 20
        elif age_in_hours < 6:
            article.score += 15
        elif age_in_hours < 12:
            article.score += 10
        elif age_in_hours < 24:
            article.score += 5

        article.published_at = pub_datetime
                        
def thumbnail_validity(url, timeout=1):
    """Fast check using HTTP HEAD to avoid downloading the whole image."""
    if not url:
        return False
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            if 'image' in content_type:
                return True
        return False
    except requests.RequestException:
        return False

def thumbnail_check(articles):
    for article in articles:
        if not thumbnail_validity(article.thumbnail):
            article.score = -1

def score_articles(data: list):
    keyword_score(data)
    source_score(data)
    age_score(data)
    thumbnail_check(data)
    return data


'''
#testing
if __name__ == "__main__":
    articles = scored_articles()

    for article in articles:
        print(article.title)
        print(article.source)
        print(article.published_at)
        print('->', article.score)
        
'''
