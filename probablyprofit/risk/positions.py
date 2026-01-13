"""
Advanced Position Management

Trailing stops, correlation detection, and smart position sizing.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from loguru import logger
from pydantic import BaseModel


class StopType(Enum):
    """Types of stop-loss orders."""

    FIXED = "fixed"  # Fixed percentage stop
    TRAILING = "trailing"  # Moves with price
    BREAKEVEN = "breakeven"  # Move to entry after profit threshold


@dataclass
class TrailingStop:
    """
    Trailing stop-loss that locks in gains.

    As price moves in your favor, the stop moves up.
    If price reverses and hits the stop, position is closed.

    Example:
        Entry: $0.50
        Trailing %: 15%

        Price moves to $0.70:
          - Highest seen: $0.70
          - Stop level: $0.70 * (1 - 0.15) = $0.595

        Price drops to $0.60:
          - Still above stop ($0.595), hold position

        Price drops to $0.58:
          - Below stop! Trigger exit at ~$0.58
          - Locked in $0.08 profit instead of riding back to $0.50
    """

    market_id: str
    entry_price: float
    size: float
    side: str  # "long" or "short"

    # Stop configuration
    trail_pct: float = 0.15  # 15% trailing stop
    initial_stop_pct: float = 0.20  # 20% initial stop

    # Tracking
    highest_price: float = 0.0
    lowest_price: float = float("inf")
    current_stop: float = 0.0
    activated: bool = False  # Trailing activated after profit threshold

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Initialize stop levels."""
        if self.side == "long":
            self.highest_price = self.entry_price
            self.current_stop = self.entry_price * (1 - self.initial_stop_pct)
        else:
            self.lowest_price = self.entry_price
            self.current_stop = self.entry_price * (1 + self.initial_stop_pct)

    def update(self, current_price: float) -> Tuple[bool, float]:
        """
        Update trailing stop with current price.

        Args:
            current_price: Current market price

        Returns:
            Tuple of (should_exit, stop_level)
        """
        self.last_updated = datetime.now()

        if self.side == "long":
            return self._update_long(current_price)
        else:
            return self._update_short(current_price)

    def _update_long(self, current_price: float) -> Tuple[bool, float]:
        """Update for long position."""
        # Check if stop hit
        if current_price <= self.current_stop:
            logger.warning(
                f"🛑 Trailing stop HIT for {self.market_id}: "
                f"price ${current_price:.4f} <= stop ${self.current_stop:.4f}"
            )
            return (True, self.current_stop)

        # Update highest price
        if current_price > self.highest_price:
            self.highest_price = current_price

            # Check if we should activate trailing (after some profit)
            profit_pct = (current_price - self.entry_price) / self.entry_price
            if profit_pct > 0.10:  # Activate after 10% profit
                self.activated = True

            # Update trailing stop
            if self.activated:
                new_stop = current_price * (1 - self.trail_pct)
                if new_stop > self.current_stop:
                    old_stop = self.current_stop
                    self.current_stop = new_stop
                    logger.info(
                        f"📈 Trailing stop raised for {self.market_id}: "
                        f"${old_stop:.4f} → ${new_stop:.4f}"
                    )

        return (False, self.current_stop)

    def _update_short(self, current_price: float) -> Tuple[bool, float]:
        """Update for short position."""
        # Check if stop hit
        if current_price >= self.current_stop:
            logger.warning(
                f"🛑 Trailing stop HIT for {self.market_id}: "
                f"price ${current_price:.4f} >= stop ${self.current_stop:.4f}"
            )
            return (True, self.current_stop)

        # Update lowest price
        if current_price < self.lowest_price:
            self.lowest_price = current_price

            # Activate after profit
            profit_pct = (self.entry_price - current_price) / self.entry_price
            if profit_pct > 0.10:
                self.activated = True

            # Update trailing stop
            if self.activated:
                new_stop = current_price * (1 + self.trail_pct)
                if new_stop < self.current_stop:
                    old_stop = self.current_stop
                    self.current_stop = new_stop
                    logger.info(
                        f"📉 Trailing stop lowered for {self.market_id}: "
                        f"${old_stop:.4f} → ${new_stop:.4f}"
                    )

        return (False, self.current_stop)

    def get_unrealized_pnl(self, current_price: float) -> float:
        """Calculate unrealized P&L."""
        if self.side == "long":
            return self.size * (current_price - self.entry_price)
        else:
            return self.size * (self.entry_price - current_price)

    def get_stats(self) -> Dict[str, Any]:
        """Get stop statistics."""
        return {
            "market_id": self.market_id,
            "side": self.side,
            "entry_price": self.entry_price,
            "current_stop": self.current_stop,
            "highest_price": self.highest_price if self.side == "long" else None,
            "lowest_price": self.lowest_price if self.side == "short" else None,
            "trail_pct": self.trail_pct,
            "activated": self.activated,
        }


