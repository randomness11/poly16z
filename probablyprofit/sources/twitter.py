"""
Twitter/X Data Source

Real-time social sentiment and breaking news from Twitter/X.
Supports both official API and scraping fallback.
"""

import asyncio
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger
from pydantic import BaseModel


class Tweet(BaseModel):
    """A single tweet."""

    id: str
    text: str
    author: str
    author_followers: int = 0
    created_at: datetime
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    url: Optional[str] = None

    @property
    def engagement(self) -> int:
        """Total engagement score."""
        return self.likes + self.retweets * 2 + self.replies

    @property
    def influence_score(self) -> float:
        """Score based on author reach and engagement."""
        # Log scale for followers to not over-weight mega accounts
        import math

        follower_score = (
            math.log10(max(self.author_followers, 1) + 1) / 7
        )  # Normalize to ~1 for 10M followers
        engagement_score = (
            math.log10(max(self.engagement, 1) + 1) / 5
        )  # Normalize to ~1 for 100k engagement
        return (follower_score + engagement_score) / 2


class TwitterSentiment(BaseModel):
    """Aggregated Twitter sentiment for a topic."""

    topic: str
    tweets: List[Tweet] = []
    sentiment_score: float = 0.0  # -1 (bearish) to +1 (bullish)
    volume: int = 0
    top_influencers: List[str] = []
    trending_hashtags: List[str] = []
    timestamp: datetime = datetime.now()

    @property
    def sentiment_label(self) -> str:
        if self.sentiment_score > 0.2:
            return "bullish"
        elif self.sentiment_score < -0.2:
            return "bearish"
        return "neutral"

    def format_for_prompt(self) -> str:
        """Format for AI agent consumption."""
        if not self.tweets:
            return f"No recent Twitter activity for '{self.topic}'"

        lines = [
            f"🐦 TWITTER SENTIMENT ({self.timestamp.strftime('%Y-%m-%d %H:%M')}):",
            f"Topic: {self.topic}",
            f"Sentiment: {self.sentiment_label.upper()} (score: {self.sentiment_score:+.2f})",
            f"Volume: {self.volume} tweets analyzed",
            "",
        ]

        if self.trending_hashtags:
            lines.append(f"Trending: {', '.join(self.trending_hashtags[:5])}")

        if self.top_influencers:
            lines.append(f"Key voices: {', '.join(self.top_influencers[:3])}")

        # Top tweets by influence
        top_tweets = sorted(self.tweets, key=lambda t: t.influence_score, reverse=True)[:3]
        if top_tweets:
            lines.append("")
            lines.append("Notable tweets:")
            for i, tweet in enumerate(top_tweets, 1):
                # Truncate long tweets
                text = tweet.text[:150] + "..." if len(tweet.text) > 150 else tweet.text
                text = text.replace("\n", " ")
                lines.append(f"  [{i}] @{tweet.author}: {text}")

        return "\n".join(lines)


# Sentiment keywords for basic analysis
BULLISH_KEYWORDS = [
    "bullish",
    "moon",
    "pump",
    "buy",
    "long",
    "up",
    "rally",
    "breakout",
    "winning",
    "success",
    "confirmed",
    "happening",
    "yes",
    "will win",
    "looking good",
    "strong",
    "surge",
    "soar",
    "rocket",
    "lfg",
    "wagmi",
]

BEARISH_KEYWORDS = [
    "bearish",
    "dump",
    "sell",
    "short",
    "down",
    "crash",
    "breakdown",
    "losing",
    "fail",
    "denied",
    "not happening",
    "no",
    "will lose",
    "looking bad",
    "weak",
    "plunge",
    "tank",
    "rekt",
    "ngmi",
    "rug",
]


def analyze_tweet_sentiment(text: str) -> float:
    """
    Basic sentiment analysis on tweet text.
    Returns -1 (bearish) to +1 (bullish).
    """
    text_lower = text.lower()

    bullish_count = sum(1 for kw in BULLISH_KEYWORDS if kw in text_lower)
    bearish_count = sum(1 for kw in BEARISH_KEYWORDS if kw in text_lower)

    total = bullish_count + bearish_count
    if total == 0:
        return 0.0

    return (bullish_count - bearish_count) / total


def extract_hashtags(text: str) -> List[str]:
    """Extract hashtags from tweet text."""
    return re.findall(r"#(\w+)", text)


