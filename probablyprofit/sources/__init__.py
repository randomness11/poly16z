"""Data sources for market intelligence."""

from probablyprofit.sources.perplexity import PerplexityClient, NewsContext
from probablyprofit.sources.sentiment import SentimentAnalyzer, MarketSentiment
from probablyprofit.sources.twitter import TwitterClient, TwitterSentiment, Tweet
from probablyprofit.sources.reddit import RedditClient, RedditSentiment, RedditPost
from probablyprofit.sources.trends import GoogleTrendsClient, TrendsSentiment, TrendData
from probablyprofit.sources.aggregator import SignalAggregator, AlphaSignal, create_aggregator

__all__ = [
    # Perplexity (news)
    "PerplexityClient",
    "NewsContext",
    # Sentiment
    "SentimentAnalyzer",
    "MarketSentiment",
    # Twitter
    "TwitterClient",
    "TwitterSentiment",
    "Tweet",
    # Reddit
    "RedditClient",
    "RedditSentiment",
    "RedditPost",
    # Google Trends
    "GoogleTrendsClient",
    "TrendsSentiment",
    "TrendData",
    # Aggregator
    "SignalAggregator",
    "AlphaSignal",
    "create_aggregator",
]
