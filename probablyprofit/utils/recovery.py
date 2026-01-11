"""
Recovery utilities for probablyprofit.

Provides state checkpointing and crash recovery to ensure
the bot can resume after unexpected failures.
"""

import json
import os
import asyncio
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from loguru import logger


@dataclass
class AgentCheckpoint:
    """Checkpoint of agent state for recovery."""

    agent_name: str
    timestamp: str
    running: bool
    loop_count: int

    # Last known state
    last_balance: float
    last_observation_time: Optional[str]
    last_decision_time: Optional[str]
    last_action: Optional[str]

    # Pending work
    pending_decisions: List[Dict[str, Any]]

    # Stats
    total_trades: int
    successful_trades: int
    failed_trades: int

    # Error tracking
    last_error: Optional[str]
    error_count: int
    consecutive_errors: int

    # Config snapshot
    dry_run: bool
    loop_interval: int
    sizing_method: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentCheckpoint":
        return cls(**data)


class RecoveryManager:
    """
    Manages agent state persistence and crash recovery.

    Periodically saves agent state to disk so the bot can
    resume from where it left off after a crash.

    Usage:
        recovery = RecoveryManager("/path/to/checkpoints")

        # In agent loop
        await recovery.checkpoint(agent)

        # On startup
        state = await recovery.load_latest(agent_name)
        if state:
            agent.restore_from_checkpoint(state)
    """

    def __init__(
        self,
        checkpoint_dir: str = ".probablyprofit/checkpoints",
        max_checkpoints: int = 10,
        checkpoint_interval: int = 5,  # Save every N loops
    ):
        """
        Initialize recovery manager.

        Args:
            checkpoint_dir: Directory to store checkpoints
            max_checkpoints: Maximum checkpoints to keep per agent
            checkpoint_interval: Save checkpoint every N loop iterations
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.max_checkpoints = max_checkpoints
        self.checkpoint_interval = checkpoint_interval

        # Ensure checkpoint directory exists
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Track loop counts for interval-based checkpointing
        self._loop_counts: Dict[str, int] = {}

        logger.info(f"[Recovery] Initialized with checkpoint dir: {self.checkpoint_dir}")

    def _get_checkpoint_path(self, agent_name: str, timestamp: Optional[str] = None) -> Path:
        """Get path for a checkpoint file."""
        if timestamp:
            filename = f"{agent_name}_{timestamp}.json"
        else:
            filename = f"{agent_name}_latest.json"
        return self.checkpoint_dir / filename

    def _get_agent_checkpoints(self, agent_name: str) -> List[Path]:
        """Get all checkpoint files for an agent, sorted by time (newest first)."""
        pattern = f"{agent_name}_*.json"
        checkpoints = list(self.checkpoint_dir.glob(pattern))
        # Sort by modification time, newest first
        checkpoints.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return checkpoints

    async def checkpoint(
        self,
        agent: Any,
        force: bool = False,
        error: Optional[Exception] = None,
    ) -> Optional[Path]:
        """
        Save agent state to checkpoint.

        Args:
            agent: Agent instance to checkpoint
            force: If True, save regardless of interval
            error: Optional error that triggered checkpoint

        Returns:
            Path to checkpoint file, or None if skipped
        """
        agent_name = getattr(agent, "name", "unknown")

        # Check interval
        self._loop_counts[agent_name] = self._loop_counts.get(agent_name, 0) + 1
        if not force and self._loop_counts[agent_name] % self.checkpoint_interval != 0:
            return None

        try:
            # Build checkpoint from agent state
            memory = getattr(agent, "memory", None)

            checkpoint = AgentCheckpoint(
                agent_name=agent_name,
                timestamp=datetime.now().isoformat(),
                running=getattr(agent, "running", False),
                loop_count=self._loop_counts[agent_name],

                last_balance=memory.observations[-1].balance if memory and memory.observations else 0.0,
                last_observation_time=(
                    memory.observations[-1].timestamp.isoformat()
                    if memory and memory.observations else None
                ),
                last_decision_time=(
                    memory.decisions[-1].metadata.get("timestamp")
                    if memory and memory.decisions else None
                ),
                last_action=(
                    memory.decisions[-1].action
                    if memory and memory.decisions else None
                ),

                pending_decisions=[],
                total_trades=len(memory.trades) if memory else 0,
                successful_trades=sum(
                    1 for t in (memory.trades if memory else [])
                    if t.status == "filled"
                ),
                failed_trades=sum(
                    1 for t in (memory.trades if memory else [])
                    if t.status == "failed"
                ),

                last_error=str(error) if error else None,
                error_count=getattr(agent, "_error_count", 0),
                consecutive_errors=getattr(agent, "_consecutive_errors", 0),

                dry_run=getattr(agent, "dry_run", False),
                loop_interval=getattr(agent, "loop_interval", 60),
                sizing_method=getattr(agent, "sizing_method", "manual"),
            )

            # Save checkpoint
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            checkpoint_path = self._get_checkpoint_path(agent_name, timestamp_str)

            with open(checkpoint_path, "w") as f:
                json.dump(checkpoint.to_dict(), f, indent=2, default=str)

            # Also save as "latest"
            latest_path = self._get_checkpoint_path(agent_name)
            with open(latest_path, "w") as f:
                json.dump(checkpoint.to_dict(), f, indent=2, default=str)

            logger.debug(f"[Recovery] Checkpoint saved: {checkpoint_path}")

            # Cleanup old checkpoints
            await self._cleanup_old_checkpoints(agent_name)

            return checkpoint_path

        except Exception as e:
            logger.error(f"[Recovery] Failed to save checkpoint: {e}")
            return None

    async def _cleanup_old_checkpoints(self, agent_name: str) -> None:
        """Remove old checkpoints beyond max_checkpoints limit."""
        checkpoints = self._get_agent_checkpoints(agent_name)

        # Keep latest symlink separate
        checkpoints = [p for p in checkpoints if "latest" not in p.name]

        if len(checkpoints) > self.max_checkpoints:
            for old_checkpoint in checkpoints[self.max_checkpoints:]:
                try:
                    old_checkpoint.unlink()
                    logger.debug(f"[Recovery] Removed old checkpoint: {old_checkpoint}")
                except Exception as e:
                    logger.warning(f"[Recovery] Failed to remove checkpoint: {e}")

    async def load_latest(self, agent_name: str) -> Optional[AgentCheckpoint]:
        """
        Load the most recent checkpoint for an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            AgentCheckpoint or None if no checkpoint exists
        """
        latest_path = self._get_checkpoint_path(agent_name)

        if not latest_path.exists():
            logger.info(f"[Recovery] No checkpoint found for '{agent_name}'")
            return None

        try:
            with open(latest_path) as f:
                data = json.load(f)

            checkpoint = AgentCheckpoint.from_dict(data)
            logger.info(
                f"[Recovery] Loaded checkpoint for '{agent_name}' "
                f"from {checkpoint.timestamp}"
            )
            return checkpoint

        except Exception as e:
            logger.error(f"[Recovery] Failed to load checkpoint: {e}")
            return None

    async def clear_checkpoints(self, agent_name: Optional[str] = None) -> int:
        """
        Clear checkpoints.

        Args:
            agent_name: Specific agent, or None for all

        Returns:
            Number of checkpoints removed
        """
        removed = 0

        if agent_name:
            checkpoints = self._get_agent_checkpoints(agent_name)
            checkpoints.append(self._get_checkpoint_path(agent_name))
        else:
            checkpoints = list(self.checkpoint_dir.glob("*.json"))

        for checkpoint in checkpoints:
            try:
                if checkpoint.exists():
                    checkpoint.unlink()
                    removed += 1
            except Exception:
                pass

        logger.info(f"[Recovery] Cleared {removed} checkpoints")
        return removed


class GracefulShutdown:
    """
    Handles graceful shutdown with state preservation.

    Usage:
        shutdown = GracefulShutdown(recovery_manager)
        shutdown.register_agent(agent)

        # Handles SIGINT/SIGTERM
        await shutdown.wait_for_shutdown()
    """

    def __init__(self, recovery_manager: RecoveryManager):
        self.recovery = recovery_manager
        self.agents: List[Any] = []
        self._shutdown_event = asyncio.Event()
        self._shutdown_requested = False

    def register_agent(self, agent: Any) -> None:
        """Register an agent for graceful shutdown."""
        self.agents.append(agent)

    async def shutdown(self, reason: str = "unknown") -> None:
        """
        Perform graceful shutdown.

        Args:
            reason: Reason for shutdown
        """
        if self._shutdown_requested:
            return

        self._shutdown_requested = True
        logger.info(f"[Shutdown] Graceful shutdown initiated: {reason}")

        # Stop all agents
        for agent in self.agents:
            try:
                logger.info(f"[Shutdown] Stopping agent '{agent.name}'...")
                agent.stop()

                # Save final checkpoint
                await self.recovery.checkpoint(agent, force=True)
                logger.info(f"[Shutdown] Saved final checkpoint for '{agent.name}'")

            except Exception as e:
                logger.error(f"[Shutdown] Error stopping agent: {e}")

        self._shutdown_event.set()
        logger.info("[Shutdown] Shutdown complete")

    async def wait_for_shutdown(self) -> None:
        """Wait until shutdown is requested."""
        await self._shutdown_event.wait()


# Global recovery manager instance
_recovery_manager: Optional[RecoveryManager] = None


def get_recovery_manager() -> RecoveryManager:
    """Get the global recovery manager instance."""
    global _recovery_manager
    if _recovery_manager is None:
        _recovery_manager = RecoveryManager()
    return _recovery_manager


def set_recovery_manager(manager: RecoveryManager) -> None:
    """Set the global recovery manager instance."""
    global _recovery_manager
    _recovery_manager = manager
