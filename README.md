# appointment-bot

A 24/7 Python bot that monitors the [TLS Contact](https://visas-de.tlscontact.com)
website for available **UK → Germany** visa appointment slots and sends you an
instant **Telegram message** (and optionally an email) the moment a slot opens up.

---

## Features

| Feature | Details |
|---|---|
| 🛡️ Cloudflare bypass | Uses **cloudscraper** (primary) and **Playwright + playwright-stealth** (fallback) to transparently solve Cloudflare JS challenges and defeat bot-detection fingerprinting |
| 🔔 Telegram notifications | Instant HTML-formatted message with slot dates, times, visa category, and a direct booking link |
| 📧 Email notifications | Optional SMTP email alert (Gmail / any SMTP server) |
| 🏙️ Multi-city support | London, Manchester, Edinburgh, Birmingham |
| 🐳 Docker-ready | Single `docker-compose up -d` for 24/7 cloud deployment |
| ⚙️ Configurable | All settings via a single `.env` file |

---

## Prerequisites

Before you start, make sure you have one of the following installed:

- **Docker + Docker Compose** ← _easiest; recommended for 24/7 running_
- **Python 3.11 or newer** ← _for running directly on your machine_

You can check with:
```bash
docker --version          # e.g. Docker version 24.x
python --version          # e.g. Python 3.11.x  (or python3 --version)
```

> **Windows users:** use `python` instead of `python3` in all commands below, and
> run setup.bat instead of setup.sh.

---

## Step 1 – Get your Telegram credentials

You need two things: a **bot token** and your personal **chat ID**.

### 1a. Create a Telegram bot and get the token

1. Open Telegram and search for **@BotFather**.
2. Send the message `/newbot`.
3. Follow the prompts (choose a name and username for your bot).
4. BotFather replies with a token that looks like:
   ```
   123456789:ABCdefGhIJKlmNoPQRsTUVwxYZ
   ```
5. Copy and save this token — you will paste it into `TELEGRAM_BOT_TOKEN` shortly.

### 1b. Find your chat ID

1. Open Telegram and search for **@userinfobot**.
2. Send any message to it (e.g. `/start`).
3. It replies with your numeric ID, e.g. `987654321`.
4. Copy and save this number — you will paste it into `TELEGRAM_CHAT_ID` shortly.

---

## Step 2 – Clone the repository

```bash
git clone https://github.com/Affanal/appointment-bot.git
cd appointment-bot
```

---

## Step 3 – Configure the bot

Copy the example configuration file and fill in your values:

```bash
# Linux / macOS
cp .env.example .env

# Windows (Command Prompt)
copy .env.example .env
```

Now open `.env` in any text editor and set the two required values:

```env
# Required — paste the values you got from Step 1
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxYZ
TELEGRAM_CHAT_ID=987654321

# Which UK application centre to watch (default: London)
# LON = London  |  MAN = Manchester  |  EDI = Edinburgh  |  BIR = Birmingham
TLS_CITY=LON

# How often to check for slots, in seconds (default: 300 = every 5 minutes)
CHECK_INTERVAL=300
```

Save and close the file.

---

## Step 4 – Run the bot

Choose **one** of the methods below.

---

### Method A: Docker (recommended — runs 24/7 automatically)

> Requires Docker Desktop (Windows / macOS) or Docker Engine (Linux).

```bash
docker-compose up -d
```

That's it. The bot is now running in the background and will restart automatically
if your machine reboots or the process crashes.

**Useful commands:**

```bash
docker-compose logs -f          # stream live logs  (Ctrl+C to stop streaming)
docker-compose ps               # check if the bot is running
docker-compose stop             # stop the bot
docker-compose start            # start it again
docker-compose down             # stop and remove the container
docker-compose up -d --build    # rebuild after a code change
```

---

### Method B: One-command local setup (Linux / macOS)

```bash
bash setup.sh
```

This script creates a virtual environment, installs all dependencies, installs the
Chromium browser used for Cloudflare bypass, and then starts the bot.

To run the bot again later (without re-installing everything):

```bash
source .venv/bin/activate
python bot.py
```

---

### Method C: One-command local setup (Windows)

Double-click `setup.bat`, or run it in a Command Prompt:

```bat
setup.bat
```

To run the bot again later:

```bat
.venv\Scripts\activate
python bot.py
```

---

### Method D: Manual local setup (any platform)

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Install Python packages
pip install -r requirements.txt

# 3. Install the Chromium browser (only needed once)
playwright install chromium

# 4. Start the bot
python bot.py
```

---

## Step 5 – Verify it's working

When the bot starts you should see log lines like:

```
2025-06-01 10:00:00 [INFO] bot: TLS Contact monitor started. Watching London → Germany. Checking every 300 s.
2025-06-01 10:00:02 [INFO] checker: cloudscraper: 0 slot(s) found for LON → Germany.
2025-06-01 10:00:02 [INFO] bot: No slots available yet.
2025-06-01 10:00:02 [INFO] bot: Sleeping 300 s until next check.
```

When appointment slots become available you will receive a Telegram message like:

```
🟢 3 appointment slots available!
📍 TLS Contact London → Germany

📅 2025-06-10 | ⏰ 09:00 | 🗂 Tourist
📅 2025-06-11 | ⏰ 11:30
📅 2025-06-12

🔗 Book now
```

---

## Optional: Email notifications

Add these lines to your `.env` file to also receive email alerts:

```env
EMAIL_SENDER=your.gmail@gmail.com
EMAIL_PASSWORD=your_app_password     # Gmail → Settings → App Passwords
EMAIL_RECIPIENT=destination@email.com
```

> Gmail requires an **App Password** (not your normal password).
> Generate one at: **Google Account → Security → 2-Step Verification → App passwords**.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `ValueError: TELEGRAM_BOT_TOKEN is not set` | `.env` file missing or not filled in | Copy `.env.example` → `.env` and set the token |
| `ValueError: TELEGRAM_CHAT_ID is not set` | Chat ID missing in `.env` | Message @userinfobot on Telegram and paste the number |
| Bot exits after 10 errors | Network / Cloudflare issue | Check internet connectivity; try a VPN or longer `CHECK_INTERVAL` |
| `ModuleNotFoundError` | Dependencies not installed | Run `pip install -r requirements.txt` |
| `playwright._impl._errors.Error: Executable doesn't exist` | Chromium not installed | Run `playwright install chromium` |
| Docker: `Cannot connect to the Docker daemon` | Docker not running | Start Docker Desktop and try again |
| No Telegram message received | Wrong chat ID | Make sure you messaged the bot at least once before running |

---

## Configuration Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | ✅ | – | Telegram bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | ✅ | – | Your Telegram numeric chat ID |
| `TLS_CITY` | | `LON` | Application centre: `LON`, `MAN`, `EDI`, `BIR` |
| `CHECK_INTERVAL` | | `300` | Seconds between checks |
| `EMAIL_SENDER` | | – | Gmail address (or leave blank to disable) |
| `EMAIL_PASSWORD` | | – | Gmail app password |
| `EMAIL_RECIPIENT` | | – | Destination email address |
| `EMAIL_SMTP_HOST` | | `smtp.gmail.com` | SMTP server hostname |
| `EMAIL_SMTP_PORT` | | `587` | SMTP server port |

---

## How It Works

```
bot.py  ──(every CHECK_INTERVAL seconds)──►  checker.py
                                                 │
                            ┌────────────────────┤
                            │                    │
                    cloudscraper            Playwright
                   (fast, no GUI)       + playwright-stealth
                            │                    │
                            └──► /api/.../slotsList (JSON)
                                         │
                                  slots found?
                                    YES │
                                        ▼
                                  notifier.py
                               ┌────────────────┐
                               │ Telegram (HTML) │
                               │ Email (SMTP)    │
                               └────────────────┘
```

1. **cloudscraper** – wraps `requests` to execute Cloudflare's JavaScript challenge
   in a lightweight JS runtime (no browser). Handles the vast majority of checks
   quickly and with minimal resource usage.
2. **Playwright + playwright-stealth** – fallback when cloudscraper is blocked.
   Launches a headless Chromium browser with all automation signals patched out
   and intercepts the XHR response containing slot data.

---

## Project Structure

```
appointment-bot/
├── bot.py              # Main async monitoring loop
├── checker.py          # Cloudflare bypass + slot fetching
├── notifier.py         # Telegram & email notifications
├── config.py           # Configuration (env vars / .env)
├── setup.sh            # One-command setup for Linux / macOS
├── setup.bat           # One-command setup for Windows
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example        # Copy this to .env and fill in your values
└── tests/
    └── test_bot.py
```

---

## Development & Testing

```bash
pip install pytest
pytest tests/ -v
```

---

## Disclaimer

This tool is for personal use to monitor publicly available appointment information.
Always comply with TLS Contact's terms of service. Do not set very short check
intervals (< 2 minutes) to avoid overloading their servers.