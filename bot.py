"""
TLS Contact UK → Germany appointment-slot monitor.

Usage
-----
    python bot.py

The bot polls TLS Contact every CHECK_INTERVAL seconds (default 5 minutes).
When available slots are detected it sends a Telegram message (and optionally
an email) and waits before checking again.
"""

import asyncio
import logging
import sys

import config
import checker
import notifier

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("bot")


# ---------------------------------------------------------------------------
# Core loop
# ---------------------------------------------------------------------------

async def run() -> None:
    """Main monitoring loop – runs until interrupted."""
    config.validate()

    city_label = config.CITY_LABELS.get(config.TLS_CITY, config.TLS_CITY)
    logger.info(
        "TLS Contact monitor started. Watching %s → Germany. "
        "Checking every %d s.",
        city_label,
        config.CHECK_INTERVAL,
    )

    consecutive_errors = 0
    max_consecutive_errors = 10  # give up after this many back-to-back failures

    while True:
        try:
            slots = await checker.check_slots()
            consecutive_errors = 0  # reset on success

            if slots:
                logger.info("%d slot(s) found – sending notification.", len(slots))
                await notifier.notify(slots)
            else:
                logger.info("No slots available yet.")

        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            consecutive_errors += 1
            logger.error(
                "Check failed (%d/%d): %s",
                consecutive_errors,
                max_consecutive_errors,
                exc,
            )
            if consecutive_errors >= max_consecutive_errors:
                logger.critical(
                    "Too many consecutive errors. Exiting. "
                    "Check your configuration and network connectivity."
                )
                sys.exit(1)

        logger.info("Sleeping %d s until next check.", config.CHECK_INTERVAL)
        await asyncio.sleep(config.CHECK_INTERVAL)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("Interrupted by user. Goodbye.")


if __name__ == "__main__":
    main()
