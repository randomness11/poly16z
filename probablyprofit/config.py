"""
Configuration Management for ProbablyProfit

Handles loading, saving, and validating configuration from multiple sources:
1. ~/.probablyprofit/config.yaml (user config)
2. .env file (local project config)
3. Environment variables (runtime overrides)
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from dotenv import load_dotenv

# Config directory
CONFIG_DIR = Path.home() / ".probablyprofit"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.yaml"


@dataclass
class AIProvider:
    """Configuration for an AI provider."""

    name: str
    api_key: Optional[str] = None
    model: str = ""
    available: bool = False


@dataclass
class WalletConfig:
    """Wallet configuration."""

    private_key: Optional[str] = None
    platform: str = "polymarket"  # polymarket or kalshi


@dataclass
class APIConfig:
    """API and network configuration."""

    # Timeouts (seconds)
    http_timeout: float = 30.0
    websocket_timeout: float = 60.0

    # Rate limiting
    polymarket_rate_limit_calls: int = 8
    polymarket_rate_limit_period: float = 1.0

    # Circuit breaker
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0

    # Retry logic
    retry_max_attempts: int = 3
    retry_base_delay: float = 2.0
    retry_max_delay: float = 30.0

    # Cache settings
    market_cache_ttl: float = 60.0
    market_cache_max_size: int = 1000
    price_cache_ttl: float = 10.0
    positions_cache_max_size: int = 200


@dataclass
class AgentConfig:
    """Agent loop configuration."""

    # Loop settings
    default_loop_interval: int = 60
    max_consecutive_errors: int = 10
    base_backoff: float = 5.0
    max_backoff: float = 300.0

    # Memory limits
    memory_max_observations: int = 100
    memory_max_decisions: int = 100
    memory_max_trades: int = 100

    # Checkpointing
    checkpoint_interval: int = 5  # loops
    risk_save_interval: int = 10  # loops


@dataclass
class RiskConfig:
    """Risk management configuration."""

    # Position limits
    max_position_pct: float = 0.10
    max_single_trade: float = 50.0
    max_daily_loss_pct: float = 0.20
    max_total_exposure_pct: float = 0.50

    # Sizing
    kelly_fraction: float = 0.25
    min_confidence_to_trade: float = 0.6

    # Stop loss / Take profit
    default_stop_loss_pct: float = 0.20
    default_take_profit_pct: float = 0.50


@dataclass
class Config:
    """Main configuration object."""

    # AI Providers
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-sonnet-4-5-20250929"
    google_api_key: Optional[str] = None
    google_model: str = "gemini-2.0-flash"

    # Wallet
    private_key: Optional[str] = None
    platform: str = "polymarket"

    # Trading
    initial_capital: float = 1000.0
    dry_run: bool = True  # Default to safe mode
    interval: int = 60

    # Intelligence
    perplexity_api_key: Optional[str] = None
    twitter_bearer_token: Optional[str] = None

    # Risk
    max_position_size: float = 50.0
    max_daily_loss: float = 100.0

    # State
    is_configured: bool = False
    preferred_agent: str = "auto"  # auto, openai, anthropic, google

    # Sub-configs (initialized with defaults)
    api: APIConfig = field(default_factory=APIConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)

    def get_available_agents(self) -> List[str]:
        """Get list of configured AI providers."""
        agents = []
        if self.openai_api_key:
            agents.append("openai")
        if self.anthropic_api_key:
            agents.append("anthropic")
        if self.google_api_key:
            agents.append("google")
        return agents

    def get_best_agent(self) -> Optional[str]:
        """Get the best available agent (user preference or first available)."""
        available = self.get_available_agents()
        if not available:
            return None
        if self.preferred_agent != "auto" and self.preferred_agent in available:
            return self.preferred_agent
        # Preference order: anthropic > openai > google
        for agent in ["anthropic", "openai", "google"]:
            if agent in available:
                return agent
        return available[0] if available else None

    def get_api_key_for_agent(self, agent: str) -> Optional[str]:
        """Get API key for a specific agent."""
        mapping = {
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
            "google": self.google_api_key,
        }
        return mapping.get(agent)

    def get_model_for_agent(self, agent: str) -> str:
        """Get model name for a specific agent."""
        mapping = {
            "openai": self.openai_model,
            "anthropic": self.anthropic_model,
            "google": self.google_model,
        }
        return mapping.get(agent, "")

    def has_wallet(self) -> bool:
        """Check if wallet is configured."""
        return bool(self.private_key)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for saving."""
        return {
            "ai": {
                "preferred_agent": self.preferred_agent,
                "openai_model": self.openai_model,
                "anthropic_model": self.anthropic_model,
                "google_model": self.google_model,
            },
            "trading": {
                "platform": self.platform,
                "initial_capital": self.initial_capital,
                "dry_run": self.dry_run,
                "interval": self.interval,
            },
            "risk": {
                "max_position_size": self.max_position_size,
                "max_daily_loss": self.max_daily_loss,
                "max_position_pct": self.risk.max_position_pct,
                "max_daily_loss_pct": self.risk.max_daily_loss_pct,
                "kelly_fraction": self.risk.kelly_fraction,
            },
            "api": {
                "http_timeout": self.api.http_timeout,
                "rate_limit_calls": self.api.polymarket_rate_limit_calls,
                "rate_limit_period": self.api.polymarket_rate_limit_period,
                "circuit_breaker_threshold": self.api.circuit_breaker_threshold,
                "retry_max_attempts": self.api.retry_max_attempts,
            },
            "agent": {
                "loop_interval": self.agent.default_loop_interval,
                "max_consecutive_errors": self.agent.max_consecutive_errors,
                "checkpoint_interval": self.agent.checkpoint_interval,
            },
        }

    def credentials_to_dict(self) -> Dict[str, Any]:
        """Get credentials as dictionary (stored separately for security)."""
        creds = {}
        if self.openai_api_key:
            creds["openai_api_key"] = self.openai_api_key
        if self.anthropic_api_key:
            creds["anthropic_api_key"] = self.anthropic_api_key
        if self.google_api_key:
            creds["google_api_key"] = self.google_api_key
        if self.private_key:
            creds["private_key"] = self.private_key
        if self.perplexity_api_key:
            creds["perplexity_api_key"] = self.perplexity_api_key
        if self.twitter_bearer_token:
            creds["twitter_bearer_token"] = self.twitter_bearer_token
        return creds


