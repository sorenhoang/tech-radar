"""GitHub Trending — topic filters over the community all-language RSS feed."""
from __future__ import annotations

from core import Item
from sources import fetch_feed, filter_by_keywords

_BASE = "https://mshibanami.github.io/GitHubTrendingRSS/daily"

DEFAULT_TOPICS = [
    {"name": "Database", "keywords": ["database", "postgres", "postgresql", "mysql", "sqlite", "redis", "mongodb", "query", "index", "migration", "oltp", "olap", "sql"]},
    {"name": "Software Engineering", "keywords": ["software engineering", "developer", "code review", "testing", "architecture", "backend", "api", "observability", "opentelemetry", "logging", "tracing", "reliability", "scalability", "refactoring", "ci/cd", "deployment", "auth", "concurrency"]},
    {"name": "Distributed Systems", "keywords": ["distributed", "consensus", "raft", "kubernetes", "queue", "streaming", "microservice", "database", "cache"]},
    {"name": "Performance", "keywords": ["performance", "optimization", "optimize", "fast", "latency", "benchmark", "profiling", "memory"]},
    {"name": "AI", "keywords": ["ai", "agent", "llm", "machine learning", "embedding", "rag", "model", "inference"]},
    {"name": "Finance", "keywords": ["finance", "fintech", "trading", "portfolio", "stock", "crypto", "investment", "payment"]},
    {"name": "Productivity", "keywords": ["productivity", "automation", "workflow", "notes", "task", "calendar", "email", "document"]},
]



def _matches_topic(item: Item, topic: dict) -> bool:
    text = f"{item.title} {item.summary}".lower()
    return any(keyword.lower() in text for keyword in topic.get("keywords") or [])


def _with_topic_label(item: Item, topic_name: str) -> Item:
    return Item(
        source=item.source,
        title=f"[{topic_name}] {item.title}",
        url=item.url,
        published=item.published,
        summary=item.summary,
    )


def _filter_by_topics(items: list[Item], topics: list[dict]) -> list[Item]:
    picked: list[Item] = []
    seen_ids: set[str] = set()
    for item in items:
        for topic in topics:
            if _matches_topic(item, topic):
                labelled = _with_topic_label(item, topic.get("name") or "Topic")
                if labelled.id not in seen_ids:
                    picked.append(labelled)
                    seen_ids.add(labelled.id)
                break
    return picked

def fetch(cfg: dict) -> list[Item]:
    topics = cfg.get("topics") or DEFAULT_TOPICS
    # Fetch 25 so topic labelling has headroom; radar.py caps the final list at 10.
    items = fetch_feed("GitHub Trending", None, f"{_BASE}/all.xml", max_items=25)
    # Label items that match a topic; keep all items regardless (daily ranking, not a filter).
    labelled: list[Item] = []
    for item in items:
        for topic in topics:
            if _matches_topic(item, topic):
                labelled.append(_with_topic_label(item, topic.get("name") or "Topic"))
                break
        else:
            labelled.append(item)
    keywords = cfg.get("keywords", [])
    return filter_by_keywords(labelled, keywords) if keywords else labelled
