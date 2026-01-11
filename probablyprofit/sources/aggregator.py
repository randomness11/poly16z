"""
Signal Aggregator

Combines multiple data sources into unified alpha signals.
The brain that synthesizes Twitter, Reddit, Google Trends, and news.
"""

import asyncio
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from pydantic import BaseModel
from loguru import logger


class AlphaSignal(BaseModel):
    """A unified alpha signal combining multiple sources."""

    market_question: str

    # Aggregated scores (-1 to +1)
    sentiment_score: float = 0.0  # Overall sentiment
    momentum_score: float = 0.0  # Trend momentum
    volume_score: float = 0.0  # Social volume/attention
    confidence: float = 0.5  # Confidence in signal

    # Direction
    direction: str = "neutral"  # bullish, bearish, neutral

    # Source breakdown
    twitter_sentiment: float = 0.0
    reddit_sentiment: float = 0.0
    trends_momentum: float = 0.0
    news_sentiment: float = 0.0

    # Source availability
    sources_used: List[str] = []
    sources_failed: List[str] = []

    # Raw data for debugging
    twitter_data: Optional[Dict[str, Any]] = None
    reddit_data: Optional[Dict[str, Any]] = None
    trends_data: Optional[Dict[str, Any]] = None
    news_data: Optional[Dict[str, Any]] = None

    timestamp: datetime = datetime.now()

    def format_for_prompt(self) -> str:
        """Format signal for AI agent consumption."""
        lines = [
            "=" * 50,
            f"🎯 ALPHA SIGNAL ({self.timestamp.strftime('%Y-%m-%d %H:%M')})",
            "=" * 50,
            "",
            f"Overall Direction: {self.direction.upper()}",
            f"Confidence: {self.confidence:.0%}",
            "",
            "📊 SCORES:",
            f"  Sentiment: {self.sentiment_score:+.2f} (range: -1 to +1)",
            f"  Momentum:  {self.momentum_score:+.2f}",
            f"  Volume:    {self.volume_score:.2f} (0=low, 1=high)",
            "",
            "📡 SOURCE BREAKDOWN:",
        ]

        if "twitter" in self.sources_used:
            lines.append(f"  🐦 Twitter:  {self.twitter_sentiment:+.2f}")
        if "reddit" in self.sources_used:
            lines.append(f"  🔴 Reddit:   {self.reddit_sentiment:+.2f}")
        if "trends" in self.sources_used:
            lines.append(f"  📈 Trends:   {self.trends_momentum:+.2f}")
        if "news" in self.sources_used:
            lines.append(f"  📰 News:     {self.news_sentiment:+.2f}")

        if self.sources_failed:
            lines.append(f"\n  ⚠️  Failed: {', '.join(self.sources_failed)}")

        lines.append("")
        lines.append("=" * 50)

        return "\n".join(lines)


@dataclass
class AggregatorConfig:
    """Configuration for signal aggregation."""

    # Source weights (must sum to 1.0)
    twitter_weight: float = 0.30
    reddit_weight: float = 0.20
    trends_weight: float = 0.15
    news_weight: float = 0.35

    # Thresholds
    min_sources: int = 1  # Minimum sources for valid signal
    high_confidence_threshold: float = 0.7

    # Timeouts
    source_timeout: float = 30.0


