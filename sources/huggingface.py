"""Hugging Face — blog feed covering model releases, papers, and tooling."""
from __future__ import annotations

from core import Item
from sources import fetch_feed


def fetch(cfg: dict) -> list[Item]:
    return fetch_feed("Hugging Face", None, "https://huggingface.co/blog/feed.xml")
