"""Discord notifier via incoming webhook."""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import requests

from core import HTTP_TIMEOUT, Item, log


DISCORD_WEBHOOK_URL = os.environ.get("TECH_RADAR_DISCORD_WEBHOOK_URL", "").strip()

ICONS = {
    "Events": "📅",
    "Anthropic News": "📣",
    "Engineering Blog": "🛠️",
    "Claude Code Changelog": "🚀",
    "Anthropic Courses": "🎓",
    "AI YouTube": "📺",
    "dev.to": "👩‍💻",
    "Engineering": "⚙️",
    "Hugging Face": "🤗",
    "Hacker News": "🔶",
    "Cloudflare": "☁️",
    "GitHub Trending": "📈",
    "Security": "🛡️",
}

MAX_ITEMS_PER_CATEGORY = 10
MAX_DISCORD_CONTENT_CHARS = 1900


def _escape_markdown_link_text(text: str) -> str:
    return text.replace("[", "\\[").replace("]", "\\]")

def _subsource_key(item: Item) -> str:
    title = item.title.strip()
    if title.startswith("[") and "]" in title:
        return title[1:title.index("]")]
    return item.source

def _display_title_parts(item: Item) -> tuple[str | None, str]:
    title = item.title.strip()
    if title.startswith("[") and "]" in title:
        prefix = title[1:title.index("]")]
        clean_title = title[title.index("]") + 1:].strip()
        return prefix, clean_title or title
    return None, title


def _pick_category_items(items: list[Item]) -> list[Item]:
    by_subsource: dict[str, list[Item]] = {}
    for item in items:
        by_subsource.setdefault(_subsource_key(item), []).append(item)

    picked: list[Item] = []
    keys = sorted(by_subsource)
    while len(picked) < MAX_ITEMS_PER_CATEGORY and any(by_subsource[key] for key in keys):
        for key in keys:
            if by_subsource[key] and len(picked) < MAX_ITEMS_PER_CATEGORY:
                picked.append(by_subsource[key].pop(0))
    return picked


def format_discord_message(new_items: list[Item], digest_day=None) -> dict:
    """Morning digest grouped by source with clickable item titles."""
    by_source: dict[str, list[Item]] = {}
    for item in new_items:
        by_source.setdefault(item.source, []).append(item)

    day_label = digest_day.isoformat() if digest_day else "yesterday"
    total = len(new_items)
    lines = [
        f"@everyone **Good morning! Tech Radar for {day_label}**",
        "",
        f"I found **{total}** new updates from yesterday.",
        "",
    ]

    for source, items in sorted(by_source.items()):
        icon = ICONS.get(source, "•")
        lines.append(f"**{icon} {source}** ({len(items)})")
        selected = _pick_category_items(items)
        for item in selected:
            prefix, clean_title = _display_title_parts(item)
            title = _escape_markdown_link_text(clean_title)
            source_label = f"{prefix}: " if prefix else ""
            lines.append(f"• {source_label}[{title}]({item.url})")
        lines.append("")

    lines.extend([
        "---",
        "Filtered to new/unseen updates.",
        "",
        "See you tomorrow.",
    ])
    return {"content": "\n".join(lines).strip()}

def _split_content(content: str) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for line in content.splitlines():
        line_len = len(line) + (1 if current else 0)
        if current and current_len + line_len > MAX_DISCORD_CONTENT_CHARS:
            chunks.append("\n".join(current))
            current = []
            current_len = 0
        if len(line) > MAX_DISCORD_CONTENT_CHARS:
            if current:
                chunks.append("\n".join(current))
                current = []
                current_len = 0
            for start in range(0, len(line), MAX_DISCORD_CONTENT_CHARS):
                chunks.append(line[start:start + MAX_DISCORD_CONTENT_CHARS])
            continue
        current.append(line)
        current_len += line_len
    if current:
        chunks.append("\n".join(current))
    return chunks or [""]


def send_discord(payload: dict) -> bool:
    if not DISCORD_WEBHOOK_URL:
        log("  ✗ No Discord webhook configured")
        return False
    try:
        chunks = _split_content(payload.get("content", ""))
        for chunk in chunks:
            resp = requests.post(DISCORD_WEBHOOK_URL, json={"content": chunk, "flags": 4}, timeout=HTTP_TIMEOUT)
            resp.raise_for_status()
        log(f"  ✓ Sent to Discord via webhook ({len(chunks)} message(s))")
        return True
    except Exception as e:
        log(f"  ✗ Discord webhook failed: {e}")
        return False
