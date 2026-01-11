"""
Intelligence-Enhanced Agent

Wraps any base agent with multi-source alpha intelligence.
Aggregates Twitter, Reddit, Google Trends, and news for smarter decisions.
"""

import os
from typing import Any, List, Optional
from loguru import logger

from probablyprofit.agent.base import BaseAgent, Observation
from probablyprofit.api.client import PolymarketClient, Market
from probablyprofit.risk.manager import RiskManager


class IntelligenceAgent(BaseAgent):
    """
    Wraps any trading agent with multi-source alpha intelligence.

    This agent enhances observations with:
    - News context from Perplexity API
    - Twitter/X social sentiment
    - Reddit community sentiment
    - Google Trends momentum
    - Combined alpha signals

    Example:
        base_agent = OpenAIAgent(...)
        intel_agent = IntelligenceAgent(
            wrapped_agent=base_agent,
            enable_aggregator=True,
            top_n_markets=3,
        )
        await intel_agent.run()
    """

    def __init__(
        self,
        wrapped_agent: BaseAgent,
        perplexity_api_key: Optional[str] = None,
        twitter_token: Optional[str] = None,
        top_n_markets: int = 3,
        enable_sentiment: bool = True,
        enable_aggregator: bool = False,
    ):
        """
        Initialize intelligence wrapper.

        Args:
            wrapped_agent: The base agent to wrap
            perplexity_api_key: Perplexity API key for news
            twitter_token: Twitter API bearer token (optional)
            top_n_markets: Number of top markets to fetch intel for
            enable_sentiment: Whether to calculate sentiment
            enable_aggregator: Use full multi-source aggregator
        """
        # Inherit settings from wrapped agent
        super().__init__(
            client=wrapped_agent.client,
            risk_manager=wrapped_agent.risk_manager,
            name=f"Intel-{wrapped_agent.name}",
            loop_interval=wrapped_agent.loop_interval,
            strategy=wrapped_agent.strategy,
            dry_run=wrapped_agent.dry_run,
        )

        self.wrapped_agent = wrapped_agent
        self.top_n_markets = top_n_markets
        self.enable_sentiment = enable_sentiment
        self.enable_aggregator = enable_aggregator

        # Initialize signal aggregator (multi-source)
        self.aggregator = None
        if enable_aggregator:
            try:
                from probablyprofit.sources.aggregator import SignalAggregator
                self.aggregator = SignalAggregator(
                    twitter_token=twitter_token or os.getenv("TWITTER_BEARER_TOKEN"),
                    perplexity_key=perplexity_api_key or os.getenv("PERPLEXITY_API_KEY"),
                )
                logger.info("🎯 Multi-source signal aggregator enabled")
            except Exception as e:
                logger.warning(f"Signal aggregator not available: {e}")

        # Initialize Perplexity client (standalone, if aggregator disabled)
        self.perplexity = None
        if not enable_aggregator and perplexity_api_key:
            try:
                from probablyprofit.sources.perplexity import PerplexityClient
                self.perplexity = PerplexityClient(api_key=perplexity_api_key)
                logger.info("📰 News intelligence enabled via Perplexity")
            except ImportError:
                logger.warning("Perplexity client not available")

        # Initialize sentiment analyzer
        self.sentiment_analyzer = None
        if enable_sentiment and not enable_aggregator:
            try:
                from probablyprofit.sources.sentiment import SentimentAnalyzer
                self.sentiment_analyzer = SentimentAnalyzer()
                logger.info("📊 Sentiment analysis enabled")
            except ImportError:
                logger.warning("Sentiment analyzer not available")
    
    def _get_top_markets(self, markets: List[Market], n: int) -> List[Market]:
        """Get top N markets by volume."""
        sorted_markets = sorted(markets, key=lambda m: m.volume, reverse=True)
        return sorted_markets[:n]
    
    async def _enrich_observation(self, observation: Observation) -> Observation:
        """
        Enrich observation with intelligence data.

        Args:
            observation: Base observation

        Returns:
            Enhanced observation with news, sentiment, and alpha signals
        """
        # Get top markets for intel fetching
        top_markets = self._get_top_markets(observation.markets, self.top_n_markets)

        news_summaries = []
        sentiment_summaries = []
        market_sentiments = {}

        # Use aggregator for multi-source intelligence
        if self.aggregator and top_markets:
            logger.info(f"🎯 Fetching multi-source intel for {len(top_markets)} markets...")

            for market in top_markets:
                try:
                    # Get combined alpha signal
                    signal = await self.aggregator.get_signal(market.question)

                    # Format for prompt
                    news_summaries.append(signal.format_for_prompt())

                    # Store sentiment data
                    market_sentiments[market.condition_id] = {
                        "direction": signal.direction,
                        "sentiment_score": signal.sentiment_score,
                        "momentum_score": signal.momentum_score,
                        "confidence": signal.confidence,
                        "sources": signal.sources_used,
                        "twitter": signal.twitter_sentiment,
                        "reddit": signal.reddit_sentiment,
                        "trends": signal.trends_momentum,
                        "news": signal.news_sentiment,
                    }

                    sentiment_summaries.append(
                        f"Market: {market.question[:50]}... → "
                        f"{signal.direction.upper()} ({signal.confidence:.0%} confidence)"
                    )

                except Exception as e:
                    logger.warning(f"Failed to fetch signal for market: {e}")

        # Fallback to Perplexity-only mode
        elif self.perplexity and top_markets:
            logger.info(f"📰 Fetching news for {len(top_markets)} top markets...")

            for market in top_markets:
                try:
                    context = await self.perplexity.get_market_context(market.question)
                    news_summaries.append(context.format_for_prompt())

                    # Calculate sentiment if enabled
                    if self.sentiment_analyzer:
                        sentiment = await self.sentiment_analyzer.analyze(
                            market_id=market.condition_id,
                            market_question=market.question,
                            news_context=context,
                            price_history=market.outcome_prices,
                        )
                        sentiment_summaries.append(sentiment.format_for_prompt())
                        market_sentiments[market.condition_id] = sentiment.model_dump()

                except Exception as e:
                    logger.warning(f"Failed to fetch intel for market: {e}")

        # Combine into observation
        if news_summaries:
            observation.news_context = "\n\n---\n\n".join(news_summaries)

        if sentiment_summaries:
            observation.sentiment_summary = "\n".join(sentiment_summaries)

        if market_sentiments:
            observation.market_sentiments = market_sentiments

        return observation
    
    async def observe(self) -> Observation:
        """
        Observe with intelligence enrichment.
        """
        # Get base observation
        observation = await super().observe()
        
        # Enrich with intelligence
        observation = await self._enrich_observation(observation)
        
        return observation
    
    async def decide(self, observation: Observation):
        """
        Delegate decision to wrapped agent with enriched observation.
        """
        return await self.wrapped_agent.decide(observation)


