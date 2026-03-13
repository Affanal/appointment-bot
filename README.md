# appointment-bot

A 24/7 Python bot that monitors the [TLS Contact](https://visas-de.tlscontact.com) website for available **UK → Germany** visa appointment slots and sends an instant notification via **Telegram** (and optionally email) the moment a slot opens up.

---

## Features

| Feature | Details |
|---|---|
| 🛡️ Cloudflare bypass | Uses **cloudscraper** (primary) and **Playwright + playwright-stealth** (fallback) to transparently solve Cloudflare JS challenges and defeat bot-detection fingerprinting |
| 🔔 Telegram notifications | Instant HTML-formatted message with slot dates, times, visa category, and a direct booking link |
| 📧 Email notifications | Optional SMTP email alert (Gmail / any SMTP server) |
| 🏙️ Multi-city support | London, Manchester, Edinburgh, Birmingham |
| 🐳 Docker-ready | Single `docker-compose up -d` for 24/7 cloud deployment |
| ⚙️ Configurable | All settings via environment variables / `.env` file |

---

## Quick Start

### 1. Clone and configure

```bash
git clone https://github.com/Affanal/appointment-bot.git
cd appointment-bot
cp .env.example .env
```

Edit `.env` with your values:

```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdef...   # from @BotFather
TELEGRAM_CHAT_ID=987654321                 # from @userinfobot
TLS_CITY=LON                              # LON | MAN | EDI | BIR
CHECK_INTERVAL=300                         # seconds between checks (default 5 min)
```

### 2. Get your Telegram credentials

1. Open Telegram and message **@BotFather** → `/newbot` → follow prompts → copy the token into `TELEGRAM_BOT_TOKEN`.
2. Message **@userinfobot** → it replies with your numeric chat ID → copy into `TELEGRAM_CHAT_ID`.

### 3a. Run with Docker (recommended for 24/7)

```bash
docker-compose up -d          # build image and start in background
docker-compose logs -f        # stream logs
```

### 3b. Run locally (Python 3.11+)

```bash
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium   # only needed the first time
python bot.py
```

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

### Cloudflare bypass strategy

1. **cloudscraper** – wraps `requests` to execute Cloudflare's JavaScript challenge in a lightweight JS runtime (no browser). Handles the vast majority of checks quickly and with minimal resource usage.
2. **Playwright + playwright-stealth** – used automatically as a fallback when cloudscraper is blocked. Launches a headless Chromium browser patched to hide all automation signals (navigator.webdriver, chrome runtime, plugin lists, canvas fingerprint, etc.) and intercepts the XHR response containing the slot data.

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

## Development & Testing

```bash
pip install pytest
pytest tests/ -v
```

---

## Project Structure

```
appointment-bot/
├── bot.py              # Main async monitoring loop
├── checker.py          # Cloudflare bypass + slot fetching
├── notifier.py         # Telegram & email notifications
├── config.py           # Configuration (env vars / .env)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── tests/
    └── test_bot.py
```

---

## Disclaimer

This tool is for personal use to monitor publicly available appointment information.
Always comply with TLS Contact's terms of service. Do not set very short check
intervals (< 2 minutes) to avoid overloading their servers.