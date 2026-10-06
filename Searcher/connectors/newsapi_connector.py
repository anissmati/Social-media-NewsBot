import requests, os
from config import NEWSAPI, NEWSAPI_KEY
from models import NewsItem

from dotenv import load_dotenv

load_dotenv()
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
def get_proxied_image_url(original_url):
    # Route requests through a Cloudflare Worker or allowed image proxy
    return f"https://wsrv.nl/?url={original_url}"

class newsAPI_connector:
    def __init__(self):
        self.url = NEWSAPI
        self.api_key = NEWSAPI_KEY

    def fetch_news(self, query: str, limit: int = 10):
        params = {
            "q": query,
            "pageSize": limit,
            "language": "en",
            "apikey": self.api_key,
            "sortby": "publishedAt"
        }

        try:
            response = requests.get(self.url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            return self._parse_results(data.get("articles", []))
        except Exception as e:
            print(f"Error fetching data: {e}")
            return []
        
    def _parse_results(self, articles: list) -> list[NewsItem]:
        cleanNews = []

        for art in articles:
            item = NewsItem(
                title= art.get("title"),
                source= ("NewsApi: ", art.get("source", {}).get("name", "NewsApi")),
                url= art.get("url"), 
                published_at= art.get("publishedAt"),
                summary= art.get("description"),
                thumbnail= (art.get("urlToImage")),
            )

            cleanNews.append(item)

        return cleanNews
