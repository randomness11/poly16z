# [±] ProbablyProfit

<div align="center">

### Your hedge fund. One prompt away.

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776ab?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](https://opensource.org/licenses/MIT)
[![Twitter](https://img.shields.io/badge/Twitter-@ankitkr0-1da1f2?style=flat-square&logo=twitter&logoColor=white)](https://twitter.com/ankitkr0)

</div>

---

```
You are an elite prediction market trader.

Find markets where the crowd is wrong. Buy YES when price is 20%+ below
true probability. Buy NO when price is 20%+ above. Size bets using Kelly
criterion. Never risk more than 5% per trade. Exit at 2x or cut losses at -30%.

Avoid: politics you don't understand, markets < $5k volume, coin flips.
```

**That's it.** That's your entire trading bot.

One prompt. Claude reads 500+ markets. Finds mispriced bets. Executes trades. Manages risk. 24/7.

```bash
pip install probablyprofit
probablyprofit run -s strategy.txt --live
```

**You just mass-deployed a AI trader squad to prediction markets.**

---

## What People Don't Get

Everyone's building AI wrappers. We built the trading terminal.

- **Polymarket** → $2B+ volume prediction market on crypto rails
- **Kalshi** → Regulated US exchange, real USD
- **ProbablyProfit** → The AI layer that trades both

You describe your edge in English. The AI handles everything else:
- Scans hundreds of markets in seconds
- Calculates expected value using reasoning
- Sizes positions with Kelly criterion
- Executes via CLOB (limit orders, not AMM slippage)
- Tracks P&L, manages risk, never sleeps

**This isn't a toy.** This is the infrastructure for AI-native trading.

---

## The Stack

```
┌─────────────────────────────────────────────────────────────┐
│                      YOUR STRATEGY                          │
│         "Buy undervalued YES on election markets"           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    AI DECISION ENGINE                        │
│                                                              │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐                │
│   │ Claude  │    │  GPT-4  │    │ Gemini  │   ← Pick one   │
│   └─────────┘    └─────────┘    └─────────┘     or all     │
│                        ↓                                     │
│              [Ensemble Mode: 2/3 consensus]                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    RISK MANAGEMENT                           │
│                                                              │
│   Kelly Sizing │ Position Limits │ Stop Loss │ Take Profit  │
│   Max Drawdown │ Correlation Checks │ Exposure Caps         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   ORDER MANAGEMENT                           │
│                                                              │
│   Order Lifecycle │ Fill Tracking │ Partial Fills           │
│   Cancel/Modify │ Reconciliation │ Event Callbacks          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────┐         ┌────────────────────────────┐
│     POLYMARKET       │         │          KALSHI            │
│   Crypto / Global    │         │     Regulated / US         │
│   ETH Settlement     │         │     USD Settlement         │
└──────────────────────┘         └────────────────────────────┘
```

---

## 60-Second Setup

```bash
# Install
pip install probablyprofit[full]

# Configure (interactive)
probablyprofit setup

# Paper trade first (virtual money)
probablyprofit run "Buy YES under 0.30 on high-volume markets" --paper

# Go live when ready
probablyprofit run -s my_strategy.txt --live
```

---

## Real Example: Value Strategy

Save this as `value.txt`:

```
You are a value investor for prediction markets.

EDGE: Markets are inefficient. Crowds overreact to news and
underreact to base rates. Find the gap.

BUY YES when:
- Your estimated probability is 20%+ higher than market price
- Resolution criteria is unambiguous
- Volume > $10,000 (liquidity matters)
- Time to resolution > 7 days (avoid last-minute chaos)

BUY NO when:
- Market is 20%+ overpriced vs your estimate
- Same liquidity/clarity requirements

POSITION SIZING:
- Base: $20 per trade
- High conviction (30%+ edge): $50
- Maximum 5 concurrent positions
- Never more than 20% of bankroll at risk

EXIT RULES:
- Take profit at 2x
- Stop loss at -30%
- Close 24 hours before resolution

AVOID:
- Markets you don't deeply understand
- Prices between 0.40-0.60 (coin flips)
- Celebrity/meme markets (unpredictable)
- Anything with ambiguous resolution
```

Run it:

```bash
probablyprofit run -s value.txt --paper
```

Watch it scan markets, reason about probabilities, and execute trades.

---

## Python API

For builders who want full control:

```python
import asyncio
from probablyprofit import (
    PolymarketClient,
    AnthropicAgent,
    RiskManager,
    OrderManager
)

async def main():
    # Setup clients
    client = PolymarketClient(private_key="0x...")
    risk = RiskManager(
        initial_capital=1000.0,
        max_position_size=50.0,
        max_drawdown=0.20  # Stop at 20% loss
    )
    orders = OrderManager(client=client)

    # Create AI agent
    agent = AnthropicAgent(
        client=client,
        risk_manager=risk,
        order_manager=orders,
        strategy_prompt=open("value.txt").read()
    )

    # Register callbacks
    orders.on_fill = lambda order, fill: print(f"Filled: {fill.size}@{fill.price}")
    orders.on_complete = lambda order: print(f"Order complete: {order.order_id}")

    # Run forever
    await agent.run_loop()

asyncio.run(main())
```

---

## Features

| Feature | What It Does |
|---------|--------------|
| **Plain English Strategies** | No code. Describe your edge like you'd explain to a friend. |
| **Multi-AI Support** | Claude, GPT-4, Gemini. Or ensemble mode for consensus. |
| **Order Management** | Full lifecycle: submit → partial fills → complete. Callbacks for everything. |
| **Risk Engine** | Kelly sizing, position limits, stop-loss, take-profit, max drawdown. |
| **Dual Platform** | Polymarket (crypto, global) + Kalshi (regulated, US). Same interface. |
| **Paper Trading** | Test strategies with virtual money before risking real capital. |
| **Backtesting** | Simulate on historical data to validate your edge. |
| **WebSocket Feeds** | Real-time price streams for reactive strategies. |
| **Web Dashboard** | Monitor positions, P&L, and agent decisions in your browser. |
| **Persistence** | SQLite storage for trades, decisions, and performance metrics. |

---

## Strategy Ideas

### Arbitrage Hunter
```
Find price discrepancies between related markets.
If "Trump wins" is 0.45 and "Biden wins" is 0.58, something's wrong.
The two should sum to ~1.00. Trade the gap.
```

### News Reactor
```
You have mass knowledge. You'll find news that market hasn't reacted to.
When you find significant news affecting a market's outcome:
- Verify the source
- Estimate probability shift
- Enter within 5 minutes
- Size based on edge magnitude
```

### Contrarian
```
When markets move 20%+ in a day on no real news, fade the move.
Crowds overreact. Reversion is your edge.
Wait for the spike. Enter against it. Exit when price normalizes.
```

### Base Rate Specialist
```
Focus on categories where you know historical base rates.
Elections: incumbents win X% of the time.
Sports: home teams win Y% of the time.
Find markets where price diverges significantly from base rate.
```

---

## CLI Reference

```bash
# Core commands
probablyprofit setup                    # Interactive configuration
probablyprofit run "strategy" --paper   # Paper trading
probablyprofit run -s file.txt --live   # Live trading
probablyprofit run --dry-run "..."      # Analyze only (no trades)

# Market data
probablyprofit markets                  # List active markets
probablyprofit markets -q "trump"       # Search markets
probablyprofit market <id>              # Market details

# Portfolio
probablyprofit balance                  # Check wallet
probablyprofit positions                # View open positions
probablyprofit orders                   # View orders
probablyprofit history                  # Trade history

# Tools
probablyprofit backtest -s strat.txt    # Backtest strategy
probablyprofit dashboard                # Launch web UI
```

---

## Configuration

### Environment Variables

```bash
# AI Providers (pick one or more)
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...
export GOOGLE_API_KEY=...

# Polymarket (Ethereum wallet)
export POLYMARKET_PRIVATE_KEY=0x...

# Kalshi (API credentials)
export KALSHI_API_KEY=...
export KALSHI_PRIVATE_KEY_PATH=/path/to/key.pem
```

### Config File

```yaml
# ~/.probablyprofit/config.yaml

agent:
  default_model: claude-sonnet-4-20250514
  loop_interval: 300  # seconds between scans

risk:
  initial_capital: 1000.0
  max_position_size: 50.0
  max_total_exposure: 0.5
  max_drawdown: 0.20

platforms:
  polymarket:
    enabled: true
  kalshi:
    enabled: false
```

---

## Platforms

| Platform | Type | Region | Settlement | Auth |
|----------|------|--------|------------|------|
| [Polymarket](https://polymarket.com) | Crypto | Global* | USDC on Polygon | Ethereum wallet |
| [Kalshi](https://kalshi.com) | Regulated | US only | USD | RSA key pair |

*Polymarket blocks US IPs but doesn't KYC. Use at your own risk.

---

## Why This Exists

Prediction markets are the most efficient information aggregation mechanism ever created. They're also massively inefficient in practice:

- **Information asymmetry**: You know things the crowd doesn't
- **Behavioral biases**: Crowds overreact to news, underreact to base rates
- **Liquidity gaps**: Small markets are mispriced because nobody's watching
- **Speed**: News moves faster than markets update

AI changes the game. It can:
- Read and reason about hundreds of markets simultaneously
- Apply your edge consistently without emotion
- Execute 24/7 without fatigue
- Learn from outcomes (coming soon)

**ProbablyProfit is the interface between your insight and the market.**

---

## Disclaimer

**This is experimental software. Use at your own risk.**

- Trading involves risk of total loss
- Past performance doesn't predict future results
- AI can and will make mistakes
- Only trade money you can afford to lose
- The authors are not responsible for any losses
- This is not financial advice

---

## Contributing

PRs welcome. See [CONTRIBUTING.md](probablyprofit/CONTRIBUTING.md)

Key areas:
- New AI provider integrations
- Additional exchange support
- Strategy templates
- Risk management improvements
- Documentation

---

## License

MIT License - see [LICENSE](LICENSE)

---

<div align="center">

Built by [@ankitkr0](https://twitter.com/ankitkr0)

**You give it a strategy. It gives you edge.**

**[± ProbablyProfit](https://randomness11.github.io/probablyprofit/)**

</div>
