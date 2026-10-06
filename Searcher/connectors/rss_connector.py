import feedparser
import requests
from config import RSS
from models import NewsItem

def get_proxied_image_url(original_url):
    # Route requests through a Cloudflare Worker or allowed image proxy
    return f"https://wsrv.nl/?url={original_url}"

class RSS_Connector:
    def __init__(self, feed_url: str = RSS):
        # RSS usually uses a direct URL to the .xml or .rss file
        self.url = feed_url

    def fetch_news(self, limit: int = 10) -> list[NewsItem]:
        try:
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
            feed = feedparser.parse(response.content)
            
            if feed.bozo: # bozo is a flag for malformed XML
                print("Warning: Potential issue with RSS feed format.")

            # RSS feeds usually store items in 'entries'
            return self._parse_results(feed.entries[:limit])
            
        except Exception as e:
            print(f"Error fetching RSS data: {e}")
            return []

    def _parse_results(self, entries: list) -> list[NewsItem]:
        clean_news = []

        for entry in entries:
            # RSS fields vary, so we use .get() or feedparser's attribute dict
            item = NewsItem(
                title=entry.get("title"),
                source=entry.get("author", "RSS Feed"),
                url=entry.get("link"),
                published_at=entry.get("published"),
                # RSS often uses 'summary' or 'description'
                summary=entry.get("summary") or entry.get("description"),
                # Images are tricky in RSS; they are usually in 'links' or 'media_content'
                thumbnail=(self._extract_image(entry))
            )
            clean_news.append(item)

        return clean_news

    def _extract_image(self, entry):
        """Helper to find thumbnails in common RSS media tags"""
        if "links" in entry:
            for link in entry.links:
                if "image" in link.get("type", ""):
                    return link.get("href")
        return None
