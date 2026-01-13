"""
Fallback Agent

Wraps multiple AI agents and automatically falls back to the next
if one fails. Ensures your bot keeps running even when APIs go down.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Type

from loguru import logger

from probablyprofit.agent.base import BaseAgent, Decision, Observation
from probablyprofit.api.client import PolymarketClient
from probablyprofit.api.exceptions import AgentException
from probablyprofit.risk.manager import RiskManager


@dataclass
class AgentHealth:
    """Tracks health status of an agent."""

    name: str
    failures: int = 0
    successes: int = 0
    last_failure: Optional[datetime] = None
    last_success: Optional[datetime] = None
    is_healthy: bool = True
    cooldown_until: Optional[datetime] = None

    # Config
    failure_threshold: int = 3  # Failures before marking unhealthy
    cooldown_duration: int = 300  # Seconds to wait before retrying unhealthy agent

    def record_success(self) -> None:
        """Record a successful decision."""
        self.successes += 1
        self.last_success = datetime.now()
        self.failures = 0  # Reset failure count
        self.is_healthy = True
        self.cooldown_until = None

    def record_failure(self) -> None:
        """Record a failed decision."""
        self.failures += 1
        self.last_failure = datetime.now()

        if self.failures >= self.failure_threshold:
            self.is_healthy = False
            self.cooldown_until = datetime.now() + timedelta(seconds=self.cooldown_duration)
            logger.warning(
                f"[FallbackAgent] Agent '{self.name}' marked unhealthy after {self.failures} failures. "
                f"Cooldown until {self.cooldown_until}"
            )

    def check_cooldown(self) -> bool:
        """Check if cooldown has expired and agent should be retried."""
        if self.cooldown_until and datetime.now() >= self.cooldown_until:
            logger.info(f"[FallbackAgent] Agent '{self.name}' cooldown expired, marking healthy")
            self.is_healthy = True
            self.failures = 0
            self.cooldown_until = None
            return True
        return self.is_healthy


@dataclass
class FallbackConfig:
    """Configuration for fallback behavior."""

    # If True, always try primary agent first even if it recently failed
    always_try_primary: bool = True

    # Minimum confidence to accept a decision (otherwise try next agent)
    min_confidence: float = 0.0

    # Max time to wait for a single agent decision
    timeout_seconds: float = 60.0

    # Whether to log detailed fallback activity
    verbose: bool = True


class FallbackAgent(BaseAgent):
    """
    Agent that wraps multiple AI agents with automatic fallback.

    If the primary agent fails, it automatically tries the next agent
    in the chain. This ensures your bot keeps running even when
    OpenAI, Anthropic, or Google have outages.

    Usage:
        from probablyprofit.agent import OpenAIAgent, AnthropicAgent, GeminiAgent
        from probablyprofit.agent.fallback import FallbackAgent

        # Create individual agents
        openai = OpenAIAgent(client, risk_manager, api_key, strategy)
        claude = AnthropicAgent(client, risk_manager, api_key, strategy)
        gemini = GeminiAgent(client, risk_manager, api_key, strategy)

        # Wrap in fallback chain
        agent = FallbackAgent(
            client=client,
            risk_manager=risk_manager,
            agents=[openai, claude, gemini],  # Order matters - first is primary
            name="ResilientAgent"
        )

        await agent.run()
    """

    def __init__(
        self,
        client: PolymarketClient,
        risk_manager: RiskManager,
        agents: List[BaseAgent],
        name: str = "FallbackAgent",
        loop_interval: int = 60,
        strategy: Optional[Any] = None,
        dry_run: bool = False,
        config: Optional[FallbackConfig] = None,
    ):
        """
        Initialize fallback agent.

        Args:
            client: Polymarket API client
            risk_manager: Risk management system
            agents: List of agents in fallback order (first = primary)
            name: Agent name
            loop_interval: Seconds between loop iterations
            strategy: Optional strategy for filtering
            dry_run: If True, don't place real trades
            config: Fallback configuration
        """
        super().__init__(
            client=client,
            risk_manager=risk_manager,
            name=name,
            loop_interval=loop_interval,
            strategy=strategy,
            dry_run=dry_run,
        )

        if not agents:
            raise ValueError("FallbackAgent requires at least one agent")

        self.agents = agents
        self.config = config or FallbackConfig()

        # Initialize health tracking for each agent
        self.agent_health: Dict[str, AgentHealth] = {
            agent.name: AgentHealth(name=agent.name) for agent in agents
        }

        # Track which agent made the last decision
        self.last_decision_agent: Optional[str] = None

        # Stats
        self.fallback_count = 0
        self.total_decisions = 0

        agent_names = [a.name for a in agents]
        logger.info(f"[FallbackAgent] Initialized with {len(agents)} agents: {agent_names}")

    def _get_available_agents(self) -> List[BaseAgent]:
        """Get list of agents that are currently available (healthy or cooldown expired)."""
        available = []

        for agent in self.agents:
            health = self.agent_health[agent.name]

            # Check if cooldown expired
            health.check_cooldown()

            if health.is_healthy:
                available.append(agent)
            elif self.config.always_try_primary and agent == self.agents[0]:
                # Always include primary agent
                available.insert(0, agent)

        return available

    async def decide(self, observation: Observation) -> Decision:
        """
        Make a trading decision, falling back through agents on failure.

        Args:
            observation: Current market observation

        Returns:
            Decision from the first successful agent

        Raises:
            AgentException: If all agents fail
        """
        self.total_decisions += 1
        available_agents = self._get_available_agents()

        if not available_agents:
            logger.error("[FallbackAgent] No agents available!")
            # Reset all agents and try anyway
            for health in self.agent_health.values():
                health.is_healthy = True
                health.failures = 0
            available_agents = self.agents

        errors: List[tuple] = []  # (agent_name, error)

        for i, agent in enumerate(available_agents):
            health = self.agent_health[agent.name]
            is_fallback = i > 0

            if is_fallback:
                self.fallback_count += 1
                if self.config.verbose:
                    logger.warning(
                        f"[FallbackAgent] Falling back to '{agent.name}' "
                        f"(attempt {i + 1}/{len(available_agents)})"
                    )

            try:
                # Get decision from this agent
                decision = await agent.decide(observation)

                # Check minimum confidence
                if decision.confidence < self.config.min_confidence:
                    logger.warning(
                        f"[FallbackAgent] '{agent.name}' returned low confidence "
                        f"({decision.confidence:.2f} < {self.config.min_confidence}), trying next agent"
                    )
                    continue

                # Success!
                health.record_success()
                self.last_decision_agent = agent.name

                # Add metadata about which agent made the decision
                decision.metadata["fallback_agent"] = agent.name
                decision.metadata["was_fallback"] = is_fallback
                decision.metadata["fallback_attempt"] = i + 1

                if self.config.verbose:
                    logger.info(
                        f"[FallbackAgent] Decision from '{agent.name}': "
                        f"{decision.action} (confidence: {decision.confidence:.2f})"
                    )

                return decision

            except Exception as e:
                error_msg = str(e)
                errors.append((agent.name, error_msg))
                health.record_failure()

                logger.warning(f"[FallbackAgent] '{agent.name}' failed: {error_msg}")

                # Continue to next agent
                continue

        # All agents failed
        error_summary = "; ".join([f"{name}: {err}" for name, err in errors])
        logger.error(f"[FallbackAgent] All agents failed: {error_summary}")

        # Return a safe "hold" decision instead of crashing
        return Decision(
            action="hold",
            reasoning=f"All agents failed: {error_summary}",
            confidence=0.0,
            metadata={
                "all_agents_failed": True,
                "errors": dict(errors),
            },
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get fallback statistics."""
        return {
            "total_decisions": self.total_decisions,
            "fallback_count": self.fallback_count,
            "fallback_rate": self.fallback_count / max(1, self.total_decisions),
            "last_decision_agent": self.last_decision_agent,
            "agent_health": {
                name: {
                    "healthy": health.is_healthy,
                    "failures": health.failures,
                    "successes": health.successes,
                    "cooldown_until": str(health.cooldown_until) if health.cooldown_until else None,
                }
                for name, health in self.agent_health.items()
            },
        }

    def reset_health(self, agent_name: Optional[str] = None) -> None:
        """
        Reset health status for agents.

        Args:
            agent_name: Specific agent to reset, or None for all
        """
        if agent_name:
            if agent_name in self.agent_health:
                health = self.agent_health[agent_name]
                health.is_healthy = True
                health.failures = 0
                health.cooldown_until = None
                logger.info(f"[FallbackAgent] Reset health for '{agent_name}'")
        else:
            for health in self.agent_health.values():
                health.is_healthy = True
                health.failures = 0
                health.cooldown_until = None
            logger.info("[FallbackAgent] Reset health for all agents")


