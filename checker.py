"""
TLS Contact appointment-slot checker with Cloudflare bypass.

Strategy
--------
1. **cloudscraper** (lightweight, no browser required) – handles Cloudflare's
   JS-challenge v1 / v2 transparently by executing the challenge in a
   Node.js / native runtime.
2. **Playwright + playwright-stealth** – stealth-patched headless Chromium that
   defeats Cloudflare's bot-detection heuristics (fingerprinting, TLS
   fingerprint, JS environment checks).  Used as a fallback when cloudscraper
   fails or when the site requires full browser interaction.

Only strategy 2 (Playwright) is able to solve interactive CAPTCHAs or
Cloudflare Turnstile; cloudscraper covers the majority of day-to-day checks.
"""

import json
import logging
import random
import time
from typing import Any

import cloudscraper  # type: ignore[import-untyped]

import config

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared HTTP headers that mimic a real browser
# ---------------------------------------------------------------------------
_HEADERS: dict[str, str] = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-GB,en;q=0.9",
    "Referer": config.TLS_APPOINTMENT_URL,
    "Origin": config.TLS_BASE_URL,
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}


# ---------------------------------------------------------------------------
# Strategy 1 – cloudscraper
# ---------------------------------------------------------------------------

def _check_with_cloudscraper() -> list[dict[str, Any]]:
    """
    Use *cloudscraper* to fetch the slot list from TLS Contact.

    Returns a (possibly empty) list of slot dicts on success.
    Raises an exception if the request fails or the response is not parseable.
    """
    scraper = cloudscraper.create_scraper(
        browser={
            "browser": "chrome",
            "platform": "windows",
            "desktop": True,
        }
    )
    scraper.headers.update(_HEADERS)

    response = scraper.get(config.TLS_SLOTS_URL, timeout=30)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "")
    if "application/json" not in content_type and not response.text.strip().startswith(("[", "{")):
        # Received HTML – likely still a Cloudflare challenge page
        raise ValueError(
            f"Expected JSON but got Content-Type: {content_type!r}. "
            "Cloudflare challenge not cleared."
        )

    data = response.json()
    return _normalise(data)


# ---------------------------------------------------------------------------
# Strategy 2 – Playwright + stealth
# ---------------------------------------------------------------------------

async def _check_with_playwright() -> list[dict[str, Any]]:
    """
    Launch a stealth headless Chromium browser, navigate to the TLS Contact
    appointment page, intercept the XHR/fetch call to the slots API, and
    return the parsed slot list.
    """
    from playwright.async_api import async_playwright  # type: ignore[import-untyped]
    from playwright_stealth import stealth_async  # type: ignore[import-untyped]

    slots_data: list[dict] = []
    error: Exception | None = None

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-GB",
            timezone_id="Europe/London",
            viewport={"width": 1280, "height": 800},
        )

        page = await context.new_page()
        await stealth_async(page)

        # Intercept the API response that carries slot data
        async def _handle_response(response: Any) -> None:
            nonlocal slots_data, error
            if "slotsList" in response.url or "slots" in response.url.lower():
                try:
                    body = await response.json()
                    slots_data = _normalise(body)
                    logger.debug(
                        "Intercepted slots API response from %s", response.url
                    )
                except Exception as exc:  # noqa: BLE001
                    error = exc

        page.on("response", _handle_response)

        try:
            # Navigate to the appointment page so TLS Contact's JS fires the
            # slot-list request automatically
            await page.goto(
                config.TLS_APPOINTMENT_URL,
                wait_until="networkidle",
                timeout=60_000,
            )
            # Give any late XHR calls a little extra time
            await page.wait_for_timeout(3_000)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Playwright navigation error: %s", exc)
        finally:
            await browser.close()

    if error:
        raise error

    return slots_data


# ---------------------------------------------------------------------------
# Normalisation helper
# ---------------------------------------------------------------------------

def _normalise(raw: Any) -> list[dict[str, Any]]:
    """
    Convert the raw TLS Contact API response into a flat list of slot dicts.

    TLS Contact returns one of these shapes:
    - A list: ``[{"date": "...", ...}, ...]``
    - A dict with a ``slots`` / ``availableSlots`` / ``data`` key
    """
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        for key in ("slots", "availableSlots", "data", "appointments", "results"):
            if key in raw and isinstance(raw[key], list):
                return raw[key]
    logger.debug("Unexpected slots payload shape: %s", type(raw))
    return []


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def check_slots() -> list[dict[str, Any]]:
    """
    Return a list of available appointment slots.

    Tries cloudscraper first; falls back to Playwright on failure.
    Returns an empty list when no slots are available.
    """
    # Small random jitter to avoid perfectly periodic request patterns
    jitter = random.uniform(0.5, 2.5)
    time.sleep(jitter)

    # --- Strategy 1: cloudscraper ---
    try:
        slots = _check_with_cloudscraper()
        logger.info(
            "cloudscraper: %d slot(s) found for %s → Germany.",
            len(slots),
            config.TLS_CITY,
        )
        return slots
    except Exception as exc:  # noqa: BLE001
        logger.warning("cloudscraper failed (%s). Falling back to Playwright.", exc)

    # --- Strategy 2: Playwright + stealth ---
    try:
        slots = await _check_with_playwright()
        logger.info(
            "Playwright: %d slot(s) found for %s → Germany.",
            len(slots),
            config.TLS_CITY,
        )
        return slots
    except Exception as exc:  # noqa: BLE001
        logger.error("Playwright also failed: %s", exc)
        raise
