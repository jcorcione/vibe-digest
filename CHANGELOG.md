# Changelog

All notable changes to **Vibe Digest** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] – 2024-01-01

### Added
- Initial release of Vibe Digest VS Code extension
- `newsletter.digest` command bound to `Ctrl+Alt+N`
- Gmail OAuth2 authentication with token caching in the OS app-data directory
- Queries `label:newsletter newer_than:1d` to fetch recent newsletter emails
- HTML-to-Markdown conversion via BeautifulSoup + markdownify
- RSS/Atom feed aggregation via feedparser (up to 5 items per feed)
- Writes combined digest to `<workspace>/newsletter-digest.md`
- Opens the digest in VS Code Markdown Preview
- Auto-run scheduling via `vibeDigest.autoRun` and `vibeDigest.cron` settings
- Python venv auto-bootstrap on first run
- **Vibe Digest Pro** badge and PDF export unlock via `vibeDigest.licenseKey`
- Configurable RSS URLs via `vibeDigest.rssUrls` setting
