"""
poly16z Plugin System

Extensible plugin architecture for adding custom:
- Data sources
- Agents
- Strategies
- Risk rules
- Output handlers
"""

from poly16z.plugins.registry import PluginRegistry, PluginType
from poly16z.plugins.base import (
    BasePlugin,
    DataSourcePlugin,
    AgentPlugin,
    StrategyPlugin,
    RiskPlugin,
    OutputPlugin,
)
from poly16z.plugins.hooks import HookManager, Hook

# Global registry instance
registry = PluginRegistry()

__all__ = [
    "registry",
    "PluginRegistry",
    "PluginType",
    "BasePlugin",
    "DataSourcePlugin",
    "AgentPlugin", 
    "StrategyPlugin",
    "RiskPlugin",
    "OutputPlugin",
    "HookManager",
    "Hook",
]