def ensure_config_dir() -> Path:
    """Ensure config directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR


# Global config singleton
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global config singleton, loading if necessary."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reset_config() -> None:
    """Reset the global config singleton (useful for testing)."""
    global _config
    _config = None


def load_config() -> Config:
    """
    Load configuration from all sources.

    Priority (highest to lowest):
    1. Environment variables
    2. .env file in current directory
    3. ~/.probablyprofit/credentials.yaml
    4. ~/.probablyprofit/config.yaml
    """
    config = Config()

    # Load from user config files
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                data = yaml.safe_load(f) or {}

            # AI settings
            ai = data.get("ai", {})
            config.preferred_agent = ai.get("preferred_agent", "auto")
            config.openai_model = ai.get("openai_model", config.openai_model)
            config.anthropic_model = ai.get("anthropic_model", config.anthropic_model)
            config.google_model = ai.get("google_model", config.google_model)

            # Trading settings
            trading = data.get("trading", {})
            config.platform = trading.get("platform", config.platform)
            config.initial_capital = trading.get("initial_capital", config.initial_capital)
            config.dry_run = trading.get("dry_run", config.dry_run)
            config.interval = trading.get("interval", config.interval)

            # Risk settings (top-level)
            risk = data.get("risk", {})
            config.max_position_size = risk.get("max_position_size", config.max_position_size)
            config.max_daily_loss = risk.get("max_daily_loss", config.max_daily_loss)

            # Risk sub-config
            config.risk.max_position_pct = risk.get(
                "max_position_pct", config.risk.max_position_pct
            )
            config.risk.max_single_trade = risk.get(
                "max_single_trade", config.risk.max_single_trade
            )
            config.risk.max_daily_loss_pct = risk.get(
                "max_daily_loss_pct", config.risk.max_daily_loss_pct
            )
            config.risk.max_total_exposure_pct = risk.get(
                "max_total_exposure_pct", config.risk.max_total_exposure_pct
            )
            config.risk.kelly_fraction = risk.get("kelly_fraction", config.risk.kelly_fraction)
            config.risk.min_confidence_to_trade = risk.get(
                "min_confidence_to_trade", config.risk.min_confidence_to_trade
            )
            config.risk.default_stop_loss_pct = risk.get(
                "default_stop_loss_pct", config.risk.default_stop_loss_pct
            )
            config.risk.default_take_profit_pct = risk.get(
                "default_take_profit_pct", config.risk.default_take_profit_pct
            )

            # API settings
            api = data.get("api", {})
            config.api.http_timeout = api.get("http_timeout", config.api.http_timeout)
            config.api.websocket_timeout = api.get(
                "websocket_timeout", config.api.websocket_timeout
            )
            config.api.polymarket_rate_limit_calls = api.get(
                "rate_limit_calls", config.api.polymarket_rate_limit_calls
            )
            config.api.polymarket_rate_limit_period = api.get(
                "rate_limit_period", config.api.polymarket_rate_limit_period
            )
            config.api.circuit_breaker_threshold = api.get(
                "circuit_breaker_threshold", config.api.circuit_breaker_threshold
            )
            config.api.circuit_breaker_timeout = api.get(
                "circuit_breaker_timeout", config.api.circuit_breaker_timeout
            )
            config.api.retry_max_attempts = api.get(
                "retry_max_attempts", config.api.retry_max_attempts
            )
            config.api.retry_base_delay = api.get("retry_base_delay", config.api.retry_base_delay)
            config.api.retry_max_delay = api.get("retry_max_delay", config.api.retry_max_delay)
            config.api.market_cache_ttl = api.get("market_cache_ttl", config.api.market_cache_ttl)
            config.api.market_cache_max_size = api.get(
                "market_cache_max_size", config.api.market_cache_max_size
            )
            config.api.price_cache_ttl = api.get("price_cache_ttl", config.api.price_cache_ttl)
            config.api.positions_cache_max_size = api.get(
                "positions_cache_max_size", config.api.positions_cache_max_size
            )

            # Agent settings
            agent = data.get("agent", {})
            config.agent.default_loop_interval = agent.get(
                "loop_interval", config.agent.default_loop_interval
            )
            config.agent.max_consecutive_errors = agent.get(
                "max_consecutive_errors", config.agent.max_consecutive_errors
            )
            config.agent.base_backoff = agent.get("base_backoff", config.agent.base_backoff)
            config.agent.max_backoff = agent.get("max_backoff", config.agent.max_backoff)
            config.agent.memory_max_observations = agent.get(
                "memory_max_observations", config.agent.memory_max_observations
            )
            config.agent.memory_max_decisions = agent.get(
                "memory_max_decisions", config.agent.memory_max_decisions
            )
            config.agent.memory_max_trades = agent.get(
                "memory_max_trades", config.agent.memory_max_trades
            )
            config.agent.checkpoint_interval = agent.get(
                "checkpoint_interval", config.agent.checkpoint_interval
            )
            config.agent.risk_save_interval = agent.get(
                "risk_save_interval", config.agent.risk_save_interval
            )

        except Exception:
            pass

    # Load credentials from secure file
    if CREDENTIALS_FILE.exists():
        try:
            with open(CREDENTIALS_FILE) as f:
                creds = yaml.safe_load(f) or {}

            config.openai_api_key = creds.get("openai_api_key")
            config.anthropic_api_key = creds.get("anthropic_api_key")
            config.google_api_key = creds.get("google_api_key")
            config.private_key = creds.get("private_key")
            config.perplexity_api_key = creds.get("perplexity_api_key")
            config.twitter_bearer_token = creds.get("twitter_bearer_token")
        except Exception:
            pass

    # Load from .env file (overrides config files)
    load_dotenv()

    # Environment variables override everything
    config.openai_api_key = os.getenv("OPENAI_API_KEY", config.openai_api_key)
    config.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", config.anthropic_api_key)
    config.google_api_key = os.getenv("GOOGLE_API_KEY", config.google_api_key)
    config.private_key = os.getenv("PRIVATE_KEY", config.private_key)
    config.perplexity_api_key = os.getenv("PERPLEXITY_API_KEY", config.perplexity_api_key)
    config.twitter_bearer_token = os.getenv("TWITTER_BEARER_TOKEN", config.twitter_bearer_token)

    if os.getenv("INITIAL_CAPITAL"):
        config.initial_capital = float(os.getenv("INITIAL_CAPITAL"))
    if os.getenv("PLATFORM"):
        config.platform = os.getenv("PLATFORM")

    # Determine if configured
    config.is_configured = len(config.get_available_agents()) > 0

    return config


def save_config(config: Config) -> None:
    """Save configuration to user config files."""
    ensure_config_dir()

    # Save non-sensitive config
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config.to_dict(), f, default_flow_style=False)

    # Save credentials with restricted permissions
    creds = config.credentials_to_dict()
    if creds:
        with open(CREDENTIALS_FILE, "w") as f:
            yaml.dump(creds, f, default_flow_style=False)
        # Restrict permissions on credentials file
        os.chmod(CREDENTIALS_FILE, 0o600)


def validate_api_key(provider: str, key: str) -> bool:
    """
    Validate an API key by making a simple request.
    Returns True if valid, False otherwise.
    """
    if not key:
        return False

    try:
        if provider == "openai":
            import openai

            client = openai.OpenAI(api_key=key)
            # Simple models list call to validate
            client.models.list()
            return True

        elif provider == "anthropic":
            import anthropic

            client = anthropic.Anthropic(api_key=key)
            # Count tokens is a lightweight validation call
            client.count_tokens("test")
            return True

        elif provider == "google":
            import google.generativeai as genai

            genai.configure(api_key=key)
            # List models to validate
            list(genai.list_models())
            return True

    except Exception:
        return False

    return False


def get_quick_status() -> Dict[str, Any]:
    """Get a quick status summary of the configuration."""
    config = load_config()

    return {
        "configured": config.is_configured,
        "agents": config.get_available_agents(),
        "best_agent": config.get_best_agent(),
        "wallet": config.has_wallet(),
        "platform": config.platform,
        "dry_run": config.dry_run,
    }
