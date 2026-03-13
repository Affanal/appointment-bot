"""
Unit tests for the TLS Contact appointment bot.

Run with:
    pytest tests/
"""

import asyncio
import json
import types
import unittest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# config tests
# ---------------------------------------------------------------------------

class TestConfig(unittest.TestCase):
    def test_validate_raises_when_telegram_token_missing(self):
        import config
        with patch.object(config, "TELEGRAM_BOT_TOKEN", ""), \
             patch.object(config, "TELEGRAM_CHAT_ID", "123"):
            with self.assertRaises(ValueError):
                config.validate()

    def test_validate_raises_when_chat_id_missing(self):
        import config
        with patch.object(config, "TELEGRAM_BOT_TOKEN", "tok"), \
             patch.object(config, "TELEGRAM_CHAT_ID", ""):
            with self.assertRaises(ValueError):
                config.validate()

    def test_validate_passes_when_configured(self):
        import config
        with patch.object(config, "TELEGRAM_BOT_TOKEN", "tok"), \
             patch.object(config, "TELEGRAM_CHAT_ID", "123"):
            config.validate()  # must not raise

    def test_tls_slots_url_contains_city(self):
        import config
        import importlib
        with patch.dict("os.environ", {"TLS_CITY": "MAN"}):
            importlib.reload(config)
            self.assertIn("MAN", config.TLS_SLOTS_URL)
        # Restore default
        with patch.dict("os.environ", {"TLS_CITY": "LON"}):
            importlib.reload(config)


# ---------------------------------------------------------------------------
# checker._normalise tests
# ---------------------------------------------------------------------------

class TestNormalise(unittest.TestCase):
    def _get_checker(self):
        import sys, importlib
        with patch.dict("os.environ", {
            "TELEGRAM_BOT_TOKEN": "tok",
            "TELEGRAM_CHAT_ID": "123",
        }):
            import config as cfg
            importlib.reload(cfg)
            if "checker" in sys.modules:
                del sys.modules["checker"]
            import checker as chk
            return chk

    def test_list_passthrough(self):
        chk = self._get_checker()
        data = [{"date": "2025-01-01"}, {"date": "2025-01-02"}]
        self.assertEqual(chk._normalise(data), data)

    def test_dict_with_slots_key(self):
        chk = self._get_checker()
        data = {"slots": [{"date": "2025-01-01"}], "total": 1}
        self.assertEqual(chk._normalise(data), data["slots"])

    def test_dict_with_available_slots_key(self):
        chk = self._get_checker()
        data = {"availableSlots": [{"date": "2025-02-01"}]}
        self.assertEqual(chk._normalise(data), data["availableSlots"])

    def test_dict_with_data_key(self):
        chk = self._get_checker()
        data = {"data": [{"date": "2025-03-01"}]}
        self.assertEqual(chk._normalise(data), data["data"])

    def test_unknown_shape_returns_empty(self):
        chk = self._get_checker()
        self.assertEqual(chk._normalise({"unknown_key": "value"}), [])

    def test_empty_list(self):
        chk = self._get_checker()
        self.assertEqual(chk._normalise([]), [])


# ---------------------------------------------------------------------------
# checker.check_slots – cloudscraper path
# ---------------------------------------------------------------------------

class TestCheckSlotsCloudScraper(unittest.IsolatedAsyncioTestCase):
    def _get_checker(self):
        import sys, importlib
        with patch.dict("os.environ", {
            "TELEGRAM_BOT_TOKEN": "tok",
            "TELEGRAM_CHAT_ID": "123",
        }):
            import config as cfg
            importlib.reload(cfg)
            if "checker" in sys.modules:
                del sys.modules["checker"]
            import checker as chk
            return chk

    async def test_returns_slots_on_success(self):
        chk = self._get_checker()
        slots_payload = [{"date": "2025-06-01", "time": "09:00"}]

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = slots_payload

        mock_scraper = MagicMock()
        mock_scraper.headers = MagicMock()
        mock_scraper.get.return_value = mock_response

        with patch("cloudscraper.create_scraper", return_value=mock_scraper):
            result = await chk.check_slots()

        self.assertEqual(result, slots_payload)

    async def test_falls_back_to_playwright_on_scraper_error(self):
        chk = self._get_checker()
        playwright_slots = [{"date": "2025-07-15"}]

        with patch("cloudscraper.create_scraper", side_effect=RuntimeError("CF block")), \
             patch.object(chk, "_check_with_playwright", new=AsyncMock(return_value=playwright_slots)):
            result = await chk.check_slots()

        self.assertEqual(result, playwright_slots)


# ---------------------------------------------------------------------------
# notifier.notify tests
# ---------------------------------------------------------------------------

class TestNotify(unittest.IsolatedAsyncioTestCase):
    def _get_notifier(self):
        import sys, importlib
        with patch.dict("os.environ", {
            "TELEGRAM_BOT_TOKEN": "tok",
            "TELEGRAM_CHAT_ID": "123",
        }):
            import config as cfg
            importlib.reload(cfg)
            if "notifier" in sys.modules:
                del sys.modules["notifier"]
            import notifier as ntf
            return ntf

    async def test_notify_calls_telegram_and_email(self):
        ntf = self._get_notifier()
        slots = [
            {"date": "2025-06-01", "time": "10:00", "category": "Tourist"},
            {"date": "2025-06-02", "time": "11:30"},
        ]

        with patch.object(ntf, "send_telegram", new=AsyncMock()) as mock_tg, \
             patch.object(ntf, "send_email", MagicMock()) as mock_em:
            await ntf.notify(slots)

        mock_tg.assert_called_once()
        msg = mock_tg.call_args[0][0]
        self.assertIn("2025-06-01", msg)
        self.assertIn("2025-06-02", msg)
        self.assertIn("Book now", msg)
        mock_em.assert_called_once()

    async def test_notify_singular_slot_label(self):
        ntf = self._get_notifier()
        with patch.object(ntf, "send_telegram", new=AsyncMock()) as mock_tg, \
             patch.object(ntf, "send_email", MagicMock()):
            await ntf.notify([{"date": "2025-06-01"}])

        msg = mock_tg.call_args[0][0]
        self.assertIn("1 appointment slot available", msg)

    async def test_notify_plural_slot_label(self):
        ntf = self._get_notifier()
        with patch.object(ntf, "send_telegram", new=AsyncMock()) as mock_tg, \
             patch.object(ntf, "send_email", MagicMock()):
            await ntf.notify([{"date": "2025-06-01"}, {"date": "2025-06-02"}])

        msg = mock_tg.call_args[0][0]
        self.assertIn("2 appointment slots available", msg)


if __name__ == "__main__":
    unittest.main()
