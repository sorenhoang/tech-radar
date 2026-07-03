# Tech Radar [![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/sorenhoang/tech-radar)

Daily tech/AI radar that fetches multiple sources, keeps only new/unseen items from yesterday in GMT+7, and sends a morning digest to Discord.

## What It Does

- Runs every morning at **06:30 GMT+7** via GitHub Actions.
- Can also be run manually from GitHub Actions or locally.
- Sends a Discord digest with clickable article titles.
- Suppresses Discord link previews.
- Shows at most 10 items per category.
- Spreads items across sub-sources/topics where possible.
- Tracks seen URLs so reruns do not resend the same links.

## Structure

```text
tech-radar/
├── radar.py                 # entry point
├── core.py                  # Item dataclass, state paths, logging
├── config.py                # load config.yaml + .env
├── config.yaml              # source toggles, feeds, keyword/topic filters
├── sources/
│   ├── __init__.py          # http_get, parse_feed, filter_by_keywords
│   ├── anthropic.py         # Anthropic News, Engineering, Changelog, Courses, Events
│   ├── youtube.py           # YouTube channel scraper
│   ├── huggingface.py       # Hugging Face blog
│   ├── hackernews.py        # Hacker News RSS
│   ├── cloudflare.py        # Cloudflare blog
│   ├── engineering.py       # Martin Fowler, AWS Blog, The New Stack, InfoQ
│   ├── devto.py             # dev.to + daily.dev
│   ├── github_trending.py   # topic-filtered GitHub Trending
│   └── security.py          # security news feeds
└── notifiers/
    └── discord.py           # Discord webhook digest
```

## Sources

| Group | What |
|---|---|
| Anthropic | News, Engineering Blog, Claude Code Changelog, Courses, Events |
| AI YouTube | Fireship, AI Explained, Matt Wolfe, Matthew Berman, Two Minute Papers |
| Backend YouTube | Hussein Nasser, ByteByteGo, TechWorld with Nana |
| Hugging Face | Model releases, papers, tooling |
| Hacker News | Top stories |
| Cloudflare | Engineering blog |
| Engineering | Martin Fowler, AWS Blog, The New Stack, InfoQ |
| dev.to / daily.dev | Community articles |
| GitHub Trending | Database, Software Engineering, Distributed Systems, Performance, AI, Finance, Productivity |
| Security | The Hacker News, Bleeping Computer, Krebs on Security, Schneier, SecurityWeek, Google Project Zero |

## Discord Setup

Reference server: https://discord.gg/XsBDHv8RfZ (`#tech-radar` channel).

1. In Discord, create or choose a server.
2. Create a text channel, for example `#tech-radar`.
3. Open **Edit Channel → Integrations → Webhooks**.
4. Create a webhook named `Tech Radar`.
5. Copy the webhook URL.

For local runs, create `.env`:

```bash
TECH_RADAR_DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
```

For GitHub Actions, add a repository secret:

```text
TECH_RADAR_DISCORD_WEBHOOK_URL
```

Never commit a real webhook URL.

## GitHub Actions

Workflow: `.github/workflows/daily-radar.yml`

```yaml
schedule:
  - cron: "30 23 * * *" # 06:30 GMT+7
workflow_dispatch:
```

GitHub cron runs in UTC, so `23:30 UTC` is `06:30 GMT+7`.

The workflow:

1. Installs Python dependencies.
2. Runs unit tests.
3. Runs `python radar.py`.
4. Commits `.tech-radar/seen.json` back to the repo.

`workflow_dispatch` lets you run it manually from the GitHub Actions tab.

## Local Usage

Create a virtualenv and install dependencies:

```bash
python3 -m venv .venv
.venv/bin/pip install requests beautifulsoup4 lxml pyyaml
```

Preview without sending:

```bash
.venv/bin/python radar.py --dry-run
```

Fetch and send to Discord:

```bash
.venv/bin/python radar.py
```

Mark currently fetched items as seen without sending:

```bash
.venv/bin/python radar.py --init
```

Clear local state:

```bash
.venv/bin/python radar.py --reset
```

## State

Local state:

```text
~/.tech-radar/seen.json
~/.tech-radar/radar.log
```

GitHub Actions state:

```text
.tech-radar/seen.json
```

Local state and GitHub Actions state are separate. Resetting local state does not affect GitHub Actions. The app does not track “sent days”; it only tracks seen URLs.

## Config

Edit `config.yaml`.

Common changes:

- Disable a source:
  ```yaml
  sources.<name>.enabled: false
  ```

- Filter a source by keywords:
  ```yaml
  sources.<name>.keywords: [backend, distributed, database]
  ```

- Limit engineering feeds:
  ```yaml
  sources.engineering.feeds: ["Martin Fowler", "AWS Blog"]
  ```

- Limit community feeds:
  ```yaml
  sources.devto.feeds: ["daily.dev"]
  ```

- Tune GitHub Trending topics:
  ```yaml
  sources.github_trending.topics:
    - name: "Database"
      keywords: [database, postgres, query, index]
  ```

## Tests

```bash
python3 -m unittest discover -s tests
PYTHONPYCACHEPREFIX=/tmp/tech-radar-pycache python3 -m py_compile radar.py core.py config.py sources/*.py notifiers/*.py tests/*.py
```
