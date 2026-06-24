import sys
import types
import unittest

sys.modules.setdefault("requests", types.SimpleNamespace())
sys.modules.setdefault("bs4", types.SimpleNamespace(BeautifulSoup=object))

from core import Item
from sources import devto


class DevToSourcesTest(unittest.TestCase):
    def test_fetch_includes_daily_dev_feed(self):
        fetched = []

        def fake_fetch_feed(source, label, url):
            fetched.append((source, label, url))
            return [Item(source, f"{source} item", f"https://example.com/{source}")]

        original_fetch_feed = devto.fetch_feed
        devto.fetch_feed = fake_fetch_feed
        try:
            items = devto.fetch({})
        finally:
            devto.fetch_feed = original_fetch_feed

        self.assertEqual(fetched, [
            ("dev.to", None, "https://dev.to/feed"),
            ("daily.dev", None, "https://daily.dev/rss.xml"),
        ])
        self.assertEqual([item.source for item in items], ["dev.to", "daily.dev"])


if __name__ == "__main__":
    unittest.main()
