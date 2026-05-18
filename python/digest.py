#!/usr/bin/env python3
"""
Vibe Digest – digest.py
=======================
Fetches Gmail newsletters (label:newsletter, newer_than:1d) and RSS feeds,
converts them to Markdown, and writes a single digest file to the workspace.

Usage:
    python digest.py --workspace /path/to/workspace \
                     --rss '["https://example.com/feed"]' \
                     [--license YOUR_LICENSE_KEY]
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Third-party imports
# ---------------------------------------------------------------------------
import feedparser
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from dotenv import load_dotenv

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
APP_NAME = "vibe-digest"
OUTPUT_FILENAME = "newsletter-digest.md"

# Token is stored in the OS-appropriate app-data directory
def _get_token_path() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    token_dir = base / APP_NAME
    token_dir.mkdir(parents=True, exist_ok=True)
    return token_dir / "token.json"


# ---------------------------------------------------------------------------
# License
# ---------------------------------------------------------------------------
def _is_pro(license_key: str) -> bool:
    """
    Basic license validation.  A real implementation would verify against a
    licensing server; here we accept any non-empty key that starts with
    'VIBE-PRO-' as valid so the logic is testable without network access.
    """
    return bool(license_key and license_key.strip().startswith("VIBE-PRO-"))


# ---------------------------------------------------------------------------
# Gmail helpers
# ---------------------------------------------------------------------------
def _get_gmail_service():
    """Authenticate and return a Gmail API service object."""
    token_path = _get_token_path()
    creds: Credentials | None = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Look for credentials.json beside this script
            creds_file = Path(__file__).parent / "credentials.json"
            if not creds_file.exists():
                raise FileNotFoundError(
                    "Gmail credentials file not found at "
                    f"{creds_file}. "
                    "Download it from Google Cloud Console and place it in python/."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_file), SCOPES)
            creds = flow.run_local_server(port=0)

        token_path.write_text(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def _fetch_newsletters() -> list[dict]:
    """Query Gmail for newsletter emails from the last day."""
    service = _get_gmail_service()
    result = (
        service.users()
        .messages()
        .list(userId="me", q="label:newsletter newer_than:1d")
        .execute()
    )

    messages = result.get("messages", [])
    emails = []

    for msg_ref in messages:
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=msg_ref["id"], format="full")
            .execute()
        )
        payload = msg.get("payload", {})
        headers = {h["name"]: h["value"] for h in payload.get("headers", [])}
        subject = headers.get("Subject", "(No subject)")
        body_html = _extract_body(payload)
        body_md = _html_to_markdown(body_html)
        emails.append({"subject": subject, "body": body_md})

    return emails


def _extract_body(payload: dict) -> str:
    """Recursively extract the HTML (or plain-text) body from a Gmail payload."""
    import base64

    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data", "")

    if body_data:
        decoded = base64.urlsafe_b64decode(body_data + "==").decode("utf-8", errors="replace")
        if "html" in mime_type:
            return decoded
        # Plain text – wrap in <pre> so markdownify keeps formatting
        return f"<pre>{decoded}</pre>"

    # Multipart – recurse into parts
    for part in payload.get("parts", []):
        result = _extract_body(part)
        if result:
            return result

    return ""


def _html_to_markdown(html: str) -> str:
    """Convert HTML to Markdown, stripping navigation/footer noise."""
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    # Remove common noise elements
    for tag in soup.select("nav, footer, script, style, [role='navigation']"):
        tag.decompose()
    return md(str(soup), heading_style="ATX").strip()


# ---------------------------------------------------------------------------
# RSS helpers
# ---------------------------------------------------------------------------
def _fetch_rss_feeds(urls: list[str]) -> list[dict]:
    """Fetch and parse RSS/Atom feeds, returning a list of article dicts."""
    articles = []
    for url in urls:
        try:
            feed = feedparser.parse(url)
            feed_title = feed.feed.get("title", url)
            for entry in feed.entries[:5]:  # cap at 5 items per feed
                title = entry.get("title", "(No title)")
                link = entry.get("link", "")
                summary_html = entry.get("summary", entry.get("description", ""))
                summary_md = _html_to_markdown(summary_html)
                articles.append(
                    {
                        "feed": feed_title,
                        "title": title,
                        "link": link,
                        "summary": summary_md,
                    }
                )
        except Exception as exc:  # noqa: BLE001
            articles.append(
                {
                    "feed": url,
                    "title": (
                        f"Error fetching feed ({type(exc).__name__}): {exc} — "
                        "check the URL is reachable and returns a valid RSS/Atom document."
                    ),
                    "link": "",
                    "summary": "",
                }
            )
    return articles


# ---------------------------------------------------------------------------
# Markdown assembly
# ---------------------------------------------------------------------------
def _build_digest(
    emails: list[dict],
    articles: list[dict],
    is_pro: bool,
) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# Vibe Digest",
        f"",
        f"Generated on {timestamp}",
    ]

    if is_pro:
        lines.append("")
        lines.append("**✨ Vibe Digest Pro**")

    # --- Newsletters ---
    lines += ["", "## 📬 Newsletters", ""]
    if emails:
        for email in emails:
            lines.append(f"### {email['subject']}")
            lines.append("")
            lines.append(email["body"])
            lines.append("")
    else:
        lines.append("_No newsletter emails found in the last 24 hours._")
        lines.append("")

    # --- RSS ---
    lines += ["## 📡 RSS Feeds", ""]
    if articles:
        current_feed = None
        for art in articles:
            if art["feed"] != current_feed:
                current_feed = art["feed"]
                lines.append(f"### {current_feed}")
                lines.append("")
            title_link = f"[{art['title']}]({art['link']})" if art["link"] else art["title"]
            lines.append(f"#### {title_link}")
            lines.append("")
            if art["summary"]:
                lines.append(art["summary"])
                lines.append("")
    else:
        lines.append("_No RSS feeds configured._")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Generate a newsletter digest")
    parser.add_argument("--workspace", required=True, help="Workspace directory path")
    parser.add_argument(
        "--rss", default="[]", help="JSON array of RSS feed URLs"
    )
    parser.add_argument("--license", default="", help="Vibe Digest Pro license key")
    args = parser.parse_args()

    workspace = Path(args.workspace)
    workspace.mkdir(parents=True, exist_ok=True)

    rss_urls: list[str] = json.loads(args.rss)
    pro = _is_pro(args.license)

    # Fetch content
    try:
        emails = _fetch_newsletters()
    except FileNotFoundError as exc:
        print(f"[Vibe Digest] Gmail credentials not found: {exc}", file=sys.stderr)
        emails = []
    except Exception as exc:  # noqa: BLE001
        exc_type = type(exc).__name__
        hint = ""
        # Surface actionable hints for the most common failure modes
        if "invalid_grant" in str(exc).lower() or "token" in str(exc).lower():
            hint = " Re-run the extension to go through the OAuth flow again and refresh your token."
        elif "quota" in str(exc).lower():
            hint = " Your Gmail API quota may be exhausted; try again later."
        elif "network" in str(exc).lower() or "connect" in str(exc).lower():
            hint = " Check your internet connection."
        print(
            f"[Vibe Digest] Gmail error ({exc_type}): {exc}.{hint}",
            file=sys.stderr,
        )
        emails = []

    articles = _fetch_rss_feeds(rss_urls)

    # Build and write digest
    digest_md = _build_digest(emails, articles, pro)
    output_path = workspace / OUTPUT_FILENAME
    output_path.write_text(digest_md, encoding="utf-8")

    # Print path for the TypeScript extension to read
    print(str(output_path))


if __name__ == "__main__":
    main()
