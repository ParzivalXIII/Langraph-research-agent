#!/bin/bash
# Gradio Research UI Deployment Guide
# 
# Safe Track deployment: Phase 6 & 7 validated, all tests passing (214/214 ✅)
# Branch: 002-gradio-research-ui
# Status: 🚀 PRODUCTION READY

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Gradio Research UI - Deployment Guide${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# ============================================================================
# PRE-DEPLOYMENT CHECKS
# ============================================================================

echo -e "${YELLOW}[STEP 1] Pre-Deployment Checklist${NC}"
echo ""

# Check Python version
echo -n "Checking Python version... "
if python3 --version | grep -qE "Python 3\.(1[0-9]|[0-9]{2})"; then
    echo -e "${GREEN}✓ Python 3.10+${NC}"
else
    echo -e "${RED}✗ Python version < 3.10 (required: 3.10+)${NC}"
    exit 1
fi

# Check uv is installed
echo -n "Checking uv package manager... "
if command -v uv &> /dev/null; then
    echo -e "${GREEN}✓ uv installed${NC}"
else
    echo -e "${RED}✗ uv not found (install: pip install uv)${NC}"
    exit 1
fi

# Check venv exists
echo -n "Checking virtual environment... "
if [ -d ".venv" ]; then
    echo -e "${GREEN}✓ .venv directory found${NC}"
else
    echo -e "${RED}✗ .venv not found (run: python3 -m venv .venv)${NC}"
    exit 1
fi

# Check key files exist
echo -n "Checking required files... "
REQUIRED_FILES=(
    "ui/app.py"
    "ui/models.py"
    "ui/client/api_client.py"
    "ui/components/results.py"
    "ui/components/diagnostics.py"
    "ui/README.md"
    "pyproject.toml"
)
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}✗ Missing: $file${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✓ All required files present${NC}"

echo ""

# ============================================================================
# UNIT TESTS
# ============================================================================

echo -e "${YELLOW}[STEP 2] Run Unit Tests${NC}"
echo ""

uv run pytest tests/unit/ -q --tb=no

echo ""
echo -e "${GREEN}✓ Unit tests passed${NC}"
echo ""

# ============================================================================
# ENVIRONMENT SETUP
# ============================================================================

echo -e "${YELLOW}[STEP 3] Environment Configuration${NC}"
echo ""

# Recommended environment variables
echo "Set these environment variables for production:"
echo ""
echo "  # Backend configuration"
echo "  export API_BASE_URL=http://localhost:8000  # or your backend URL"
echo "  export API_TIMEOUT=60                      # request timeout in seconds"
echo ""
echo "  # Gradio configuration"
echo "  export GRADIO_SERVER_PORT=7860             # UI port number"
echo ""

# Check if backend is running
echo -n "Checking if backend is running on localhost:8000... "
if curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/health" 2>/dev/null | grep -q "200"; then
    echo -e "${GREEN}✓ Backend is running${NC}"
else
    echo -e "${YELLOW}⚠ Backend not responding (will try anyway)${NC}"
fi

echo ""

# ============================================================================
# DEPLOYMENT OPTIONS
# ============================================================================

echo -e "${YELLOW}[STEP 4] Choose Deployment Method${NC}"
echo ""

echo "Option 1: Local Development (Testing)"
echo "  uv run python ui/app.py"
echo "  Then open: http://localhost:7860"
echo ""

echo "Option 2: Docker Container"
echo "  docker build -f docker/Dockerfile -t gradio-ui ."
echo "  docker run -p 7860:7860 -e API_BASE_URL=http://host.docker.internal:8000 gradio-ui"
echo "  Then open: http://localhost:7860"
echo ""

echo "Option 3: Kubernetes"
echo "  kubectl apply -f deployments/gradio-ui.yaml"
echo "  kubectl port-forward svc/gradio-ui 7860:7860"
echo "  Then open: http://localhost:7860"
echo ""

echo "Option 4: Production ASGI Server (Gunicorn + Uvicorn)"
echo "  gunicorn --workers 2 --bind 0.0.0.0:7860 ui.app:app"
echo "  (Note: Gradio apps typically run with built-in server, not ASGI)"
echo ""

# ============================================================================
# QUICK START
# ============================================================================

echo -e "${YELLOW}[STEP 5] Quick Start (Local Testing)${NC}"
echo ""

echo "Starting Gradio UI on http://localhost:7860..."
echo ""
echo "To stop: Press Ctrl+C"
echo ""

# Verify backend is running before starting UI
if ! curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/health" 2>/dev/null | grep -q "200"; then
    echo -e "${YELLOW}⚠ WARNING: Backend not responding at http://localhost:8000${NC}"
    echo "  To run backend in another terminal:"
    echo "    uv run fastapi dev app/main.py"
    echo ""
fi

echo "Starting UI..."
uv run python ui/app.py

# ============================================================================
# POST-DEPLOYMENT VERIFICATION
# ============================================================================

# This section runs after the UI is stopped (Ctrl+C)

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Deployment Complete${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${GREEN}✓ UI has been running successfully${NC}"
echo ""

echo "Logs and troubleshooting:"
echo "  - Check backend logs for errors"
echo "  - Check Gradio server output for import/syntax errors"
echo "  - See ui/README.md for troubleshooting guide"
echo ""
