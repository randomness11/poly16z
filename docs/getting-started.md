# Getting Started with Polymarket AI Bot

This guide will get you up and running in 10 minutes.

## Prerequisites

- Python 3.10 or higher
- Polymarket account (optional for testing)
- Anthropic API key ([Get one here](https://console.anthropic.com))

## Step 1: Installation

```bash
# Navigate to the project directory
cd probablyprofit

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```bash
# Required - at least one AI provider
ANTHROPIC_API_KEY=sk-ant-...
# or OPENAI_API_KEY=sk-...
# or GOOGLE_API_KEY=...

# Optional (for live trading) - your Polygon wallet private key
PRIVATE_KEY=0x_your_private_key_here

# Optional (for news context)
PERPLEXITY_API_KEY=pplx-...
```

## Step 3: Run the Quickstart

Test that everything works:

```bash
python quickstart.py
```

This will:
1. Connect to Polymarket
2. Fetch current markets
3. Ask Claude to analyze them
4. Show you the AI's reasoning

## Step 4: Run an Example Bot

Try one of the three example strategies:

### Momentum Bot
```bash
python examples/momentum_bot.py
```

### Contrarian Bot
```bash
python examples/contrarian_bot.py
```

### News-Driven Bot
```bash
python examples/news_bot.py
```

## Step 5: Create Your Own Bot

Create a new file `my_bot.py`:

```python
import asyncio
import os
from dotenv import load_dotenv
from probablyprofit import AnthropicAgent, PolymarketClient, RiskManager

load_dotenv()

# Define your strategy in natural language!
MY_STRATEGY = """
You are a [YOUR STRATEGY HERE] trader.

Your strategy:
1. [STEP 1]
2. [STEP 2]

Entry rules:
- [RULE 1]
- [RULE 2]

Exit rules:
- Take profit at [X%]
- Stop loss at [Y%]
"""

async def main():
    client = PolymarketClient(
        private_key=os.getenv("PRIVATE_KEY"),
    )

    risk_manager = RiskManager(initial_capital=1000.0)

    agent = AnthropicAgent(
        client=client,
        risk_manager=risk_manager,
        strategy_prompt=MY_STRATEGY,
    )

    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:

```bash
python my_bot.py
```

## What's Next?

### 1. Learn Prompt Engineering

Read [strategy-guide.md](strategy-guide.md) to learn how to write effective trading strategies.

### 2. Explore the API

Check out [api-reference.md](api-reference.md) for detailed API documentation.

### 3. Backtest Your Strategy

Before risking real money, backtest via CLI:

```bash
probablyprofit backtest --strategy "your strategy" --days 30
```

Or check backtesting results in the web dashboard.

### 4. Use Paper Trading

Test with fake money first:

```bash
# Via CLI
probablyprofit run "your strategy" --paper --paper-capital 10000

# Or via Python
agent = AnthropicAgent(..., paper_trading=True)
```

### 5. Go Live (Carefully!)

When you're ready:

1. Start with small position sizes
2. Monitor closely for the first few days
3. Gradually increase capital as you gain confidence

## Common Issues

### "Missing API key"

Make sure `.env` has your `ANTHROPIC_API_KEY`.

### "Cannot place order"

If you get this error, it means you're running in read-only mode (no Polymarket credentials). This is fine for testing - the bot will still analyze markets, it just won't execute trades.

### "Rate limit exceeded"

You're making too many API calls. Increase `loop_interval` in your agent configuration.

## Safety Tips

⚠️ **Important**:

1. **Start small** - Use tiny position sizes initially
2. **Paper trade first** - Test thoroughly before using real money
3. **Monitor closely** - Check your bot frequently at first
4. **Set strict limits** - Use conservative risk management settings
5. **Understand the code** - Read through the framework before using it
6. **Only risk what you can afford to lose**

## Getting Help

- 📖 Read the docs in `docs/`
- 💬 Check GitHub issues
- 🐛 Report bugs on GitHub

## Summary

You now have:
- ✅ A working AI trading bot framework
- ✅ Three example strategies to learn from
- ✅ Tools to create your own custom bots
- ✅ Risk management and backtesting capabilities

The power is in the strategy prompt - experiment, test, and refine!

Happy trading! 🚀
