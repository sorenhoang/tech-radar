"""dev.to — community articles feed."""
from __future__ import annotations

from core import Item
from sources import fetch_feed, filter_by_keywords


def fetch(cfg: dict) -> list[Item]:
    items = fetch_feed("dev.to", None, "https://dev.to/feed")
    return filter_by_keywords(items, cfg.get("keywords") or [])
