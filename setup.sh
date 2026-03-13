#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# setup.sh – one-command local setup for Linux / macOS
#
# Usage:
#   bash setup.sh
#
# What it does:
#   1. Checks that Python 3.11+ is available
#   2. Creates a virtual environment (.venv)
#   3. Installs all Python dependencies
#   4. Installs the Chromium browser used by Playwright
#   5. Copies .env.example → .env if .env doesn't exist yet
#   6. Starts the bot
# ---------------------------------------------------------------------------

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Colour

info()    { echo -e "${GREEN}[setup]${NC} $*"; }
warn()    { echo -e "${YELLOW}[setup]${NC} $*"; }
error()   { echo -e "${RED}[setup] ERROR:${NC} $*" >&2; }

# ---------------------------------------------------------------------------
# 1. Find a Python 3.11+ interpreter
# ---------------------------------------------------------------------------
PYTHON=""
for cmd in python3.13 python3.12 python3.11 python3 python; do
    if command -v "$cmd" &>/dev/null; then
        version=$("$cmd" -c 'import sys; print(sys.version_info[:2])')
        if "$cmd" -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)' 2>/dev/null; then
            PYTHON="$cmd"
            break
        fi
    fi
done

if [[ -z "$PYTHON" ]]; then
    error "Python 3.11 or newer is required but was not found."
    error "Install it from https://www.python.org/downloads/ and re-run this script."
    exit 1
fi

info "Using Python: $($PYTHON --version)"

# ---------------------------------------------------------------------------
# 2. Create virtual environment
# ---------------------------------------------------------------------------
if [[ ! -d ".venv" ]]; then
    info "Creating virtual environment in .venv ..."
    "$PYTHON" -m venv .venv
else
    info "Virtual environment already exists (.venv). Skipping creation."
fi

# shellcheck source=/dev/null
source .venv/bin/activate
info "Virtual environment activated."

# ---------------------------------------------------------------------------
# 3. Install Python dependencies
# ---------------------------------------------------------------------------
info "Installing Python dependencies from requirements.txt ..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
info "Dependencies installed."

# ---------------------------------------------------------------------------
# 4. Install Playwright's Chromium browser
# ---------------------------------------------------------------------------
info "Installing Chromium browser for Playwright (this may take a minute) ..."
playwright install chromium
info "Chromium installed."

# ---------------------------------------------------------------------------
# 5. Create .env from .env.example if it doesn't exist
# ---------------------------------------------------------------------------
if [[ ! -f ".env" ]]; then
    cp .env.example .env
    warn "Created .env from .env.example."
    warn ""
    warn "  *** ACTION REQUIRED ***"
    warn "  Open .env in a text editor and set:"
    warn "    TELEGRAM_BOT_TOKEN  – get from @BotFather on Telegram"
    warn "    TELEGRAM_CHAT_ID    – get from @userinfobot on Telegram"
    warn ""
    warn "Then run:  source .venv/bin/activate && python bot.py"
    warn "(or run this script again)"
    exit 0
fi

# ---------------------------------------------------------------------------
# 6. Start the bot
# ---------------------------------------------------------------------------
info "Starting the bot. Press Ctrl+C to stop."
python bot.py
