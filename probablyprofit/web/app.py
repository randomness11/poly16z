"""
FastAPI Application

Main FastAPI app for the probablyprofit dashboard.
"""

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from probablyprofit.agent.base import BaseAgent
from probablyprofit.web.api.routes import router as api_router
from probablyprofit.web.api.websocket import websocket_endpoint

# Path to React build
STATIC_DIR = Path(__file__).parent / "static"


@dataclass
class AgentState:
    """Global agent state for web access."""

    agent: BaseAgent
    agent_type: str
    strategy_name: str
    start_time: datetime

    @property
    def uptime_seconds(self) -> float:
        return (datetime.now() - self.start_time).total_seconds()


# Global agent state
_agent_state: Optional[AgentState] = None


def create_app() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title="probablyprofit Dashboard API",
        description="Real-time trading bot monitoring and control",
        version="1.0.0",
    )

    # CORS middleware for React frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",  # Vite dev server
            "http://localhost:3000",  # Create React App
            "http://localhost:8000",  # Same origin
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routes
    app.include_router(api_router)

    # WebSocket endpoint
    app.add_websocket_route("/ws", websocket_endpoint)

    # Serve React app if built, otherwise fallback to simple HTML
    if STATIC_DIR.exists() and (STATIC_DIR / "index.html").exists():
        # Mount static assets
        app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

        @app.get("/", response_class=HTMLResponse)
        async def dashboard():
            """Serve the React dashboard."""
            return FileResponse(STATIC_DIR / "index.html")

        @app.get("/{path:path}")
        async def catch_all(path: str):
            """Catch-all for React Router - serve index.html for unknown routes."""
            # Don't catch API routes
            if path.startswith("api/") or path.startswith("ws"):
                return {"error": "Not found"}
            # Check if it's a static file
            file_path = STATIC_DIR / path
            if file_path.exists() and file_path.is_file():
                return FileResponse(file_path)
            # Return React app for client-side routing
            return FileResponse(STATIC_DIR / "index.html")

    else:
        # Fallback to simple HTML dashboard
        @app.get("/", response_class=HTMLResponse)
        async def dashboard():
            """Serve the simple dashboard UI."""
            from probablyprofit.web.dashboard import DASHBOARD_HTML

            return DASHBOARD_HTML

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    return app


def set_agent_state(agent: BaseAgent, agent_type: str, strategy_name: str):
    """Set global agent state for web access."""
    global _agent_state
    _agent_state = AgentState(
        agent=agent,
        agent_type=agent_type,
        strategy_name=strategy_name,
        start_time=datetime.now(),
    )


def get_agent_state() -> Optional[AgentState]:
    """Get global agent state."""
    return _agent_state
