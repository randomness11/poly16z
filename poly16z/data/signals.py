"""
Signal Generator

Generates trading signals from market data and external sources.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import numpy as np
from loguru import logger
from pydantic import BaseModel

from poly16z.api.client import Market


class Signal(BaseModel):
    """Trading signal."""

    type: str  # "momentum", "volume", "news", "sentiment", etc.
    market_id: str
    strength: float  # -1 to 1
    direction: str  # "bullish", "bearish", "neutral"
    confidence: float  # 0 to 1
    metadata: Dict[str, Any] = {}
    timestamp: datetime = datetime.now()


class SignalGenerator:
    """
    Generates trading signals from various data sources.

    Signals:
    - Momentum: Price/probability changes
    - Volume: Unusual trading activity
    - News: Breaking news events
    - Sentiment: Social media sentiment
    - Liquidity: Market depth changes
    """

    def __init__(self):
        """Initialize signal generator."""
        self.price_history: Dict[str, List[float]] = {}
        self.volume_history: Dict[str, List[float]] = {}

    def update_market_data(
        self,
        market: Market,
    ) -> None:
        """
        Update historical market data.

        Args:
            market: Market object
        """
        market_id = market.condition_id

        # Update price history
        if market_id not in self.price_history:
            self.price_history[market_id] = []

        # Store first outcome price (simplified)
        if market.outcome_prices:
            self.price_history[market_id].append(market.outcome_prices[0])

        # Keep only last 100 data points
        if len(self.price_history[market_id]) > 100:
            self.price_history[market_id] = self.price_history[market_id][-100:]

        # Update volume history
        if market_id not in self.volume_history:
            self.volume_history[market_id] = []

        self.volume_history[market_id].append(market.volume)

        if len(self.volume_history[market_id]) > 100:
            self.volume_history[market_id] = self.volume_history[market_id][-100:]

    def detect_momentum(
        self,
        market: Market,
        threshold: float = 0.10,
    ) -> Optional[Signal]:
        """
        Detect momentum signals.

        Args:
            market: Market to analyze
            threshold: Minimum price change threshold

        Returns:
            Signal if momentum detected
        """
        market_id = market.condition_id

        if market_id not in self.price_history:
            return None

        prices = self.price_history[market_id]
        if len(prices) < 2:
            return None

        # Calculate recent price change
        current_price = prices[-1]
        previous_price = prices[-2]
        change_pct = (current_price - previous_price) / previous_price

        if abs(change_pct) < threshold:
            return None

        # Determine direction and strength
        if change_pct > 0:
            direction = "bullish"
            strength = min(change_pct / threshold, 1.0)
        else:
            direction = "bearish"
            strength = max(change_pct / threshold, -1.0)

        signal = Signal(
            type="momentum",
            market_id=market_id,
            strength=strength,
            direction=direction,
            confidence=min(abs(strength), 1.0),
            metadata={
                "change_pct": change_pct,
                "current_price": current_price,
                "previous_price": previous_price,
            },
        )

        logger.info(
            f"Momentum signal: {direction} {strength:+.2f} "
            f"for {market.question[:50]}..."
        )

        return signal

    def detect_volume_spike(
        self,
        market: Market,
        threshold: float = 2.0,
    ) -> Optional[Signal]:
        """
        Detect volume spikes.

        Args:
            market: Market to analyze
            threshold: Multiplier for average volume

        Returns:
            Signal if volume spike detected
        """
        market_id = market.condition_id

        if market_id not in self.volume_history:
            return None

        volumes = self.volume_history[market_id]
        if len(volumes) < 10:
            return None

        # Calculate average volume
        avg_volume = np.mean(volumes[:-1])
        current_volume = volumes[-1]

        if current_volume < avg_volume * threshold:
            return None

        volume_ratio = current_volume / avg_volume
        strength = min(volume_ratio / threshold, 2.0) - 1.0  # 0 to 1

        signal = Signal(
            type="volume",
            market_id=market_id,
            strength=strength,
            direction="bullish",  # High volume generally bullish
            confidence=min(strength, 1.0),
            metadata={
                "volume_ratio": volume_ratio,
                "current_volume": current_volume,
                "avg_volume": avg_volume,
            },
        )

        logger.info(
            f"Volume spike signal: {volume_ratio:.1f}x average "
            f"for {market.question[:50]}..."
        )

        return signal

    def detect_price_extremes(
        self,
        market: Market,
        extreme_threshold: float = 0.10,
    ) -> Optional[Signal]:
        """
        Detect extreme prices (potential contrarian opportunities).

        Args:
            market: Market to analyze
            extreme_threshold: Distance from 0.5 to be considered extreme

        Returns:
            Signal if extreme detected
        """
        if not market.outcome_prices:
            return None

        price = market.outcome_prices[0]

        # Check if price is extreme (very high or very low)
        if price < extreme_threshold:
            # Very low price - potential contrarian buy
            signal = Signal(
                type="extreme",
                market_id=market.condition_id,
                strength=1.0 - (price / extreme_threshold),
                direction="bullish",
                confidence=0.6,  # Lower confidence for contrarian
                metadata={
                    "price": price,
                    "type": "oversold",
                },
            )
            logger.info(f"Oversold signal for {market.question[:50]}...")
            return signal

        elif price > (1.0 - extreme_threshold):
            # Very high price - potential contrarian sell
            signal = Signal(
                type="extreme",
                market_id=market.condition_id,
                strength=-((price - (1.0 - extreme_threshold)) / extreme_threshold),
                direction="bearish",
                confidence=0.6,
                metadata={
                    "price": price,
                    "type": "overbought",
                },
            )
            logger.info(f"Overbought signal for {market.question[:50]}...")
            return signal

        return None

    def generate_signals(
        self,
        markets: List[Market],
    ) -> List[Signal]:
        """
        Generate all signals for a list of markets.

        Args:
            markets: Markets to analyze

        Returns:
            List of generated signals
        """
        signals = []

        for market in markets:
            # Update historical data
            self.update_market_data(market)

            # Generate various signals
            momentum_signal = self.detect_momentum(market)
            if momentum_signal:
                signals.append(momentum_signal)

            volume_signal = self.detect_volume_spike(market)
            if volume_signal:
                signals.append(volume_signal)

            extreme_signal = self.detect_price_extremes(market)
            if extreme_signal:
                signals.append(extreme_signal)

        logger.info(f"Generated {len(signals)} signals from {len(markets)} markets")
        return signals