class TwitterClient:
    """
    Twitter/X client for social sentiment analysis.

    Supports multiple backends:
    1. Official Twitter API v2 (requires bearer token)
    2. Nitter scraping (no auth needed, rate limited)

    Usage:
        # With API key
        client = TwitterClient(bearer_token="your_token")

        # Without API key (uses scraping)
        client = TwitterClient()

        sentiment = await client.get_sentiment("Bitcoin ETF")
    """

    # Twitter API v2 endpoints
    TWITTER_API_BASE = "https://api.twitter.com/2"

    # Nitter instances for scraping fallback
    NITTER_INSTANCES = [
        "https://nitter.privacydev.net",
        "https://nitter.poast.org",
        "https://nitter.cz",
    ]

    def __init__(
        self,
        bearer_token: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize Twitter client.

        Args:
            bearer_token: Twitter API v2 bearer token (optional)
            timeout: Request timeout
        """
        self.bearer_token = bearer_token
        self.timeout = timeout
        self.use_api = bool(bearer_token)

        # HTTP client for API calls
        headers = {}
        if bearer_token:
            headers["Authorization"] = f"Bearer {bearer_token}"

        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers=headers,
            follow_redirects=True,
        )

        mode = "API" if self.use_api else "scraping"
        logger.info(f"TwitterClient initialized (mode: {mode})")

    async def search_tweets(
        self,
        query: str,
        max_results: int = 50,
        hours_back: int = 24,
    ) -> List[Tweet]:
        """
        Search for tweets matching a query.

        Args:
            query: Search query
            max_results: Maximum tweets to return
            hours_back: How far back to search

        Returns:
            List of Tweet objects
        """
        if self.use_api:
            return await self._search_api(query, max_results, hours_back)
        else:
            return await self._search_scrape(query, max_results)

    async def _search_api(
        self,
        query: str,
        max_results: int,
        hours_back: int,
    ) -> List[Tweet]:
        """Search using official Twitter API v2."""
        try:
            # Build query with recency
            start_time = (datetime.utcnow() - timedelta(hours=hours_back)).isoformat() + "Z"

            params = {
                "query": f"{query} -is:retweet lang:en",
                "max_results": min(max_results, 100),
                "start_time": start_time,
                "tweet.fields": "created_at,public_metrics,author_id",
                "user.fields": "username,public_metrics",
                "expansions": "author_id",
            }

            response = await self._client.get(
                f"{self.TWITTER_API_BASE}/tweets/search/recent",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            # Map author IDs to usernames
            users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}

            tweets = []
            for tweet_data in data.get("data", []):
                author_id = tweet_data.get("author_id", "")
                author = users.get(author_id, {})

                tweets.append(
                    Tweet(
                        id=tweet_data["id"],
                        text=tweet_data["text"],
                        author=author.get("username", "unknown"),
                        author_followers=author.get("public_metrics", {}).get("followers_count", 0),
                        created_at=datetime.fromisoformat(
                            tweet_data["created_at"].replace("Z", "+00:00")
                        ),
                        likes=tweet_data.get("public_metrics", {}).get("like_count", 0),
                        retweets=tweet_data.get("public_metrics", {}).get("retweet_count", 0),
                        replies=tweet_data.get("public_metrics", {}).get("reply_count", 0),
                        url=f"https://twitter.com/{author.get('username', 'i')}/status/{tweet_data['id']}",
                    )
                )

            logger.debug(f"Twitter API returned {len(tweets)} tweets for '{query}'")
            return tweets

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning("Twitter API rate limited")
            else:
                logger.error(f"Twitter API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Twitter API error: {e}")
            return []

    async def _search_scrape(
        self,
        query: str,
        max_results: int,
    ) -> List[Tweet]:
        """Search using Nitter scraping (fallback)."""
        tweets = []

        for instance in self.NITTER_INSTANCES:
            try:
                # Nitter search endpoint
                url = f"{instance}/search"
                params = {"f": "tweets", "q": query}

                response = await self._client.get(url, params=params)
                if response.status_code != 200:
                    continue

                # Parse HTML response (basic extraction)
                html = response.text
                tweets = self._parse_nitter_html(html, max_results)

                if tweets:
                    logger.debug(f"Nitter ({instance}) returned {len(tweets)} tweets")
                    break

            except Exception as e:
                logger.debug(f"Nitter {instance} failed: {e}")
                continue

        if not tweets:
            logger.warning(f"All Nitter instances failed for query: {query}")

        return tweets

    def _parse_nitter_html(self, html: str, max_results: int) -> List[Tweet]:
        """Parse tweets from Nitter HTML response."""
        tweets = []

        # Basic regex extraction (works for most Nitter instances)
        # Find tweet containers
        tweet_pattern = r'class="tweet-content[^"]*"[^>]*>([^<]+)</div>'
        author_pattern = r'class="username"[^>]*>@?(\w+)</a>'

        contents = re.findall(tweet_pattern, html, re.DOTALL)
        authors = re.findall(author_pattern, html)

        for i, (content, author) in enumerate(zip(contents, authors)):
            if i >= max_results:
                break

            # Clean up text
            text = re.sub(r"<[^>]+>", "", content).strip()
            text = re.sub(r"\s+", " ", text)

            if len(text) > 10:  # Filter empty/tiny tweets
                tweets.append(
                    Tweet(
                        id=f"nitter_{i}_{hash(text) % 10000}",
                        text=text,
                        author=author,
                        author_followers=0,  # Not available via scraping
                        created_at=datetime.now(),  # Approximate
                        likes=0,
                        retweets=0,
                        replies=0,
                    )
                )

        return tweets

    async def get_sentiment(
        self,
        topic: str,
        max_tweets: int = 50,
        hours_back: int = 24,
    ) -> TwitterSentiment:
        """
        Get aggregated sentiment for a topic.

        Args:
            topic: Topic to analyze
            max_tweets: Max tweets to analyze
            hours_back: Time window

        Returns:
            TwitterSentiment object
        """
        logger.info(f"Fetching Twitter sentiment for: {topic}")

        tweets = await self.search_tweets(topic, max_tweets, hours_back)

        if not tweets:
            return TwitterSentiment(
                topic=topic,
                tweets=[],
                sentiment_score=0.0,
                volume=0,
                timestamp=datetime.now(),
            )

        # Analyze sentiment
        sentiment_scores = []
        all_hashtags = []
        author_influence = {}

        for tweet in tweets:
            # Individual tweet sentiment
            score = analyze_tweet_sentiment(tweet.text)
            # Weight by influence
            weighted_score = score * (1 + tweet.influence_score)
            sentiment_scores.append(weighted_score)

            # Collect hashtags
            all_hashtags.extend(extract_hashtags(tweet.text))

            # Track influential authors
            if tweet.author not in author_influence:
                author_influence[tweet.author] = tweet.influence_score
            else:
                author_influence[tweet.author] = max(
                    author_influence[tweet.author], tweet.influence_score
                )

        # Aggregate sentiment
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
        # Clamp to [-1, 1]
        avg_sentiment = max(-1.0, min(1.0, avg_sentiment))

        # Top hashtags by frequency
        hashtag_counts = {}
        for tag in all_hashtags:
            hashtag_counts[tag] = hashtag_counts.get(tag, 0) + 1
        trending = sorted(hashtag_counts.keys(), key=lambda t: hashtag_counts[t], reverse=True)

        # Top influencers
        top_authors = sorted(
            author_influence.keys(), key=lambda a: author_influence[a], reverse=True
        )

        return TwitterSentiment(
            topic=topic,
            tweets=tweets,
            sentiment_score=avg_sentiment,
            volume=len(tweets),
            top_influencers=top_authors[:5],
            trending_hashtags=trending[:10],
            timestamp=datetime.now(),
        )

    async def get_market_sentiment(
        self,
        market_question: str,
        extract_keywords: bool = True,
    ) -> TwitterSentiment:
        """
        Get Twitter sentiment for a prediction market question.

        Args:
            market_question: The market question
            extract_keywords: Auto-extract search keywords

        Returns:
            TwitterSentiment
        """
        # Extract key terms from question
        if extract_keywords:
            # Remove common words
            stop_words = {
                "will",
                "the",
                "a",
                "an",
                "in",
                "on",
                "at",
                "by",
                "for",
                "to",
                "of",
                "and",
                "or",
                "be",
                "is",
                "are",
                "was",
                "were",
                "this",
                "that",
                "these",
                "those",
                "it",
                "its",
                "what",
                "when",
                "where",
                "who",
                "how",
                "which",
                "before",
                "after",
            }
            words = re.findall(r"\b\w+\b", market_question.lower())
            keywords = [w for w in words if w not in stop_words and len(w) > 2]

            # Take top 3-4 keywords
            query = " ".join(keywords[:4])
        else:
            query = market_question

        return await self.get_sentiment(query)

    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
