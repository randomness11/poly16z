"""
Social Media Collector

Collects signals from Twitter and other social platforms.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from loguru import logger
from pydantic import BaseModel


class Tweet(BaseModel):
    """Represents a tweet."""

    id: str
    text: str
    author: str
    created_at: datetime
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    url: str = ""


class SocialCollector:
    """
    Collects social media signals.

    Supports:
    - Twitter/X search and streaming
    - Sentiment analysis
    - Trend detection
    """

    def __init__(
        self,
        twitter_bearer_token: Optional[str] = None,
    ):
        """
        Initialize social collector.

        Args:
            twitter_bearer_token: Twitter API bearer token
        """
        self.twitter_bearer_token = twitter_bearer_token

        # Cache
        self.tweets_cache: List[Tweet] = []

    async def fetch_tweets(
        self,
        query: str,
        max_results: int = 100,
        hours: int = 24,
    ) -> List[Tweet]:
        """
        Fetch tweets matching a query.

        Args:
            query: Search query
            max_results: Maximum tweets to return
            hours: Hours to look back

        Returns:
            List of Tweet objects
        """
        if not self.twitter_bearer_token:
            logger.warning("Twitter bearer token not provided")
            return []

        try:
            import tweepy

            # Initialize client
            client = tweepy.Client(bearer_token=self.twitter_bearer_token)

            # Calculate start time
            start_time = datetime.now() - timedelta(hours=hours)

            # Search tweets
            response = client.search_recent_tweets(
                query=query,
                max_results=max_results,
                start_time=start_time,
                tweet_fields=["created_at", "public_metrics"],
            )

            tweets = []
            if response.data:
                for tweet_data in response.data:
                    metrics = tweet_data.public_metrics or {}

                    tweet = Tweet(
                        id=tweet_data.id,
                        text=tweet_data.text,
                        author="",  # Would need user lookup
                        created_at=tweet_data.created_at,
                        likes=metrics.get("like_count", 0),
                        retweets=metrics.get("retweet_count", 0),
                        replies=metrics.get("reply_count", 0),
                        url=f"https://twitter.com/i/web/status/{tweet_data.id}",
                    )
                    tweets.append(tweet)

            logger.info(f"Fetched {len(tweets)} tweets for query: {query}")
            self.tweets_cache.extend(tweets)

            return tweets

        except Exception as e:
            logger.error(f"Error fetching tweets: {e}")
            return []

    def analyze_sentiment(
        self,
        tweets: List[Tweet],
    ) -> Dict[str, Any]:
        """
        Analyze sentiment of tweets.

        Args:
            tweets: List of tweets

        Returns:
            Sentiment analysis results
        """
        if not tweets:
            return {
                "avg_sentiment": 0.0,
                "positive": 0,
                "negative": 0,
                "neutral": 0,
            }

        # Simple keyword-based sentiment (could be enhanced with ML model)
        positive_words = ["bullish", "moon", "pump", "win", "good", "great", "up"]
        negative_words = ["bearish", "dump", "crash", "loss", "bad", "down"]

        sentiments = []
        positive_count = 0
        negative_count = 0
        neutral_count = 0

        for tweet in tweets:
            text_lower = tweet.text.lower()

            pos_score = sum(1 for word in positive_words if word in text_lower)
            neg_score = sum(1 for word in negative_words if word in text_lower)

            if pos_score > neg_score:
                sentiment = 1
                positive_count += 1
            elif neg_score > pos_score:
                sentiment = -1
                negative_count += 1
            else:
                sentiment = 0
                neutral_count += 1

            sentiments.append(sentiment)

        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0

        return {
            "avg_sentiment": avg_sentiment,
            "positive": positive_count,
            "negative": negative_count,
            "neutral": neutral_count,
            "total": len(tweets),
        }

    def detect_trending(
        self,
        keywords: List[str],
        threshold: int = 10,
        hours: int = 1,
    ) -> Dict[str, int]:
        """
        Detect trending keywords.

        Args:
            keywords: Keywords to track
            threshold: Minimum mentions to be considered trending
            hours: Time window

        Returns:
            Dictionary of keyword counts
        """
        cutoff = datetime.now() - timedelta(hours=hours)

        counts = {keyword: 0 for keyword in keywords}

        for tweet in self.tweets_cache:
            if tweet.created_at < cutoff:
                continue

            text_lower = tweet.text.lower()
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    counts[keyword] += 1

        trending = {k: v for k, v in counts.items() if v >= threshold}

        if trending:
            logger.info(f"Trending keywords: {trending}")

        return trending
