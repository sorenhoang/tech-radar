import sys
import types
import unittest

sys.modules.setdefault("requests", types.SimpleNamespace())
sys.modules.setdefault("bs4", types.SimpleNamespace(BeautifulSoup=object))

from core import Item
from sources import github_trending


class GitHubTrendingTest(unittest.TestCase):
    def test_fetch_uses_topics_instead_of_language_feeds(self):
        fetched_urls = []

        def fake_fetch_feed(source, label, url):
            fetched_urls.append(url)
            return [
                Item("GitHub Trending", "acme/vector-db", "https://example.com/vector", summary="AI embeddings search"),
                Item("GitHub Trending", "acme/raft-cache", "https://example.com/raft", summary="distributed systems consensus"),
                Item("GitHub Trending", "acme/css-theme", "https://example.com/css", summary="themes and colors"),
            ]

        original_fetch_feed = github_trending.fetch_feed
        github_trending.fetch_feed = fake_fetch_feed
        try:
            items = github_trending.fetch({
                "topics": [
                    {"name": "AI", "keywords": ["ai", "embedding"]},
                    {"name": "Distributed Systems", "keywords": ["distributed", "consensus"]},
                ]
            })
        finally:
            github_trending.fetch_feed = original_fetch_feed

        self.assertEqual(fetched_urls, ["https://mshibanami.github.io/GitHubTrendingRSS/daily/all.xml"])
        self.assertEqual([item.title for item in items], [
            "[AI] acme/vector-db",
            "[Distributed Systems] acme/raft-cache",
        ])

    def test_default_topics_include_database_and_software_engineering_keywords(self):
        fetched_urls = []

        def fake_fetch_feed(source, label, url):
            fetched_urls.append(url)
            return [
                Item("GitHub Trending", "acme/postgres-tuner", "https://example.com/db", summary="PostgreSQL query index migration tooling"),
                Item("GitHub Trending", "acme/observability-kit", "https://example.com/obs", summary="OpenTelemetry logging tracing reliability toolkit"),
            ]

        original_fetch_feed = github_trending.fetch_feed
        github_trending.fetch_feed = fake_fetch_feed
        try:
            items = github_trending.fetch({})
        finally:
            github_trending.fetch_feed = original_fetch_feed

        self.assertEqual(fetched_urls, ["https://mshibanami.github.io/GitHubTrendingRSS/daily/all.xml"])
        self.assertEqual([item.title for item in items], [
            "[Database] acme/postgres-tuner",
            "[Software Engineering] acme/observability-kit",
        ])


if __name__ == "__main__":
    unittest.main()
