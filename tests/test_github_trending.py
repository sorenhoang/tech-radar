import sys
import types
import unittest

sys.modules.setdefault("requests", types.SimpleNamespace())
sys.modules.setdefault("bs4", types.SimpleNamespace(BeautifulSoup=object))

from core import Item
from sources import github_trending


def _make_fake_fetch(items):
    def fake_fetch_feed(source, label, url, max_items=10):
        return items
    return fake_fetch_feed


class GitHubTrendingTest(unittest.TestCase):
    def test_topic_matched_items_get_labelled(self):
        fake_items = [
            Item("GitHub Trending", "acme/vector-db", "https://example.com/vector", summary="AI embeddings search"),
            Item("GitHub Trending", "acme/raft-cache", "https://example.com/raft", summary="distributed systems consensus"),
            Item("GitHub Trending", "acme/css-theme", "https://example.com/css", summary="themes and colors"),
        ]
        github_trending.fetch_feed = _make_fake_fetch(fake_items)
        try:
            items = github_trending.fetch({
                "topics": [
                    {"name": "AI", "keywords": ["ai", "embedding"]},
                    {"name": "Distributed Systems", "keywords": ["distributed", "consensus"]},
                ]
            })
        finally:
            del github_trending.fetch_feed

        titles = [i.title for i in items]
        # matched items get labelled; unmatched item stays as-is
        self.assertIn("[AI] acme/vector-db", titles)
        self.assertIn("[Distributed Systems] acme/raft-cache", titles)
        self.assertIn("acme/css-theme", titles)
        self.assertEqual(len(items), 3)

    def test_all_items_returned_not_only_topic_matches(self):
        """All trending repos must reach the digest (ranking, not a filter)."""
        fake_items = [
            Item("GitHub Trending", "acme/rust-game", "https://example.com/game", summary="a video game"),
            Item("GitHub Trending", "acme/ai-tool",  "https://example.com/ai",   summary="llm inference wrapper"),
        ]
        github_trending.fetch_feed = _make_fake_fetch(fake_items)
        try:
            items = github_trending.fetch({
                "topics": [{"name": "AI", "keywords": ["llm", "inference"]}]
            })
        finally:
            del github_trending.fetch_feed

        self.assertEqual(len(items), 2)
        titles = [i.title for i in items]
        self.assertIn("acme/rust-game", titles)       # no topic match — still included
        self.assertIn("[AI] acme/ai-tool", titles)    # labelled

    def test_uses_all_language_daily_feed(self):
        fetched_urls = []

        def fake_fetch_feed(source, label, url, max_items=10):
            fetched_urls.append(url)
            return []

        github_trending.fetch_feed = fake_fetch_feed
        try:
            github_trending.fetch({})
        finally:
            del github_trending.fetch_feed

        self.assertEqual(fetched_urls, ["https://mshibanami.github.io/GitHubTrendingRSS/daily/all.xml"])

    def test_default_topics_label_database_and_software_engineering(self):
        fake_items = [
            Item("GitHub Trending", "acme/postgres-tuner", "https://example.com/db", summary="PostgreSQL query index migration tooling"),
            Item("GitHub Trending", "acme/observability-kit", "https://example.com/obs", summary="OpenTelemetry logging tracing reliability toolkit"),
        ]
        github_trending.fetch_feed = _make_fake_fetch(fake_items)
        try:
            items = github_trending.fetch({})
        finally:
            del github_trending.fetch_feed

        titles = [i.title for i in items]
        self.assertIn("[Database] acme/postgres-tuner", titles)
        self.assertIn("[Software Engineering] acme/observability-kit", titles)


if __name__ == "__main__":
    unittest.main()
