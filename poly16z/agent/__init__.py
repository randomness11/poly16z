"""AI Agent framework."""

from poly16z.agent.base import BaseAgent
from poly16z.agent.anthropic_agent import AnthropicAgent
from poly16z.agent.ensemble import EnsembleAgent, VotingStrategy

# Optional AI providers
try:
    from poly16z.agent.gemini_agent import GeminiAgent
except ImportError:
    GeminiAgent = None

try:
    from poly16z.agent.openai_agent import OpenAIAgent
except ImportError:
    OpenAIAgent = None

try:
    from poly16z.agent.mock_agent import MockAgent
except ImportError:
    MockAgent = None

__all__ = ["BaseAgent", "AnthropicAgent", "GeminiAgent", "OpenAIAgent", "EnsembleAgent", "VotingStrategy", "MockAgent"]

