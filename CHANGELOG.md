# Changelog

All notable changes to Vibe Digest are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Planned
- PDF export (Pro)
- Multi-Gmail account support (Pro)
- Slack webhook integration (Pro)
- Custom digest templates (Pro)

---

## [0.1.0] — 2026-05-18

### Added
- Initial release 🎉
- Gmail OAuth integration (label:newsletter, newer_than:1d)
- RSS feed support via `vibeDigest.rssUrls` setting
- HTML → Markdown extraction (BeautifulSoup + markdownify)
- `Ctrl+Alt+N` keyboard shortcut to trigger digest
- Auto-run scheduling via cron expression (`vibeDigest.autoRun` + `vibeDigest.cron`)
- Python venv auto-bootstrap on first activation
- Pro license key stub (`vibeDigest.licenseKey`)
- Jest tests for TypeScript utilities
- PyTest suite for Python digest logic
- README with OAuth setup guide and settings reference
