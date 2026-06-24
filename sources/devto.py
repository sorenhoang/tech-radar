"""Community article feeds — dev.to and daily.dev."""
from __future__ import annotations

from core import Item
from sources import fetch_feed, filter_by_keywords



FEEDS = [
    ("dev.to", "https://dev.to/feed"),
    ("daily.dev", "https://daily.dev/rss.xml"),
]

def fetch(cfg: dict) -> list[Item]:
    enabled_labels = cfg.get("feeds")
    items: list[Item] = []
    for source, url in FEEDS:
        if enabled_labels and source not in enabled_labels:
            continue
        items.extend(fetch_feed(source, None, url))
    return filter_by_keywords(items, cfg.get("keywords") or [])
