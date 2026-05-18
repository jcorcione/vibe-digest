# 📰 Vibe Digest

A lightweight VS Code extension that fetches your latest Gmail newsletters and RSS feeds, then aggregates them into a **`newsletter-digest.md`** file right inside your workspace.

---

## ✨ Features

| Feature | Detail |
|---|---|
| **Gmail newsletters** | Queries messages with `label:newsletter newer_than:1d` |
| **RSS feeds** | Reads any list of RSS URLs from settings |
| **Markdown output** | Auto-opens `newsletter-digest.md` in the workspace |
| **Keyboard shortcut** | `Ctrl+Alt+N` (Mac: `Cmd+Alt+N`) |
| **Auto-run schedule** | Optional cron-based auto-run |
| **Pro tier** | Multi-account support, PDF export (license key) |

---

## 🚀 Quick Start

### 1. Install

Install from the VS Code Marketplace, or install locally:

```bash
# Build locally
npm ci
npm run compile
npm run package    # produces vibe-digest-x.x.x.vsix

# Install the .vsix
code --install-extension vibe-digest-0.1.0.vsix
```

### 2. Set up Gmail OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project → enable **Gmail API**.
3. Create **OAuth 2.0 Desktop credentials**.
4. Download `credentials.json` and place it at:
   - **Windows:** `%APPDATA%\vibe-digest\credentials.json`
   - **Mac/Linux:** `~/.vibe-digest/credentials.json`

On first run, a browser window opens for consent. The token is stored automatically.

### 3. Run

Press **`Ctrl+Alt+N`** (or open the Command Palette → *Generate Newsletter Digest*).

---

## ⚙️ Settings

| Setting | Default | Description |
|---|---|---|
| `vibeDigest.rssUrls` | `[]` | Array of RSS feed URLs |
| `vibeDigest.autoRun` | `false` | Enable auto-run on schedule |
| `vibeDigest.cron` | `"0 8 * * *"` | Cron expression (daily at 8am) |
| `vibeDigest.licenseKey` | `""` | Pro license key |

**Example `settings.json`:**

```json
{
  "vibeDigest.rssUrls": [
    "https://hnrss.org/frontpage",
    "https://feeds.arstechnica.com/arstechnica/index"
  ],
  "vibeDigest.autoRun": true,
  "vibeDigest.cron": "0 8 * * 1-5"
}
```

---

## 🏗️ Development

```bash
# Install Node deps
npm ci

# Compile TypeScript
npm run compile

# Set up Python env
npm run setup   # creates python/.venv and installs requirements

# Run all tests
npm test        # runs Jest + PyTest
```

---

## 💎 Pro Features

Upgrade to **Vibe Digest Pro** for:

- Multiple Gmail accounts
- Custom digest templates
- PDF export
- Slack webhook integration

[Get a Pro license →](https://your-marketplace-link)

---

## 🔐 Privacy

OAuth tokens are stored **locally** on your machine (`%APPDATA%/vibe-digest/token.json`). No data is sent to any third-party server.
