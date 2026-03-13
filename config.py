"""
Configuration management for the TLS Contact appointment bot.
Loads settings from environment variables / .env file.
"""

import os
from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

# ---------------------------------------------------------------------------
# TLS Contact
# ---------------------------------------------------------------------------
# Supported city codes for UK → Germany appointments:
#   LON – London, MAN – Manchester, EDI – Edinburgh, BIR – Birmingham
TLS_CITY: str = os.getenv("TLS_CITY", "LON")

# Human-readable label used in notifications
CITY_LABELS: dict[str, str] = {
    "LON": "London",
    "MAN": "Manchester",
    "EDI": "Edinburgh",
    "BIR": "Birmingham",
}

# TLS Contact base URL for Germany visas from the UK
TLS_BASE_URL: str = "https://visas-de.tlscontact.com"

# Public appointment-slot endpoint (GET → JSON list)
# Path pattern used by TLS Contact's frontend API
TLS_SLOTS_URL: str = (
    f"{TLS_BASE_URL}/api/gb/{TLS_CITY}/de-de/slotsList"
)

# Appointment landing page (included in notification links)
TLS_APPOINTMENT_URL: str = (
    f"{TLS_BASE_URL}/visa/gb/{TLS_CITY}/de-de/appointment"
)

# How often to check for new slots (seconds)
CHECK_INTERVAL: int = int(os.getenv("CHECK_INTERVAL", "300"))

# ---------------------------------------------------------------------------
# Email (optional)
# ---------------------------------------------------------------------------
EMAIL_SENDER: str = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")
EMAIL_RECIPIENT: str = os.getenv("EMAIL_RECIPIENT", "")
EMAIL_SMTP_HOST: str = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
EMAIL_SMTP_PORT: int = int(os.getenv("EMAIL_SMTP_PORT", "587"))

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def validate() -> None:
    """Raise ValueError if required configuration is missing."""
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN is not set. "
            "Please copy .env.example to .env and fill in the values."
        )
    if not TELEGRAM_CHAT_ID:
        raise ValueError(
            "TELEGRAM_CHAT_ID is not set. "
            "Please copy .env.example to .env and fill in the values."
        )
