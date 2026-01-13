"""
Tests for the Polymarket API client.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from probablyprofit.api.client import Market, Order, PolymarketClient, Position
from probablyprofit.api.exceptions import ValidationException


@pytest.fixture
def client():
    """Create a mock client without real credentials (read-only mode)."""
    return PolymarketClient()  # No private key = read-only mode


class TestMarketDataclass:
    def test_market_creation(self):
        market = Market(
            condition_id="0x123",
            question="Will it rain tomorrow?",
            end_date=datetime(2024, 12, 31),
            outcomes=["Yes", "No"],
            outcome_prices=[0.65, 0.35],
            volume=10000.0,
            liquidity=5000.0,
        )
        assert market.condition_id == "0x123"
        assert market.question == "Will it rain tomorrow?"
        assert market.outcomes == ["Yes", "No"]
        assert market.active is True


class TestOrderDataclass:
    def test_order_creation(self):
        order = Order(market_id="0x123", outcome="Yes", side="BUY", size=100.0, price=0.5)
        assert order.market_id == "0x123"
        assert order.status == "pending"
        assert order.filled_size == 0.0


class TestPositionDataclass:
    def test_position_value(self):
        position = Position(
            market_id="0x123", outcome="Yes", size=100.0, avg_price=0.5, current_price=0.7
        )
        assert position.value == pytest.approx(70.0)  # 100 * 0.7
        assert position.unrealized_pnl == pytest.approx(20.0)  # (0.7 - 0.5) * 100


class TestPolymarketClient:
    @pytest.mark.asyncio
    async def test_get_balance_returns_float(self, client):
        """Test that get_balance returns a float (0.0 in read-only mode)."""
        # In read-only mode (no credentials), balance returns 0.0
        balance = await client.get_balance()
        assert isinstance(balance, float)
        assert balance == 0.0  # No credentials = 0.0

    @pytest.mark.asyncio
    async def test_close_client(self, client):
        """Test that close doesn't raise."""
        await client.close()  # Should not raise


class TestValidation:
    def test_price_validation(self):
        """Prices must be between 0 and 1."""
        from probablyprofit.utils.validators import validate_price

        assert validate_price(0.5) == 0.5

        with pytest.raises(ValidationException):
            validate_price(1.5)

        with pytest.raises(ValidationException):
            validate_price(-0.1)

    def test_side_validation(self):
        """Side must be BUY or SELL."""
        from probablyprofit.utils.validators import validate_side

        assert validate_side("BUY") == "BUY"
        assert validate_side("SELL") == "SELL"

        with pytest.raises(ValidationException):
            validate_side("HOLD")
