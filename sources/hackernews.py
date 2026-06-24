"""Hacker News — top stories RSS feed."""
from __future__ import annotations

from core import Item
from sources import fetch_feed


def fetch(cfg: dict) -> list[Item]:
    return fetch_feed("Hacker News", None, "https://news.ycombinator.com/rss")
