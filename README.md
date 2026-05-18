# Vibe Digest

A VS Code extension that aggregates your Gmail newsletters and RSS feeds into a
single Markdown digest, right inside your editor.

## Features

- **`Ctrl+Alt+N`** — Generate a fresh digest on demand
- **Gmail integration** — Fetches emails with `label:newsletter newer_than:1d`
- **RSS/Atom feeds** — Aggregate any number of feeds via the `vibeDigest.rssUrls` setting
- **Markdown preview** — Opens the digest in VS Code's built-in preview
- **Auto-run** — Schedule automatic runs with a cron expression
- **Vibe Digest Pro** — Unlock the Pro badge and PDF export with a license key

## Requirements

- VS Code 1.92+
- Python 3.11+
- Node.js 20+

## Quick Start

```bash
# Install dependencies and compile
npm ci && npm run setup && npm run compile
```

On first activation the extension will automatically create a Python virtual
environment at `python/.venv` and install all required packages.

For Gmail access, place your `credentials.json` (downloaded from Google Cloud
Console) inside the `python/` directory, then run the command once to complete
the OAuth flow.

## Settings

| Setting | Type | Default | Description |
|---|---|---|---|
| `vibeDigest.rssUrls` | `string[]` | `[]` | RSS/Atom feed URLs |
| `vibeDigest.autoRun` | `boolean` | `false` | Enable scheduled digest generation |
| `vibeDigest.cron` | `string` | `"0 8 * * *"` | Cron expression for auto-run |
| `vibeDigest.licenseKey` | `string` | `""` | Vibe Digest Pro license key |

## Development

```bash
npm run compile   # Compile TypeScript
npm run watch     # Watch mode
npm test          # Run Jest + pytest
npm run package   # Build .vsix
```

## License

See [LICENSE](LICENSE).
