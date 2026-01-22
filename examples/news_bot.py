"""
News-Driven Bot Example

Trades based on breaking news and events using Perplexity for news context.
"""

import asyncio
import os

from dotenv import load_dotenv

from probablyprofit import AnthropicAgent, PolymarketClient, RiskManager
from probablyprofit.sources import PerplexityClient

# Load environment variables
load_dotenv()

# Strategy prompt for the AI agent
NEWS_STRATEGY = """
You are a news-driven trading bot for Polymarket prediction markets.

Your strategy:
1. Monitor breaking news and major events
2. Identify markets that will be affected by the news
3. Trade quickly before the market fully adjusts
4. Look for markets where news creates mispricings

Entry rules:
- Enter when significant news breaks that affects a market
- News should be from credible sources
- Market should not have fully priced in the news yet
- Position size: 5-8% of capital for high-confidence news plays
- Move quickly but verify the news is legitimate

Exit rules:
- Take profit once market adjusts to news (usually 20-40% gain)
- Exit if news is contradicted or turns out to be false
- Hold if news impact is sustained and ongoing
- Stop loss at 20% if you misread the news impact

Risk management:
- Verify news from multiple sources before trading
- Be aware of "fake news" and misinformation
- Larger positions for major, verified news
- Smaller positions for developing/unconfirmed stories
- Maximum 4 open positions

When analyzing markets and news:
- How reliable is the news source?
- How directly does this impact the market outcome?
- Has the market already priced this in?
- Is there a time advantage (are you early)?
- What's the expected magnitude of impact?

Speed matters, but accuracy matters more.
"""


async def main():
    """Run the news-driven bot."""
    # Initialize Polymarket client
    client = PolymarketClient(
        private_key=os.getenv("PRIVATE_KEY"),
    )

    # Initialize news client (Perplexity)
    perplexity_key = os.getenv("PERPLEXITY_API_KEY")
    news_client = PerplexityClient(api_key=perplexity_key) if perplexity_key else None

    # Initialize risk manager
    risk_manager = RiskManager(
        initial_capital=float(os.getenv("INITIAL_CAPITAL", "1000")),
    )

    # Initialize AI agent
    agent = AnthropicAgent(
        client=client,
        risk_manager=risk_manager,
        strategy_prompt=NEWS_STRATEGY,
    )

    # Run the agent
    print("🚀 Starting News-Driven Bot...")
    print("📊 Strategy: News-driven trading")
    print("⏱️  Loop interval: 3 minutes")
    print("💰 Initial capital: ${}".format(os.getenv("INITIAL_CAPITAL", "1000")))
    if news_client:
        print("📰 News source: Perplexity API")
    else:
        print("⚠️  No PERPLEXITY_API_KEY - news context disabled")
    print("\nPress Ctrl+C to stop\n")

    try:
        await agent.run()
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping bot...")
        await client.close()

    # Print final stats
    print("\n📈 Final Statistics:")
    stats = risk_manager.get_stats()
    print(f"  Capital: ${stats['current_capital']:.2f}")
    print(f"  Total P&L: ${stats['total_pnl']:+.2f}")
    print(f"  Return: {stats['return_pct']:+.2%}")
    print(f"  Total Trades: {stats['total_trades']}")
    print(f"  Win Rate: {stats['win_rate']:.1%}")


if __name__ == "__main__":
    asyncio.run(main())
