import requests, os
from models import NewsItem
from config import GNEWS

from dotenv import load_dotenv

load_dotenv()
GNEWS_KEY = os.getenv("GNEWS_KEY")

def get_proxied_image_url(original_url):
    # Route requests through a Cloudflare Worker or allowed image proxy
    return f"https://wsrv.nl/?url={original_url}"

class GnewsConnector:
    def __init__(self):
        self.api_key = GNEWS_KEY
        self.url = GNEWS

    def fetch_news(self, query: str, limit: int = 10):
        params = {
            "q": query,
            "max": limit,
            "lang": "en",
            "apikey": self.api_key,
        }

        try:
            response = requests.get(self.url, params=params, timeout=10)
            response.raise_for_status() #check for errors
            data = response.json()

            return self._parse_results(data.get("articles", []))
        except Exception as e:
            print(f"Error fetching the data {e}")
            return []


    def _parse_results(self, articles: list) -> list[NewsItem]:
        cleanNews = []

        for art in articles:
            item = NewsItem(
                title= art.get("title"),
                url= art.get("url"),
                source= ("Gnews: " + art.get("source", {}).get("name", "Unknown")),
                published_at= art.get("publishedAt"),
                summary= art.get("description"),
                thumbnail= (art.get("image"))
            )
            cleanNews.append(item)

        return cleanNews
