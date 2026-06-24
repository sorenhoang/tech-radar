#!/usr/bin/env python3
"""Tech Radar — scans multiple tech/AI sources and sends grouped notifications to Discord.

State: ~/.tech-radar/seen.json
Usage:
  python radar.py             # scan + send to Discord
  python radar.py --dry-run   # print to terminal, no send
  python radar.py --init      # mark all current items as seen (first run)
  python radar.py --reset     # clear state
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core import Item, STATE_DIR, STATE_FILE, log
from config import load_config, load_dotenv
from sources import parse_published

SOURCE_MODULES = [
    "anthropic",
    "youtube",
    "huggingface",
    "hackernews",
    "cloudflare",
    "engineering",
    "devto",
    "github_trending",
    "security",
]

DIGEST_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"seen": [], "last_run": None}
    try:
        state = json.loads(STATE_FILE.read_text())
        state.setdefault("seen", [])
        state.setdefault("last_run", None)
        state.pop("sent_days", None)
        return state
    except Exception:
        log("⚠️  Could not parse state file, starting fresh")
        return {"seen": [], "last_run": None}


def save_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def fetch_all(cfg: dict) -> list[Item]:
    log("Fetching sources...")
    items: list[Item] = []
    for name in SOURCE_MODULES:
        source_cfg = (cfg.get("sources") or {}).get(name) or {}
        if source_cfg.get("enabled") is False:
            log(f"  ⊘ {name}: disabled")
            continue
        module = importlib.import_module(f"sources.{name}")
        items.extend(module.fetch(source_cfg))
    return items


def diff_new(items: list[Item], seen_ids: set[str]) -> list[Item]:
    new: list[Item] = []
    seen_now: set[str] = set()
    for item in items:
        if item.id in seen_ids or item.id in seen_now:
            continue
        seen_now.add(item.id)
        new.append(item)
    return new

def digest_day_for(now: datetime | None = None):
    """Return the local day this morning digest should cover."""
    current = now or datetime.now(DIGEST_TZ)
    local_now = current.astimezone(DIGEST_TZ)
    return (local_now - timedelta(days=1)).date()


def filter_digest_items(items: list[Item], digest_day) -> list[Item]:
    """Keep only items published on the digest day in GMT+7."""
    kept: list[Item] = []
    for item in items:
        dt = parse_published(item.published)
        if dt is None:
            continue
        if dt.astimezone(DIGEST_TZ).date() == digest_day:
            kept.append(item)
    return kept


def filter_today(items: list[Item]) -> list[Item]:
    """Keep only items whose published date == today in local timezone.

    Items without a parseable date are dropped — we can't prove they're today.
    """
    today = datetime.now().astimezone().date()
    kept: list[Item] = []
    for item in items:
        dt = parse_published(item.published)
        if dt is None:
            continue
        if dt.astimezone().date() == today:
            kept.append(item)
    return kept


def print_terminal(new_items: list[Item]) -> None:
    if not new_items:
        print("\n✨ No new updates.\n")
        return
    by_source: dict[str, list[Item]] = {}
    for item in new_items:
        by_source.setdefault(item.source, []).append(item)
    print(f"\n🔔 {len(new_items)} new updates:\n")
    for source in sorted(by_source):
        print(f"  {source}:")
        for item in by_source[source]:
            date = f" ({item.published})" if item.published else ""
            print(f"    • {item.title}{date}")
            print(f"      {item.url}")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Tech Radar")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--init", action="store_true")
    args = parser.parse_args()

    load_dotenv()

    if args.reset:
        if STATE_FILE.exists():
            STATE_FILE.unlink()
            log("State cleared.")
        else:
            log("No state to clear.")
        return 0

    cfg = load_config()
    state = load_state()
    digest_day = digest_day_for()

    seen_ids = set(state.get("seen", []))
    items = fetch_all(cfg)
    if not items:
        log("⚠️  No items fetched.")
        return 1

    new_items = diff_new(items, seen_ids)
    digest_items = filter_digest_items(new_items, digest_day)
    log(
        f"Total: {len(items)} items, {len(new_items)} new, "
        f"{len(digest_items)} for {digest_day.isoformat()}"
    )
    new_items = digest_items

    merged = list(dict.fromkeys(state.get("seen", []) + [i.id for i in items]))[-800:]
    state["seen"] = merged
    state["last_run"] = datetime.now(timezone.utc).isoformat()

    if args.init:
        save_state(state)
        log(f"✓ Initialized — {len(items)} items marked seen.")
        return 0

    if not new_items:
        save_state(state)
        log(f"✨ No new items for {digest_day.isoformat()}.")
        return 0

    if args.dry_run:
        print_terminal(new_items)
        return 0

    from notifiers.discord import format_discord_message, send_discord
    payload = format_discord_message(new_items, digest_day)
    if not send_discord(payload):
        log("⚠️  Discord send failed — not marking digest sent, will retry next run.")
        print_terminal(new_items)
        return 2

    save_state(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