def create_fallback_agent(
    client: PolymarketClient,
    risk_manager: RiskManager,
    strategy_prompt: str,
    openai_key: Optional[str] = None,
    anthropic_key: Optional[str] = None,
    google_key: Optional[str] = None,
    dry_run: bool = False,
    **kwargs,
) -> FallbackAgent:
    """
    Convenience function to create a FallbackAgent with available API keys.

    Creates agents for each provided API key and wraps them in fallback order:
    1. OpenAI (GPT-4o)
    2. Anthropic (Claude)
    3. Google (Gemini)

    Args:
        client: Polymarket client
        risk_manager: Risk manager
        strategy_prompt: Trading strategy in plain English
        openai_key: OpenAI API key
        anthropic_key: Anthropic API key
        google_key: Google API key
        dry_run: If True, don't place real trades
        **kwargs: Additional args passed to FallbackAgent

    Returns:
        Configured FallbackAgent
    """
    agents = []

    if openai_key:
        try:
            from probablyprofit.agent.openai_agent import OpenAIAgent

            agents.append(
                OpenAIAgent(
                    client=client,
                    risk_manager=risk_manager,
                    openai_api_key=openai_key,
                    strategy_prompt=strategy_prompt,
                    name="OpenAI-GPT4o",
                    dry_run=dry_run,
                )
            )
            logger.info("[FallbackAgent] Added OpenAI agent to fallback chain")
        except Exception as e:
            logger.warning(f"[FallbackAgent] Could not create OpenAI agent: {e}")

    if anthropic_key:
        try:
            from probablyprofit.agent.anthropic_agent import AnthropicAgent

            agents.append(
                AnthropicAgent(
                    client=client,
                    risk_manager=risk_manager,
                    anthropic_api_key=anthropic_key,
                    strategy_prompt=strategy_prompt,
                    name="Anthropic-Claude",
                    dry_run=dry_run,
                )
            )
            logger.info("[FallbackAgent] Added Anthropic agent to fallback chain")
        except Exception as e:
            logger.warning(f"[FallbackAgent] Could not create Anthropic agent: {e}")

    if google_key:
        try:
            from probablyprofit.agent.gemini_agent import GeminiAgent

            agents.append(
                GeminiAgent(
                    client=client,
                    risk_manager=risk_manager,
                    google_api_key=google_key,
                    strategy_prompt=strategy_prompt,
                    name="Google-Gemini",
                    dry_run=dry_run,
                )
            )
            logger.info("[FallbackAgent] Added Gemini agent to fallback chain")
        except Exception as e:
            logger.warning(f"[FallbackAgent] Could not create Gemini agent: {e}")

    if not agents:
        raise ValueError("No agents could be created. Provide at least one valid API key.")

    return FallbackAgent(
        client=client,
        risk_manager=risk_manager,
        agents=agents,
        dry_run=dry_run,
        **kwargs,
    )
