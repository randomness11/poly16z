"""
Paper Trading Engine

Simulates trading without real money.
Tracks virtual positions, P&L, and trade history.
"""

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger
from pydantic import BaseModel, ConfigDict, Field, field_serializer


class PaperTrade(BaseModel):
    """Record of a paper trade."""

    model_config = ConfigDict(ser_json_timedelta="iso8601")

    trade_id: str
    timestamp: datetime
    market_id: str
    market_question: str
    side: str  # "yes" or "no"
    action: str  # "buy" or "sell"
    size: float
    price: float
    value: float  # size * price
    fees: float = 0.0

    @field_serializer("timestamp")
    def serialize_timestamp(self, v: datetime) -> str:
        return v.isoformat()


class PaperPosition(BaseModel):
    """A virtual position in a market."""

    model_config = ConfigDict(ser_json_timedelta="iso8601")

    market_id: str
    market_question: str
    side: str  # "yes" or "no"
    size: float
    avg_price: float
    current_price: float = 0.5
    opened_at: datetime = Field(default_factory=datetime.now)
    trades: List[str] = Field(default_factory=list)  # trade_ids

    @field_serializer("opened_at")
    def serialize_opened_at(self, v: datetime) -> str:
        return v.isoformat()

    @property
    def value(self) -> float:
        """Current position value."""
        return self.size * self.current_price

    @property
    def cost_basis(self) -> float:
        """Original cost of position."""
        return self.size * self.avg_price

    @property
    def unrealized_pnl(self) -> float:
        """Unrealized profit/loss."""
        return self.value - self.cost_basis

    @property
    def unrealized_pnl_pct(self) -> float:
        """Unrealized P&L as percentage."""
        if self.cost_basis == 0:
            return 0.0
        return (self.unrealized_pnl / self.cost_basis) * 100


class PaperPortfolio(BaseModel):
    """Complete paper trading portfolio state."""

    model_config = ConfigDict(ser_json_timedelta="iso8601")

    initial_capital: float = 1000.0
    cash: float = 1000.0
    positions: Dict[str, PaperPosition] = Field(default_factory=dict)
    trades: List[PaperTrade] = Field(default_factory=list)
    realized_pnl: float = 0.0
    total_fees: float = 0.0
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)

    @field_serializer("created_at", "last_updated")
    def serialize_datetime(self, v: datetime) -> str:
        return v.isoformat()

    @property
    def positions_value(self) -> float:
        """Total value of all positions."""
        return sum(p.value for p in self.positions.values())

    @property
    def total_value(self) -> float:
        """Total portfolio value (cash + positions)."""
        return self.cash + self.positions_value

    @property
    def total_return(self) -> float:
        """Total return in dollars."""
        return self.total_value - self.initial_capital

    @property
    def total_return_pct(self) -> float:
        """Total return as percentage."""
        if self.initial_capital == 0:
            return 0.0
        return (self.total_return / self.initial_capital) * 100

    @property
    def unrealized_pnl(self) -> float:
        """Total unrealized P&L."""
        return sum(p.unrealized_pnl for p in self.positions.values())


