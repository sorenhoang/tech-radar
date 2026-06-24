# Tech Radar

Scans multiple tech/AI sources daily, groups them by category, and sends a digest to Slack.

## Structure

```
tech-radar/
├── radar.py                 # entry point
├── core.py                  # Item dataclass, paths, logging
├── config.py                # load config.yaml + .env
├── config.yaml              # enable/disable sources, keyword filters
├── .env                     # local overrides (secrets live in ~/.zshrc)
├── sources/
│   ├── __init__.py          # http_get, parse_feed, filter_by_keywords
│   ├── anthropic.py         # News, Engineering Blog, Changelog, Courses, Events
│   ├── youtube.py           # YouTube channels (AI + backend/systems)
│   ├── huggingface.py       # Hugging Face blog
│   ├── hackernews.py        # Hacker News top stories
│   ├── cloudflare.py        # Cloudflare engineering blog
│   ├── engineering.py       # Martin Fowler, AWS Blog, The New Stack, InfoQ
│   ├── devto.py             # dev.to community feed
│   ├── github_trending.py   # GitHub trending (by language)
│   └── security.py          # infosec feeds (THN, Bleeping Computer, Krebs, etc.)
└── notifiers/
    ├── slack.py             # webhook / bot DM
    ├── site.py              # static site generator → docs/
    └── video.py             # TikTok-style scroll video via Playwright + ffmpeg
```

## Sources

| Group | What |
|-------|------|
| Anthropic | News, Engineering Blog, Claude Code Changelog, Courses, Events |
| AI YouTube | Fireship, AI Explained, Matt Wolfe, Matthew Berman, Two Minute Papers |
| Backend YouTube | Hussein Nasser, ByteByteGo, TechWorld with Nana |
| Hugging Face | Model releases, papers, tooling |
| Hacker News | Top stories |
| Cloudflare | Engineering blog |
| Engineering | Martin Fowler, AWS Blog, The New Stack, InfoQ |
| dev.to | Community articles |
| GitHub Trending | TypeScript, Python, Go, Rust, Kotlin, Java |
| Security | The Hacker News, Bleeping Computer, Krebs on Security, Schneier, SecurityWeek, Google Project Zero |

## Usage

```bash
python3 radar.py --dry-run    # preview in terminal, no send
python3 radar.py --init       # mark all current items as seen (first run)
python3 radar.py              # scan + send to Slack
python3 radar.py --reset      # clear state
```

## Config

Edit `config.yaml` to:
- Disable a source: `sources.<name>.enabled: false`
- Change YouTube channels: edit `sources.youtube.channels`
- Filter by keyword: `sources.<name>.keywords: [backend, distributed, ...]`
- Filter GitHub languages: `sources.github_trending.languages: [go, rust]`
- Limit engineering feeds: `sources.engineering.feeds: ["Martin Fowler", "AWS Blog"]`

## Secrets

Set in `~/.zshrc` with the `CLAUDE_WATCHER_SLACK_*` prefix:

```
CLAUDE_WATCHER_SLACK_WEBHOOK_URL
CLAUDE_WATCHER_SLACK_BOT_TOKEN
CLAUDE_WATCHER_SLACK_USER_ID
CLAUDE_WATCHER_SLACK_CHANNEL
```

`.env` can override these — shell env always wins.

## State

`~/.tech-radar/seen.json` — tracks seen item URLs. Log at `~/.tech-radar/radar.log`.

## Dependencies

```bash
pip3 install requests beautifulsoup4 lxml
# optional:
pip3 install pyyaml          # fallback minimal parser is built-in
pip3 install playwright      # required for video generation
playwright install chromium
# brew install ffmpeg        # required for video generation
```