class SignalAggregator:
    """
    Aggregates signals from multiple data sources.

    Combines Twitter, Reddit, Google Trends, and news
    into unified alpha signals for trading decisions.

    Usage:
        aggregator = SignalAggregator()
        signal = await aggregator.get_signal("Will Bitcoin reach $100k?")
        print(signal.direction, signal.confidence)
    """

    def __init__(
        self,
        twitter_token: Optional[str] = None,
        perplexity_key: Optional[str] = None,
        config: Optional[AggregatorConfig] = None,
    ):
        """
        Initialize signal aggregator.

        Args:
            twitter_token: Twitter API bearer token (optional)
            perplexity_key: Perplexity API key (optional)
            config: Aggregator configuration
        """
        self.config = config or AggregatorConfig()

        # Initialize clients
        self._twitter = None
        self._reddit = None
        self._trends = None
        self._perplexity = None

        # Twitter (optional - uses scraping fallback)
        try:
            from probablyprofit.sources.twitter import TwitterClient
            self._twitter = TwitterClient(bearer_token=twitter_token)
            logger.info("✅ Twitter source enabled")
        except Exception as e:
            logger.warning(f"Twitter source disabled: {e}")

        # Reddit (always available - no auth needed)
        try:
            from probablyprofit.sources.reddit import RedditClient
            self._reddit = RedditClient()
            logger.info("✅ Reddit source enabled")
        except Exception as e:
            logger.warning(f"Reddit source disabled: {e}")

        # Google Trends (always available - no auth needed)
        try:
            from probablyprofit.sources.trends import GoogleTrendsClient
            self._trends = GoogleTrendsClient()
            logger.info("✅ Google Trends source enabled")
        except Exception as e:
            logger.warning(f"Google Trends source disabled: {e}")

        # Perplexity news (optional)
        if perplexity_key:
            try:
                from probablyprofit.sources.perplexity import PerplexityClient
                self._perplexity = PerplexityClient(api_key=perplexity_key)
                logger.info("✅ Perplexity news source enabled")
            except Exception as e:
                logger.warning(f"Perplexity source disabled: {e}")

        logger.info(f"SignalAggregator initialized with {self._count_sources()} sources")

    def _count_sources(self) -> int:
        """Count available sources."""
        return sum([
            self._twitter is not None,
            self._reddit is not None,
            self._trends is not None,
            self._perplexity is not None,
        ])

    async def get_signal(
        self,
        market_question: str,
        include_raw: bool = False,
    ) -> AlphaSignal:
        """
        Get aggregated alpha signal for a market.

        Args:
            market_question: The prediction market question
            include_raw: Include raw data from sources

        Returns:
            AlphaSignal with combined sentiment and momentum
        """
        logger.info(f"Aggregating signals for: {market_question[:50]}...")

        sources_used = []
        sources_failed = []

        # Collect signals from all sources in parallel
        tasks = {}

        if self._twitter:
            tasks["twitter"] = self._fetch_twitter(market_question)
        if self._reddit:
            tasks["reddit"] = self._fetch_reddit(market_question)
        if self._trends:
            tasks["trends"] = self._fetch_trends(market_question)
        if self._perplexity:
            tasks["news"] = self._fetch_news(market_question)

        # Execute all in parallel with timeout
        results = {}
        if tasks:
            try:
                gathered = await asyncio.wait_for(
                    asyncio.gather(*tasks.values(), return_exceptions=True),
                    timeout=self.config.source_timeout,
                )

                for (name, _), result in zip(tasks.items(), gathered):
                    if isinstance(result, Exception):
                        logger.warning(f"Source '{name}' failed: {result}")
                        sources_failed.append(name)
                    else:
                        results[name] = result
                        sources_used.append(name)

            except asyncio.TimeoutError:
                logger.error("Signal aggregation timed out")

        # Extract sentiment scores
        twitter_sent = results.get("twitter", {}).get("sentiment", 0.0)
        reddit_sent = results.get("reddit", {}).get("sentiment", 0.0)
        trends_mom = results.get("trends", {}).get("momentum", 0.0)
        news_sent = results.get("news", {}).get("sentiment", 0.0)

        # Calculate weighted average sentiment
        weighted_sum = 0.0
        weight_sum = 0.0

        if "twitter" in results:
            weighted_sum += twitter_sent * self.config.twitter_weight
            weight_sum += self.config.twitter_weight

        if "reddit" in results:
            weighted_sum += reddit_sent * self.config.reddit_weight
            weight_sum += self.config.reddit_weight

        if "trends" in results:
            # Trends is momentum, convert to sentiment-like scale
            trends_sent = trends_mom / 100  # Normalize percentage to -1/+1
            weighted_sum += trends_sent * self.config.trends_weight
            weight_sum += self.config.trends_weight

        if "news" in results:
            weighted_sum += news_sent * self.config.news_weight
            weight_sum += self.config.news_weight

        # Final sentiment
        sentiment = weighted_sum / weight_sum if weight_sum > 0 else 0.0
        sentiment = max(-1.0, min(1.0, sentiment))

        # Calculate momentum (average of trends and volume changes)
        momentum = trends_mom / 100 if "trends" in results else 0.0

        # Volume score (based on social activity)
        volume_scores = []
        if "twitter" in results:
            vol = results["twitter"].get("volume", 0)
            volume_scores.append(min(1.0, vol / 100))  # Normalize to 0-1
        if "reddit" in results:
            vol = results["reddit"].get("volume", 0)
            volume_scores.append(min(1.0, vol / 50))

        volume = sum(volume_scores) / len(volume_scores) if volume_scores else 0.5

        # Determine direction
        if sentiment > 0.2:
            direction = "bullish"
        elif sentiment < -0.2:
            direction = "bearish"
        else:
            direction = "neutral"

        # Calculate confidence
        confidence = self._calculate_confidence(
            sentiment=sentiment,
            num_sources=len(sources_used),
            volume=volume,
            agreement=self._check_agreement(twitter_sent, reddit_sent, news_sent),
        )

        # Build signal
        signal = AlphaSignal(
            market_question=market_question,
            sentiment_score=sentiment,
            momentum_score=momentum,
            volume_score=volume,
            confidence=confidence,
            direction=direction,
            twitter_sentiment=twitter_sent,
            reddit_sentiment=reddit_sent,
            trends_momentum=trends_mom,
            news_sentiment=news_sent,
            sources_used=sources_used,
            sources_failed=sources_failed,
            timestamp=datetime.now(),
        )

        if include_raw:
            signal.twitter_data = results.get("twitter")
            signal.reddit_data = results.get("reddit")
            signal.trends_data = results.get("trends")
            signal.news_data = results.get("news")

        logger.info(
            f"Signal generated: {direction} (confidence: {confidence:.0%}) "
            f"from {len(sources_used)} sources"
        )

        return signal

    async def _fetch_twitter(self, question: str) -> Dict[str, Any]:
        """Fetch Twitter sentiment."""
        try:
            sentiment = await self._twitter.get_market_sentiment(question)
            return {
                "sentiment": sentiment.sentiment_score,
                "volume": sentiment.volume,
                "label": sentiment.sentiment_label,
                "formatted": sentiment.format_for_prompt(),
            }
        except Exception as e:
            raise RuntimeError(f"Twitter fetch failed: {e}")

    async def _fetch_reddit(self, question: str) -> Dict[str, Any]:
        """Fetch Reddit sentiment."""
        try:
            sentiment = await self._reddit.get_market_sentiment(question)
            return {
                "sentiment": sentiment.sentiment_score,
                "volume": sentiment.volume,
                "label": sentiment.sentiment_label,
                "subreddits": sentiment.top_subreddits,
                "formatted": sentiment.format_for_prompt(),
            }
        except Exception as e:
            raise RuntimeError(f"Reddit fetch failed: {e}")

    async def _fetch_trends(self, question: str) -> Dict[str, Any]:
        """Fetch Google Trends data."""
        try:
            trends = await self._trends.get_market_sentiment(question)
            return {
                "momentum": trends.momentum,
                "interest": trends.interest_score,
                "trend": trends.overall_trend,
                "formatted": trends.format_for_prompt(),
            }
        except Exception as e:
            raise RuntimeError(f"Trends fetch failed: {e}")

    async def _fetch_news(self, question: str) -> Dict[str, Any]:
        """Fetch Perplexity news."""
        try:
            context = await self._perplexity.get_market_context(question)

            # Map sentiment labels to scores
            sent_map = {"bullish": 0.7, "bearish": -0.7, "neutral": 0.0}
            sentiment = sent_map.get(context.sentiment, 0.0)

            return {
                "sentiment": sentiment * context.confidence,
                "label": context.sentiment,
                "confidence": context.confidence,
                "formatted": context.format_for_prompt(),
            }
        except Exception as e:
            raise RuntimeError(f"News fetch failed: {e}")

    def _check_agreement(self, *sentiments: float) -> float:
        """Check how much sources agree (0=disagree, 1=full agreement)."""
        valid = [s for s in sentiments if s != 0.0]
        if len(valid) < 2:
            return 0.5

        # Check if all same sign
        positive = sum(1 for s in valid if s > 0)
        negative = sum(1 for s in valid if s < 0)

        max_agreement = max(positive, negative)
        return max_agreement / len(valid)

    def _calculate_confidence(
        self,
        sentiment: float,
        num_sources: int,
        volume: float,
        agreement: float,
    ) -> float:
        """Calculate confidence in the signal."""
        # Base confidence from number of sources
        source_conf = min(1.0, num_sources / 3)

        # Stronger sentiment = higher confidence
        strength_conf = abs(sentiment)

        # Agreement between sources
        agreement_conf = agreement

        # Volume (more activity = more confidence)
        volume_conf = volume

        # Weighted combination
        confidence = (
            source_conf * 0.25 +
            strength_conf * 0.25 +
            agreement_conf * 0.30 +
            volume_conf * 0.20
        )

        return min(1.0, max(0.0, confidence))

    async def get_batch_signals(
        self,
        market_questions: List[str],
        max_concurrent: int = 3,
    ) -> Dict[str, AlphaSignal]:
        """
        Get signals for multiple markets.

        Args:
            market_questions: List of market questions
            max_concurrent: Max concurrent fetches

        Returns:
            Dict mapping question to signal
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def fetch_one(question: str) -> tuple:
            async with semaphore:
                signal = await self.get_signal(question)
                return (question, signal)

        tasks = [fetch_one(q) for q in market_questions]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        signals = {}
        for result in results:
            if isinstance(result, tuple):
                question, signal = result
                signals[question] = signal

        return signals

    async def close(self):
        """Close all clients."""
        if self._twitter:
            await self._twitter.close()
        if self._reddit:
            await self._reddit.close()
        if self._trends:
            await self._trends.close()
        if self._perplexity:
            await self._perplexity.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()


def create_aggregator(
    twitter_token: Optional[str] = None,
    perplexity_key: Optional[str] = None,
) -> SignalAggregator:
    """
    Create a SignalAggregator with env var fallbacks.

    Args:
        twitter_token: Twitter API token (or uses TWITTER_BEARER_TOKEN env)
        perplexity_key: Perplexity API key (or uses PERPLEXITY_API_KEY env)

    Returns:
        Configured SignalAggregator
    """
    return SignalAggregator(
        twitter_token=twitter_token or os.getenv("TWITTER_BEARER_TOKEN"),
        perplexity_key=perplexity_key or os.getenv("PERPLEXITY_API_KEY"),
    )
