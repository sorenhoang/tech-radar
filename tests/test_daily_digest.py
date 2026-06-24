from datetime import datetime
import sys
import tempfile
import types
import unittest
from zoneinfo import ZoneInfo

sys.modules.setdefault("requests", types.SimpleNamespace())
sys.modules.setdefault("bs4", types.SimpleNamespace(BeautifulSoup=object))

from core import Item
from notifiers import discord
from notifiers.discord import format_discord_message, send_discord
import radar
from radar import (
    digest_day_for,
    filter_digest_items,
    load_state,
)


TZ = ZoneInfo("Asia/Ho_Chi_Minh")


class DailyDigestTest(unittest.TestCase):
    def test_digest_day_for_morning_run_uses_previous_day_in_gmt7(self):
        run_at = datetime(2026, 6, 24, 6, 30, tzinfo=TZ)

        self.assertEqual(digest_day_for(run_at).isoformat(), "2026-06-23")

    def test_filter_digest_items_keeps_yesterday_gmt7_items_only(self):
        items = [
            Item("Anthropic News", "Yesterday", "https://example.com/y", "2026-06-23T10:00:00+07:00"),
            Item("Anthropic News", "Today", "https://example.com/t", "2026-06-24T01:00:00+07:00"),
            Item("Anthropic News", "No date", "https://example.com/n", ""),
        ]

        kept = filter_digest_items(items, digest_day_for(datetime(2026, 6, 24, 6, 30, tzinfo=TZ)))

        self.assertEqual([item.title for item in kept], ["Yesterday"])

    def test_state_does_not_track_sent_days(self):
        with tempfile.TemporaryDirectory() as td:
            original_state_file = radar.STATE_FILE
            radar.STATE_FILE = radar.Path(td) / "seen.json"
            radar.STATE_FILE.write_text('{"seen": ["https://example.com"], "sent_days": ["2026-06-23"], "last_run": "now"}')
            try:
                state = load_state()
            finally:
                radar.STATE_FILE = original_state_file

        self.assertIn("seen", state)
        self.assertIn("last_run", state)
        self.assertNotIn("sent_days", state)

    def test_discord_message_is_english_mentions_channel_and_links_titles(self):
        items = [
            Item("Anthropic News", "Claude Code update", "https://example.com/claude", "2026-06-23T10:00:00+07:00"),
            Item("Security", "Critical package advisory", "https://example.com/security", "2026-06-23T12:00:00+07:00"),
        ]

        payload = format_discord_message(items, digest_day_for(datetime(2026, 6, 24, 6, 30, tzinfo=TZ)))
        content = payload["content"]

        self.assertTrue(content.startswith("@everyone **Good morning! Tech Radar for 2026-06-23**"))
        self.assertIn("[Claude Code update](https://example.com/claude)", content)
        self.assertIn("[Critical package advisory](https://example.com/security)", content)
        self.assertIn("See you tomorrow.", content)

    def test_discord_message_caps_category_and_spreads_across_subsources(self):
        items = []
        for i in range(12):
            items.append(Item("Engineering", f"[AWS Blog] AWS item {i}", f"https://example.com/aws/{i}"))
        for i in range(4):
            items.append(Item("Engineering", f"[InfoQ] InfoQ item {i}", f"https://example.com/infoq/{i}"))
        for i in range(4):
            items.append(Item("Engineering", f"[The New Stack] TNS item {i}", f"https://example.com/tns/{i}"))

        payload = format_discord_message(items, digest_day_for(datetime(2026, 6, 24, 6, 30, tzinfo=TZ)))
        content = payload["content"]
        engineering_lines = [line for line in content.splitlines() if line.startswith("• ") and "](" in line]

        self.assertEqual(len(engineering_lines), 10)
        self.assertIn("AWS item 0", content)
        self.assertIn("InfoQ item 0", content)
        self.assertIn("TNS item 0", content)
        self.assertNotIn("more_", content)
        self.assertNotIn("...and", content)

    def test_discord_message_formats_subsource_prefix_without_backslashes(self):
        items = [
            Item(
                "Engineering",
                "[AWS Blog] Run isolated sandboxes with full lifecycle control",
                "https://example.com/aws",
            )
        ]

        payload = format_discord_message(items, digest_day_for(datetime(2026, 6, 24, 6, 30, tzinfo=TZ)))
        content = payload["content"]

        self.assertIn("• AWS Blog: [Run isolated sandboxes with full lifecycle control](https://example.com/aws)", content)
        self.assertNotIn("\\[AWS Blog\\]", content)

    def test_discord_send_splits_long_messages(self):
        calls = []

        class FakeResponse:
            def raise_for_status(self):
                return None

        def fake_post(url, json, timeout):
            calls.append(json["content"])
            return FakeResponse()

        original_url = discord.DISCORD_WEBHOOK_URL
        original_requests = discord.requests
        discord.DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/test"
        discord.requests = types.SimpleNamespace(post=fake_post)
        try:
            long_payload = {"content": "header\n" + "\n".join(f"line {i} " + ("x" * 80) for i in range(80))}

            self.assertTrue(send_discord(long_payload))
        finally:
            discord.DISCORD_WEBHOOK_URL = original_url
            discord.requests = original_requests

        self.assertGreater(len(calls), 1)
        self.assertTrue(all(len(content) <= 1900 for content in calls))

    def test_discord_send_suppresses_link_previews(self):
        calls = []

        class FakeResponse:
            def raise_for_status(self):
                return None

        def fake_post(url, json, timeout):
            calls.append(json)
            return FakeResponse()

        original_url = discord.DISCORD_WEBHOOK_URL
        original_requests = discord.requests
        discord.DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/test"
        discord.requests = types.SimpleNamespace(post=fake_post)
        try:
            self.assertTrue(send_discord({"content": "• [Example](https://example.com)"}))
        finally:
            discord.DISCORD_WEBHOOK_URL = original_url
            discord.requests = original_requests

        self.assertEqual(calls[0]["flags"], 4)


if __name__ == "__main__":
    unittest.main()
