"""
Notification helpers: Telegram and (optionally) email.
"""

import logging
import re
import smtplib
from email.mime.text import MIMEText
from typing import Sequence

import config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _html_to_text(html: str) -> str:
    """Convert simple HTML (bold, anchors, line-breaks) to plain text."""
    # Replace <a href="URL">label</a> with "label (URL)"
    text = re.sub(r"<a href='([^']*)'>(.*?)</a>", r"\2 (\1)", html, flags=re.DOTALL)
    # Strip remaining tags
    text = re.sub(r"<[^>]+>", "", text)
    return text


# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------

async def send_telegram(message: str) -> None:
    """Send *message* to the configured Telegram chat (async)."""
    # Import here to keep startup fast when Telegram is not used
    from telegram import Bot  # type: ignore[import-untyped]

    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    await bot.send_message(
        chat_id=config.TELEGRAM_CHAT_ID,
        text=message,
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
    logger.info("Telegram notification sent.")


# ---------------------------------------------------------------------------
# Email (optional)
# ---------------------------------------------------------------------------

def send_email(subject: str, body: str) -> None:
    """Send an email notification.  Silently skipped if not configured."""
    if not all([config.EMAIL_SENDER, config.EMAIL_PASSWORD, config.EMAIL_RECIPIENT]):
        return

    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = config.EMAIL_SENDER
    msg["To"] = config.EMAIL_RECIPIENT

    try:
        with smtplib.SMTP(config.EMAIL_SMTP_HOST, config.EMAIL_SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(config.EMAIL_SENDER, config.EMAIL_PASSWORD)
            smtp.sendmail(config.EMAIL_SENDER, config.EMAIL_RECIPIENT, msg.as_string())
        logger.info("Email notification sent to %s.", config.EMAIL_RECIPIENT)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to send email: %s", exc)


# ---------------------------------------------------------------------------
# Unified entry point
# ---------------------------------------------------------------------------

async def notify(slots: Sequence[dict]) -> None:
    """
    Build a human-readable message from *slots* and dispatch it via
    every configured notification channel.

    Each slot dict is expected to contain at least a ``date`` key; any
    additional keys (``time``, ``category``, etc.) are included when present.
    """
    city_label = config.CITY_LABELS.get(config.TLS_CITY, config.TLS_CITY)
    count = len(slots)
    header = (
        f"🟢 <b>{count} appointment slot{'s' if count != 1 else ''} "
        f"available!</b>\n"
        f"📍 TLS Contact {city_label} → Germany\n\n"
    )

    lines: list[str] = []
    for slot in slots:
        date = slot.get("date") or slot.get("appointmentDate") or "Unknown date"
        time_ = slot.get("time") or slot.get("appointmentTime") or ""
        category = slot.get("category") or slot.get("visaCategory") or ""

        parts = [f"📅 {date}"]
        if time_:
            parts.append(f"⏰ {time_}")
        if category:
            parts.append(f"🗂 {category}")
        lines.append(" | ".join(parts))

    body = header + "\n".join(lines)
    body += f"\n\n🔗 <a href='{config.TLS_APPOINTMENT_URL}'>Book now</a>"

    # Send via all channels
    await send_telegram(body)
    send_email(
        subject=f"[TLS Bot] {count} slot(s) available – {city_label} → Germany",
        body=_html_to_text(body),
    )
