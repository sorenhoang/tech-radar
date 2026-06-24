"""Engineering blogs — architecture, backend, cloud, and distributed systems."""
from __future__ import annotations

from core import Item
from sources import fetch_feed, filter_by_keywords

FEEDS = [
    ("Martin Fowler",  "https://martinfowler.com/feed.atom"),
    ("AWS Blog",       "https://aws.amazon.com/blogs/aws/feed/"),
    ("The New Stack",  "https://thenewstack.io/feed/"),
    ("InfoQ",          "https://feed.infoq.com/"),
]


def fetch(cfg: dict) -> list[Item]:
    enabled_labels = cfg.get("feeds")
    items: list[Item] = []
    for label, url in FEEDS:
        if enabled_labels and label not in enabled_labels:
            continue
        items.extend(fetch_feed("Engineering", label, url))
    return filter_by_keywords(items, cfg.get("keywords") or [])
