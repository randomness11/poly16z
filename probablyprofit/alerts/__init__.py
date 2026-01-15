"""
Alerting System for ProbablyProfit

Provides real-time alerts via various channels:
- Telegram (primary)
- Future: Discord, Slack, Email
"""

from probablyprofit.alerts.telegram import AlertLevel, TelegramAlerter, get_alerter

__all__ = ["TelegramAlerter", "AlertLevel", "get_alerter"]