class PaperTradingEngine:
    """
    Paper trading simulation engine.

    Simulates order execution, tracks positions, and calculates P&L
    without using real money.

    Example:
        engine = PaperTradingEngine(initial_capital=1000)

        # Buy YES shares
        trade = engine.execute_trade(
            market_id="abc123",
            market_question="Will X happen?",
            side="yes",
            action="buy",
            size=100,
            price=0.45,
        )

        # Update prices and check P&L
        engine.update_price("abc123", 0.55)
        print(engine.get_portfolio_summary())
    """

    def __init__(
        self,
        initial_capital: float = 1000.0,
        fee_rate: float = 0.02,  # 2% fee
        persistence_path: Optional[str] = None,
    ):
        """
        Initialize paper trading engine.

        Args:
            initial_capital: Starting capital in USD
            fee_rate: Trading fee rate (0.02 = 2%)
            persistence_path: Path to save/load portfolio state
        """
        self.fee_rate = fee_rate
        self.persistence_path = persistence_path

        # Load existing portfolio or create new one
        if persistence_path and os.path.exists(persistence_path):
            self.portfolio = self._load_portfolio(persistence_path)
            logger.info(f"Loaded paper portfolio: ${self.portfolio.total_value:.2f}")
        else:
            self.portfolio = PaperPortfolio(
                initial_capital=initial_capital,
                cash=initial_capital,
            )
            logger.info(f"Created new paper portfolio: ${initial_capital:.2f}")

        self._trade_counter = len(self.portfolio.trades)

    def execute_trade(
        self,
        market_id: str,
        market_question: str,
        side: str,
        action: str,
        size: float,
        price: float,
    ) -> Optional[PaperTrade]:
        """
        Execute a paper trade.

        Args:
            market_id: Market identifier
            market_question: Market question text
            side: "yes" or "no"
            action: "buy" or "sell"
            size: Number of shares
            price: Price per share (0-1)

        Returns:
            PaperTrade record or None if failed
        """
        # Validate inputs
        if side.lower() not in ["yes", "no"]:
            logger.error(f"Invalid side: {side}")
            return None
        if action.lower() not in ["buy", "sell"]:
            logger.error(f"Invalid action: {action}")
            return None
        if not 0 < price < 1:
            logger.error(f"Invalid price: {price}")
            return None
        if size <= 0:
            logger.error(f"Invalid size: {size}")
            return None

        side = side.lower()
        action = action.lower()
        value = size * price
        fees = value * self.fee_rate

        # Check if we can afford the trade
        if action == "buy":
            total_cost = value + fees
            if total_cost > self.portfolio.cash:
                logger.warning(
                    f"Insufficient funds: need ${total_cost:.2f}, have ${self.portfolio.cash:.2f}"
                )
                return None

        # Check if we have position to sell
        position_key = f"{market_id}_{side}"
        if action == "sell":
            if position_key not in self.portfolio.positions:
                logger.warning(f"No position to sell: {position_key}")
                return None
            position = self.portfolio.positions[position_key]
            if position.size < size:
                logger.warning(
                    f"Insufficient position: have {position.size}, trying to sell {size}"
                )
                return None

        # Create trade record
        self._trade_counter += 1
        trade = PaperTrade(
            trade_id=f"paper_{self._trade_counter}",
            timestamp=datetime.now(),
            market_id=market_id,
            market_question=market_question,
            side=side,
            action=action,
            size=size,
            price=price,
            value=value,
            fees=fees,
        )

        # Execute the trade
        if action == "buy":
            self._execute_buy(trade, position_key)
        else:
            self._execute_sell(trade, position_key)

        # Record trade
        self.portfolio.trades.append(trade)
        self.portfolio.total_fees += fees
        self.portfolio.last_updated = datetime.now()

        # Persist if path set
        if self.persistence_path:
            self._save_portfolio()

        logger.info(
            f"📝 Paper trade: {action.upper()} {size:.2f} {side.upper()} @ ${price:.2f} "
            f"(value: ${value:.2f}, fees: ${fees:.2f})"
        )

        return trade

    def _execute_buy(self, trade: PaperTrade, position_key: str):
        """Execute a buy order."""
        total_cost = trade.value + trade.fees
        self.portfolio.cash -= total_cost

        if position_key in self.portfolio.positions:
            # Add to existing position
            position = self.portfolio.positions[position_key]
            total_size = position.size + trade.size
            total_cost_basis = (position.size * position.avg_price) + trade.value
            position.avg_price = total_cost_basis / total_size
            position.size = total_size
            position.trades.append(trade.trade_id)
        else:
            # Create new position
            self.portfolio.positions[position_key] = PaperPosition(
                market_id=trade.market_id,
                market_question=trade.market_question,
                side=trade.side,
                size=trade.size,
                avg_price=trade.price,
                current_price=trade.price,
                trades=[trade.trade_id],
            )

    def _execute_sell(self, trade: PaperTrade, position_key: str):
        """Execute a sell order."""
        position = self.portfolio.positions[position_key]

        # Calculate realized P&L
        cost_basis = trade.size * position.avg_price
        sale_proceeds = trade.value - trade.fees
        realized_pnl = sale_proceeds - cost_basis

        self.portfolio.cash += sale_proceeds
        self.portfolio.realized_pnl += realized_pnl

        # Update or remove position
        position.size -= trade.size
        position.trades.append(trade.trade_id)

        if position.size <= 0:
            del self.portfolio.positions[position_key]

        logger.info(f"Realized P&L: ${realized_pnl:+.2f}")

    def update_price(self, market_id: str, price: float, side: str = "yes"):
        """
        Update current price for a market.

        Args:
            market_id: Market identifier
            price: New price (0-1)
            side: Which side to update ("yes" or "no")
        """
        position_key = f"{market_id}_{side.lower()}"
        if position_key in self.portfolio.positions:
            self.portfolio.positions[position_key].current_price = price

        # Also update opposite side if exists
        opposite_side = "no" if side.lower() == "yes" else "yes"
        opposite_key = f"{market_id}_{opposite_side}"
        if opposite_key in self.portfolio.positions:
            self.portfolio.positions[opposite_key].current_price = 1 - price

    def update_prices_from_markets(self, markets: List[Any]):
        """
        Update prices from market data.

        Args:
            markets: List of Market objects with outcome_prices
        """
        for market in markets:
            market_id = getattr(market, "condition_id", None) or getattr(market, "ticker", None)
            if not market_id:
                continue

            prices = getattr(market, "outcome_prices", [0.5, 0.5])
            if prices:
                self.update_price(market_id, prices[0], "yes")

    def close_position(
        self,
        market_id: str,
        side: str,
        price: float,
    ) -> Optional[PaperTrade]:
        """
        Close an entire position.

        Args:
            market_id: Market identifier
            side: "yes" or "no"
            price: Current price to close at

        Returns:
            Closing trade or None if no position
        """
        position_key = f"{market_id}_{side.lower()}"
        if position_key not in self.portfolio.positions:
            return None

        position = self.portfolio.positions[position_key]
        return self.execute_trade(
            market_id=market_id,
            market_question=position.market_question,
            side=side,
            action="sell",
            size=position.size,
            price=price,
        )

    def get_position(self, market_id: str, side: str = "yes") -> Optional[PaperPosition]:
        """Get a specific position."""
        position_key = f"{market_id}_{side.lower()}"
        return self.portfolio.positions.get(position_key)

    def get_all_positions(self) -> List[PaperPosition]:
        """Get all open positions."""
        return list(self.portfolio.positions.values())

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary."""
        return {
            "initial_capital": self.portfolio.initial_capital,
            "cash": self.portfolio.cash,
            "positions_value": self.portfolio.positions_value,
            "total_value": self.portfolio.total_value,
            "total_return": self.portfolio.total_return,
            "total_return_pct": self.portfolio.total_return_pct,
            "realized_pnl": self.portfolio.realized_pnl,
            "unrealized_pnl": self.portfolio.unrealized_pnl,
            "total_fees": self.portfolio.total_fees,
            "positions_count": len(self.portfolio.positions),
            "trades_count": len(self.portfolio.trades),
        }

    def get_trade_history(self, limit: int = 50) -> List[PaperTrade]:
        """Get recent trade history."""
        return self.portfolio.trades[-limit:]

    def reset(self, initial_capital: Optional[float] = None):
        """Reset portfolio to initial state."""
        capital = initial_capital or self.portfolio.initial_capital
        self.portfolio = PaperPortfolio(
            initial_capital=capital,
            cash=capital,
        )
        self._trade_counter = 0
        logger.info(f"Paper portfolio reset to ${capital:.2f}")

        if self.persistence_path:
            self._save_portfolio()

    def _save_portfolio(self):
        """Save portfolio to disk."""
        if not self.persistence_path:
            return

        try:
            path = Path(self.persistence_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            data = self.portfolio.model_dump()
            with open(path, "w") as f:
                json.dump(data, f, indent=2, default=str)

            logger.debug(f"Saved paper portfolio to {path}")
        except Exception as e:
            logger.error(f"Failed to save portfolio: {e}")

    def _load_portfolio(self, path: str) -> PaperPortfolio:
        """Load portfolio from disk."""
        try:
            with open(path, "r") as f:
                data = json.load(f)

            # Reconstruct positions
            positions = {}
            for key, pos_data in data.get("positions", {}).items():
                positions[key] = PaperPosition(**pos_data)

            # Reconstruct trades
            trades = [PaperTrade(**t) for t in data.get("trades", [])]

            return PaperPortfolio(
                initial_capital=data.get("initial_capital", 1000.0),
                cash=data.get("cash", 1000.0),
                positions=positions,
                trades=trades,
                realized_pnl=data.get("realized_pnl", 0.0),
                total_fees=data.get("total_fees", 0.0),
            )
        except Exception as e:
            logger.error(f"Failed to load portfolio: {e}")
            return PaperPortfolio()

    def __repr__(self) -> str:
        summary = self.get_portfolio_summary()
        return (
            f"PaperTradingEngine("
            f"value=${summary['total_value']:.2f}, "
            f"return={summary['total_return_pct']:+.1f}%, "
            f"positions={summary['positions_count']}, "
            f"trades={summary['trades_count']})"
        )