def wrap_with_intelligence(
    agent: BaseAgent,
    enable_news: bool = True,
    enable_alpha: bool = False,
    top_n_markets: int = 3,
) -> BaseAgent:
    """
    Convenience function to wrap an agent with intelligence.

    Args:
        agent: Agent to wrap
        enable_news: Whether to enable news fetching (Perplexity only)
        enable_alpha: Use full multi-source alpha aggregator (Twitter, Reddit, Trends, News)
        top_n_markets: Markets to fetch intel for

    Returns:
        Intelligence-wrapped agent (or original if no sources available)
    """
    perplexity_key = os.getenv("PERPLEXITY_API_KEY")
    twitter_token = os.getenv("TWITTER_BEARER_TOKEN")

    # If alpha mode, use aggregator (works even without API keys - uses Reddit/Trends)
    if enable_alpha:
        logger.info("🎯 Alpha mode enabled - using multi-source aggregator")
        return IntelligenceAgent(
            wrapped_agent=agent,
            perplexity_api_key=perplexity_key,
            twitter_token=twitter_token,
            top_n_markets=top_n_markets,
            enable_sentiment=True,
            enable_aggregator=True,
        )

    # Standard news-only mode
    if not perplexity_key and enable_news:
        logger.warning("PERPLEXITY_API_KEY not set - news intelligence disabled")
        return agent

    return IntelligenceAgent(
        wrapped_agent=agent,
        perplexity_api_key=perplexity_key,
        top_n_markets=top_n_markets,
        enable_sentiment=True,
        enable_aggregator=False,
    )