# =============================================================================
# POSITION CORRELATION
# =============================================================================

# Keywords that indicate correlated markets
CORRELATION_GROUPS = {
    "trump": ["trump", "republican", "gop", "maga", "rnc"],
    "biden": ["biden", "democrat", "democratic", "dnc", "harris", "kamala"],
    "bitcoin": ["bitcoin", "btc", "crypto", "cryptocurrency", "ethereum", "eth"],
    "fed": ["fed", "federal reserve", "interest rate", "inflation", "fomc", "powell"],
    "election": ["election", "vote", "ballot", "polls", "electoral"],
    "ai": ["ai", "artificial intelligence", "openai", "chatgpt", "anthropic", "google ai"],
    "tech": ["apple", "google", "microsoft", "amazon", "meta", "nvidia"],
    "sports_nfl": ["nfl", "super bowl", "football", "chiefs", "eagles", "49ers"],
    "sports_nba": ["nba", "basketball", "lakers", "celtics", "finals"],
}


class CorrelationWarning(BaseModel):
    """Warning about correlated positions."""

    group: str
    markets: List[str]
    total_exposure: float
    direction: str  # "same" or "mixed"
    risk_level: str  # "low", "medium", "high"
    message: str


def extract_keywords(text: str) -> Set[str]:
    """Extract keywords from market question."""
    text_lower = text.lower()
    words = set(re.findall(r"\b\w+\b", text_lower))
    return words


def find_correlation_group(question: str) -> Optional[str]:
    """Find which correlation group a market belongs to."""
    keywords = extract_keywords(question)

    for group, group_keywords in CORRELATION_GROUPS.items():
        if any(kw in keywords for kw in group_keywords):
            return group

    return None


class CorrelationDetector:
    """
    Detects correlated positions in a portfolio.

    Warns when you have multiple positions that are likely
    to move together (e.g., long on both "Trump wins" and "GOP Senate").

    Usage:
        detector = CorrelationDetector()
        warnings = detector.analyze_portfolio(positions)
        for warning in warnings:
            print(warning.message)
    """

    def __init__(self, exposure_threshold: float = 100.0):
        """
        Initialize detector.

        Args:
            exposure_threshold: Warn if correlated exposure exceeds this
        """
        self.exposure_threshold = exposure_threshold

    def analyze_portfolio(
        self,
        positions: List[Dict[str, Any]],
    ) -> List[CorrelationWarning]:
        """
        Analyze portfolio for correlated positions.

        Args:
            positions: List of position dicts with keys:
                - market_id: str
                - question: str
                - size: float
                - side: str ("long" or "short")
                - value: float (position value in USD)

        Returns:
            List of correlation warnings
        """
        warnings = []

        # Group positions by correlation group
        groups: Dict[str, List[Dict]] = {}

        for pos in positions:
            group = find_correlation_group(pos.get("question", ""))
            if group:
                if group not in groups:
                    groups[group] = []
                groups[group].append(pos)

        # Analyze each group
        for group, group_positions in groups.items():
            if len(group_positions) < 2:
                continue

            # Calculate total exposure and direction
            total_exposure = sum(abs(p.get("value", 0)) for p in group_positions)
            long_count = sum(1 for p in group_positions if p.get("side") == "long")
            short_count = len(group_positions) - long_count

            # Determine direction
            if long_count == len(group_positions):
                direction = "same"
                direction_desc = "all LONG"
            elif short_count == len(group_positions):
                direction = "same"
                direction_desc = "all SHORT"
            else:
                direction = "mixed"
                direction_desc = f"{long_count} LONG, {short_count} SHORT"

            # Determine risk level
            if direction == "same" and total_exposure > self.exposure_threshold * 2:
                risk_level = "high"
            elif direction == "same" and total_exposure > self.exposure_threshold:
                risk_level = "medium"
            elif total_exposure > self.exposure_threshold:
                risk_level = "low"
            else:
                continue  # Skip low exposure

            # Build warning
            market_questions = [
                p.get("question", p.get("market_id", "?"))[:50] for p in group_positions
            ]

            warning = CorrelationWarning(
                group=group,
                markets=market_questions,
                total_exposure=total_exposure,
                direction=direction,
                risk_level=risk_level,
                message=(
                    f"⚠️ CORRELATED POSITIONS ({risk_level.upper()}): "
                    f"You have {len(group_positions)} positions in '{group}' markets "
                    f"({direction_desc}) with ${total_exposure:.2f} total exposure. "
                    f"These are likely to move together!"
                ),
            )
            warnings.append(warning)

            logger.warning(warning.message)

        return warnings

    def get_correlation_matrix(
        self,
        positions: List[Dict[str, Any]],
    ) -> Dict[str, Dict[str, float]]:
        """
        Build correlation matrix for positions.

        Returns:
            Dict mapping market_id to dict of correlated market_ids and scores
        """
        matrix = {}

        for i, pos1 in enumerate(positions):
            id1 = pos1.get("market_id", str(i))
            q1 = pos1.get("question", "")
            group1 = find_correlation_group(q1)

            matrix[id1] = {}

            for j, pos2 in enumerate(positions):
                if i == j:
                    continue

                id2 = pos2.get("market_id", str(j))
                q2 = pos2.get("question", "")
                group2 = find_correlation_group(q2)

                # Same group = correlated
                if group1 and group1 == group2:
                    matrix[id1][id2] = 0.8  # High correlation
                else:
                    # Check keyword overlap
                    kw1 = extract_keywords(q1)
                    kw2 = extract_keywords(q2)
                    overlap = len(kw1 & kw2)
                    if overlap > 2:
                        matrix[id1][id2] = min(0.5, overlap * 0.1)

        return matrix


