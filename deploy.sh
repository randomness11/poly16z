#!/bin/bash
# =============================================================================
# probablyprofit Deployment Script
# =============================================================================
# Usage:
#   ./deploy.sh              # Deploy in dry-run mode (default)
#   ./deploy.sh paper        # Deploy in paper trading mode
#   ./deploy.sh live         # Deploy in live trading mode (REAL MONEY)
#   ./deploy.sh ensemble     # Deploy with multiple AI providers
#   ./deploy.sh backtest     # Run backtesting simulation
#   ./deploy.sh local        # Run locally without Docker
#   ./deploy.sh stop         # Stop all services
#   ./deploy.sh logs         # View logs
#   ./deploy.sh build        # Build only (no run)
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check for .env file
check_env() {
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}Warning: .env file not found!${NC}"
        echo "Creating .env from .env.example..."
        cp probablyprofit/.env.example .env
        echo -e "${YELLOW}Please edit .env with your API keys before continuing.${NC}"
        exit 1
    fi
}

# Build React frontend
build_frontend() {
    echo -e "${BLUE}Building React frontend...${NC}"
    if [ -d "frontend" ]; then
        cd frontend
        npm ci --silent
        npm run build
        cd ..
        echo -e "${GREEN}Frontend built successfully!${NC}"
    else
        echo -e "${YELLOW}Frontend directory not found, skipping...${NC}"
    fi
}

# Build Docker image
build_docker() {
    echo -e "${BLUE}Building Docker image...${NC}"
    docker compose -f probablyprofit/docker-compose.yml build
    echo -e "${GREEN}Docker image built successfully!${NC}"
}

# Deploy functions
deploy_dry_run() {
    check_env
    echo -e "${BLUE}Deploying in DRY-RUN mode (no real trades)...${NC}"
    docker compose -f probablyprofit/docker-compose.yml up -d probablyprofit
    echo -e "${GREEN}Deployed! Dashboard: http://localhost:8000${NC}"
}

deploy_paper() {
    check_env
    echo -e "${BLUE}Deploying in PAPER TRADING mode (virtual money)...${NC}"
    docker compose -f probablyprofit/docker-compose.yml --profile paper up -d probablyprofit-paper
    echo -e "${GREEN}Deployed! Dashboard: http://localhost:8001${NC}"
}

deploy_live() {
    check_env
    echo -e "${RED}==================================================${NC}"
    echo -e "${RED}  WARNING: LIVE TRADING MODE - REAL MONEY AT RISK${NC}"
    echo -e "${RED}==================================================${NC}"
    read -p "Are you sure you want to deploy with real money? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Aborted."
        exit 0
    fi
    echo -e "${YELLOW}Deploying in LIVE TRADING mode...${NC}"
    docker compose -f probablyprofit/docker-compose.yml --profile live up -d probablyprofit-live
    echo -e "${GREEN}Deployed! Dashboard: http://localhost:8000${NC}"
}

deploy_ensemble() {
    check_env
    echo -e "${BLUE}Deploying in ENSEMBLE mode (multiple AI providers)...${NC}"
    docker compose -f probablyprofit/docker-compose.yml --profile ensemble up -d probablyprofit-ensemble
    echo -e "${GREEN}Deployed! Dashboard: http://localhost:8000${NC}"
}

run_backtest() {
    check_env
    echo -e "${BLUE}Running BACKTEST simulation...${NC}"
    docker compose -f probablyprofit/docker-compose.yml --profile backtest run --rm probablyprofit-backtest
}

run_local() {
    check_env
    echo -e "${BLUE}Running locally (no Docker)...${NC}"

    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Python 3 not found. Please install Python 3.11+${NC}"
        exit 1
    fi

    # Create virtual environment if needed
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi

    # Activate and install deps
    source venv/bin/activate
    pip install -q -r requirements.txt

    # Build frontend if needed
    if [ ! -d "probablyprofit/web/static" ]; then
        build_frontend
    fi

    # Run
    echo -e "${GREEN}Starting probablyprofit...${NC}"
    python -m probablyprofit.main --dry-run "$@"
}

stop_services() {
    echo -e "${BLUE}Stopping all services...${NC}"
    docker compose -f probablyprofit/docker-compose.yml --profile paper --profile live --profile ensemble down
    echo -e "${GREEN}All services stopped.${NC}"
}

show_logs() {
    echo -e "${BLUE}Showing logs (Ctrl+C to exit)...${NC}"
    docker compose -f probablyprofit/docker-compose.yml logs -f
}

# Main
case "${1:-}" in
    paper)
        deploy_paper
        ;;
    live)
        deploy_live
        ;;
    ensemble)
        deploy_ensemble
        ;;
    backtest)
        run_backtest
        ;;
    local)
        shift
        run_local "$@"
        ;;
    stop)
        stop_services
        ;;
    logs)
        show_logs
        ;;
    build)
        build_docker
        ;;
    frontend)
        build_frontend
        ;;
    *)
        deploy_dry_run
        ;;
esac
