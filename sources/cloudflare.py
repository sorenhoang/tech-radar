"""Cloudflare Blog — engineering posts on edge, networking, and infra."""
from __future__ import annotations

from core import Item
from sources import fetch_feed


def fetch(cfg: dict) -> list[Item]:
    return fetch_feed("Cloudflare", None, "https://blog.cloudflare.com/rss/")
