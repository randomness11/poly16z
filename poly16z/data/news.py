"""
News Collector

Collects and processes news from various sources.
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import aiohttp
import feedparser
from bs4 import BeautifulSoup
from loguru import logger
from pydantic import BaseModel


class NewsArticle(BaseModel):
    """Represents a news article."""

    title: str
    url: str
    source: str
    published: datetime
    summary: Optional[str] = None
    content: Optional[str] = None
    keywords: List[str] = []
    sentiment: float = 0.0  # -1 to 1


class NewsCollector:
    """
    Collects news from various sources.

    Supports:
    - RSS feeds (AP, Reuters, BBC, etc.)
    - News APIs (NewsAPI, etc.)
    - Custom scrapers
    """

    def __init__(
        self,
        news_api_key: Optional[str] = None,
        sources: Optional[List[str]] = None,
    ):
        """
        Initialize news collector.

        Args:
            news_api_key: NewsAPI key (optional)
            sources: List of RSS feed URLs or source names
        """
        self.news_api_key = news_api_key
        self.sources = sources or [
            "http://feeds.bbci.co.uk/news/rss.xml",
            "http://rss.cnn.com/rss/cnn_topstories.rss",
            "https://feeds.reuters.com/reuters/topNews",
        ]

        self.articles_cache: List[NewsArticle] = []

    async def fetch_rss(self, feed_url: str) -> List[NewsArticle]:
        """
        Fetch articles from an RSS feed.

        Args:
            feed_url: RSS feed URL

        Returns:
            List of NewsArticle objects
        """
        try:
            logger.debug(f"Fetching RSS feed: {feed_url}")

            # Parse feed
            feed = await asyncio.to_thread(feedparser.parse, feed_url)

            articles = []
            for entry in feed.entries[:10]:  # Limit to 10 most recent
                # Parse published date
                published = datetime.now()
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6])

                article = NewsArticle(
                    title=entry.get("title", ""),
                    url=entry.get("link", ""),
                    source=feed.feed.get("title", "Unknown"),
                    published=published,
                    summary=entry.get("summary", ""),
                )
                articles.append(article)

            logger.info(f"Fetched {len(articles)} articles from {feed_url}")
            return articles

        except Exception as e:
            logger.error(f"Error fetching RSS feed {feed_url}: {e}")
            return []

    async def fetch_newsapi(
        self,
        query: Optional[str] = None,
        hours: int = 24,
    ) -> List[NewsArticle]:
        """
        Fetch articles from NewsAPI.

        Args:
            query: Search query
            hours: Hours to look back

        Returns:
            List of NewsArticle objects
        """
        if not self.news_api_key:
            logger.warning("NewsAPI key not provided")
            return []

        try:
            from_date = (datetime.now() - timedelta(hours=hours)).isoformat()

            url = "https://newsapi.org/v2/everything"
            params = {
                "apiKey": self.news_api_key,
                "from": from_date,
                "sortBy": "publishedAt",
                "language": "en",
                "pageSize": 20,
            }

            if query:
                params["q"] = query

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    data = await response.json()

                    articles = []
                    for item in data.get("articles", []):
                        article = NewsArticle(
                            title=item.get("title", ""),
                            url=item.get("url", ""),
                            source=item.get("source", {}).get("name", "Unknown"),
                            published=datetime.fromisoformat(
                                item.get("publishedAt", "").replace("Z", "+00:00")
                            ),
                            summary=item.get("description", ""),
                            content=item.get("content", ""),
                        )
                        articles.append(article)

                    logger.info(f"Fetched {len(articles)} articles from NewsAPI")
                    return articles

        except Exception as e:
            logger.error(f"Error fetching from NewsAPI: {e}")
            return []

    async def collect(
        self,
        query: Optional[str] = None,
        hours: int = 24,
    ) -> List[NewsArticle]:
        """
        Collect news from all sources.

        Args:
            query: Optional search query
            hours: Hours to look back

        Returns:
            List of all collected articles
        """
        logger.info("Collecting news from all sources...")

        tasks = []

        # Fetch from RSS feeds
        for source in self.sources:
            tasks.append(self.fetch_rss(source))

        # Fetch from NewsAPI if available
        if self.news_api_key:
            tasks.append(self.fetch_newsapi(query, hours))

        # Gather all results
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten and filter
        all_articles = []
        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)

        # Remove duplicates by URL
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            if article.url not in seen_urls:
                seen_urls.add(article.url)
                unique_articles.append(article)

        # Sort by published date
        unique_articles.sort(key=lambda x: x.published, reverse=True)

        # Update cache
        self.articles_cache = unique_articles[:100]  # Keep last 100

        logger.info(f"Collected {len(unique_articles)} unique articles")
        return unique_articles

    def search(
        self,
        keywords: List[str],
        hours: int = 24,
    ) -> List[NewsArticle]:
        """
        Search cached articles for keywords.

        Args:
            keywords: Keywords to search for
            hours: Hours to look back

        Returns:
            Matching articles
        """
        cutoff = datetime.now() - timedelta(hours=hours)

        matching = []
        for article in self.articles_cache:
            if article.published < cutoff:
                continue

            # Check if any keyword appears in title or summary
            text = f"{article.title} {article.summary}".lower()
            if any(keyword.lower() in text for keyword in keywords):
                matching.append(article)

        logger.info(f"Found {len(matching)} articles matching keywords: {keywords}")
        return matching
