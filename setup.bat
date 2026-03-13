@echo off
REM ---------------------------------------------------------------------------
REM setup.bat – one-command local setup for Windows
REM
REM Usage:
REM   Double-click setup.bat  OR  run it in a Command Prompt
REM
REM What it does:
REM   1. Checks that Python 3.11+ is available
REM   2. Creates a virtual environment (.venv)
REM   3. Installs all Python dependencies
REM   4. Installs the Chromium browser used by Playwright
REM   5. Copies .env.example -> .env if .env doesn't exist yet
REM   6. Starts the bot
REM ---------------------------------------------------------------------------

setlocal EnableDelayedExpansion

echo [setup] Checking Python version ...
python --version >nul 2>&1
if errorlevel 1 (
    echo [setup] ERROR: Python was not found.
    echo [setup] Install Python 3.11+ from https://www.python.org/downloads/
    echo [setup] Make sure to tick "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM Verify it is at least 3.11
python -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1
if errorlevel 1 (
    echo [setup] ERROR: Python 3.11 or newer is required.
    echo [setup] Your current version:
    python --version
    echo [setup] Download a newer version from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [setup] Python OK:
python --version

REM ---------------------------------------------------------------------------
REM Create virtual environment
REM ---------------------------------------------------------------------------
if not exist ".venv" (
    echo [setup] Creating virtual environment in .venv ...
    python -m venv .venv
    if errorlevel 1 (
        echo [setup] ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo [setup] Virtual environment already exists. Skipping creation.
)

call .venv\Scripts\activate.bat
echo [setup] Virtual environment activated.

REM ---------------------------------------------------------------------------
REM Install dependencies
REM ---------------------------------------------------------------------------
echo [setup] Installing Python dependencies ...
pip install --upgrade pip -q
pip install -r requirements.txt -q
if errorlevel 1 (
    echo [setup] ERROR: Failed to install dependencies.
    pause
    exit /b 1
)
echo [setup] Dependencies installed.

REM ---------------------------------------------------------------------------
REM Install Playwright Chromium
REM ---------------------------------------------------------------------------
echo [setup] Installing Chromium browser for Playwright ...
playwright install chromium
if errorlevel 1 (
    echo [setup] ERROR: Failed to install Chromium.
    pause
    exit /b 1
)
echo [setup] Chromium installed.

REM ---------------------------------------------------------------------------
REM Create .env if it doesn't exist
REM ---------------------------------------------------------------------------
if not exist ".env" (
    copy .env.example .env >nul
    echo.
    echo [setup] Created .env from .env.example.
    echo.
    echo  *** ACTION REQUIRED ***
    echo  Open .env in Notepad and set:
    echo    TELEGRAM_BOT_TOKEN  ^(get from @BotFather on Telegram^)
    echo    TELEGRAM_CHAT_ID    ^(get from @userinfobot on Telegram^)
    echo.
    echo  Then run setup.bat again, or:
    echo    .venv\Scripts\activate
    echo    python bot.py
    echo.
    pause
    exit /b 0
)

REM ---------------------------------------------------------------------------
REM Start the bot
REM ---------------------------------------------------------------------------
echo [setup] Starting the bot. Press Ctrl+C to stop.
python bot.py

pause