# =============================================================================
# POSITION MANAGER
# =============================================================================


class PositionManager:
    """
    Comprehensive position management.

    Combines trailing stops, correlation detection, and position tracking.

    Usage:
        manager = PositionManager()

        # Open position with trailing stop
        manager.open_position(
            market_id="abc123",
            question="Will Trump win 2024?",
            entry_price=0.45,
            size=100,
            side="long",
            enable_trailing_stop=True,
        )

        # Update with current prices
        actions = manager.update_prices({"abc123": 0.52})

        # Check for correlations
        warnings = manager.check_correlations()
    """

    def __init__(
        self,
        default_trail_pct: float = 0.15,
        default_stop_pct: float = 0.20,
        correlation_threshold: float = 100.0,
    ):
        """
        Initialize position manager.

        Args:
            default_trail_pct: Default trailing stop percentage
            default_stop_pct: Default initial stop percentage
            correlation_threshold: Warn if correlated exposure exceeds this
        """
        self.default_trail_pct = default_trail_pct
        self.default_stop_pct = default_stop_pct

        # Position tracking
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.trailing_stops: Dict[str, TrailingStop] = {}

        # Correlation detector
        self.correlation_detector = CorrelationDetector(exposure_threshold=correlation_threshold)

        logger.info(
            f"PositionManager initialized "
            f"(trail: {default_trail_pct:.0%}, stop: {default_stop_pct:.0%})"
        )

    def open_position(
        self,
        market_id: str,
        question: str,
        entry_price: float,
        size: float,
        side: str = "long",
        enable_trailing_stop: bool = True,
        trail_pct: Optional[float] = None,
        stop_pct: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Open a new position with optional trailing stop.

        Args:
            market_id: Market identifier
            question: Market question
            entry_price: Entry price
            size: Position size in shares
            side: "long" or "short"
            enable_trailing_stop: Enable trailing stop
            trail_pct: Custom trailing stop %
            stop_pct: Custom initial stop %

        Returns:
            Position info dict
        """
        position = {
            "market_id": market_id,
            "question": question,
            "entry_price": entry_price,
            "current_price": entry_price,
            "size": size,
            "side": side,
            "value": size * entry_price,
            "unrealized_pnl": 0.0,
            "opened_at": datetime.now(),
            "has_trailing_stop": enable_trailing_stop,
        }

        self.positions[market_id] = position

        # Setup trailing stop
        if enable_trailing_stop:
            self.trailing_stops[market_id] = TrailingStop(
                market_id=market_id,
                entry_price=entry_price,
                size=size,
                side=side,
                trail_pct=trail_pct or self.default_trail_pct,
                initial_stop_pct=stop_pct or self.default_stop_pct,
            )
            logger.info(
                f"📍 Position opened: {side.upper()} {size:.2f} shares of {market_id} "
                f"@ ${entry_price:.4f} with trailing stop"
            )
        else:
            logger.info(
                f"📍 Position opened: {side.upper()} {size:.2f} shares of {market_id} "
                f"@ ${entry_price:.4f}"
            )

        # Check correlations with new position
        warnings = self.check_correlations()
        if warnings:
            for w in warnings:
                if market_id in str(w.markets):
                    logger.warning(f"New position may be correlated: {w.message}")

        return position

    def close_position(self, market_id: str, exit_price: float) -> Optional[Dict[str, Any]]:
        """
        Close a position.

        Args:
            market_id: Market identifier
            exit_price: Exit price

        Returns:
            Closed position info with realized P&L
        """
        if market_id not in self.positions:
            logger.warning(f"Position not found: {market_id}")
            return None

        position = self.positions[market_id]

        # Calculate realized P&L
        if position["side"] == "long":
            realized_pnl = position["size"] * (exit_price - position["entry_price"])
        else:
            realized_pnl = position["size"] * (position["entry_price"] - exit_price)

        position["exit_price"] = exit_price
        position["realized_pnl"] = realized_pnl
        position["closed_at"] = datetime.now()

        # Remove from tracking
        del self.positions[market_id]
        if market_id in self.trailing_stops:
            del self.trailing_stops[market_id]

        logger.info(
            f"📤 Position closed: {market_id} @ ${exit_price:.4f} " f"(P&L: ${realized_pnl:+.2f})"
        )

        return position

    def update_prices(
        self,
        prices: Dict[str, float],
    ) -> List[Dict[str, Any]]:
        """
        Update positions with current prices.

        Args:
            prices: Dict mapping market_id to current price

        Returns:
            List of actions to take (e.g., close positions)
        """
        actions = []

        for market_id, current_price in prices.items():
            if market_id not in self.positions:
                continue

            position = self.positions[market_id]
            position["current_price"] = current_price

            # Update unrealized P&L
            if position["side"] == "long":
                position["unrealized_pnl"] = position["size"] * (
                    current_price - position["entry_price"]
                )
            else:
                position["unrealized_pnl"] = position["size"] * (
                    position["entry_price"] - current_price
                )

            position["value"] = position["size"] * current_price

            # Check trailing stop
            if market_id in self.trailing_stops:
                stop = self.trailing_stops[market_id]
                should_exit, stop_level = stop.update(current_price)

                if should_exit:
                    actions.append(
                        {
                            "action": "close",
                            "market_id": market_id,
                            "reason": "trailing_stop",
                            "stop_level": stop_level,
                            "current_price": current_price,
                            "unrealized_pnl": position["unrealized_pnl"],
                        }
                    )

        return actions

    def check_correlations(self) -> List[CorrelationWarning]:
        """Check portfolio for correlated positions."""
        position_list = list(self.positions.values())
        return self.correlation_detector.analyze_portfolio(position_list)

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary."""
        total_value = sum(p["value"] for p in self.positions.values())
        total_pnl = sum(p["unrealized_pnl"] for p in self.positions.values())

        long_positions = [p for p in self.positions.values() if p["side"] == "long"]
        short_positions = [p for p in self.positions.values() if p["side"] == "short"]

        return {
            "num_positions": len(self.positions),
            "total_value": total_value,
            "unrealized_pnl": total_pnl,
            "long_count": len(long_positions),
            "short_count": len(short_positions),
            "long_value": sum(p["value"] for p in long_positions),
            "short_value": sum(p["value"] for p in short_positions),
            "positions": list(self.positions.values()),
            "trailing_stops": {mid: stop.get_stats() for mid, stop in self.trailing_stops.items()},
        }

    def get_position(self, market_id: str) -> Optional[Dict[str, Any]]:
        """Get position by market ID."""
        return self.positions.get(market_id)

    def get_all_positions(self) -> List[Dict[str, Any]]:
        """Get all positions."""
        return list(self.positions.values())

    def format_for_prompt(self) -> str:
        """Format portfolio for AI agent prompt."""
        if not self.positions:
            return "No open positions."

        lines = [
            "📊 CURRENT POSITIONS:",
            "",
        ]

        for pos in self.positions.values():
            pnl_str = f"${pos['unrealized_pnl']:+.2f}"
            cost_basis = pos["size"] * pos["entry_price"]
            pnl_pct = (pos["unrealized_pnl"] / cost_basis * 100) if cost_basis > 0 else 0.0

            stop_info = ""
            if pos["market_id"] in self.trailing_stops:
                stop = self.trailing_stops[pos["market_id"]]
                stop_info = f" [Stop: ${stop.current_stop:.4f}]"

            lines.append(
                f"  • {pos['side'].upper()} {pos['size']:.1f} @ ${pos['entry_price']:.4f} "
                f"→ ${pos['current_price']:.4f} ({pnl_str}, {pnl_pct:+.1f}%){stop_info}"
            )
            lines.append(f"    {pos['question'][:60]}...")

        # Check correlations
        warnings = self.check_correlations()
        if warnings:
            lines.append("")
            lines.append("⚠️ CORRELATION WARNINGS:")
            for w in warnings:
                lines.append(f"  • {w.message}")

        return "\n".join(lines)
