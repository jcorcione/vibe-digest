#!/usr/bin/env python3
"""
digest.py — Core logic for Vibe Digest VS Code extension.
Fetches Gmail newsletters + RSS feeds and writes a markdown digest.
"""

import argparse
import json
import os
import sys
import datetime
from pathlib import Path

# ── Gmail ────────────────────────────────────────────────────────────────────
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# ── RSS ───────────────────────────────────────────────────────────────────────
import feedparser

# ── HTML → Markdown ──────────────────────────────────────────────────────────
from bs4 import BeautifulSoup
import markdownify

# ── dotenv ────────────────────────────────────────────────────────────────────
from dotenv import load_dotenv

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
TOKEN_DIR = Path(os.environ.get("APPDATA", Path.home())) / "vibe-digest"
TOKEN_FILE = TOKEN_DIR / "token.json"
CREDENTIALS_FILE = TOKEN_DIR / "credentials.json"

# ─────────────────────────────────────────────────────────────────────────────


def get_gmail_service():
    TOKEN_DIR.mkdir(parents=True, exist_ok=True)
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                print(
                    f"ERROR: Place your OAuth credentials file at {CREDENTIALS_FILE}",
                    file=sys.stderr,
                )
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def fetch_gmail_items(service, max_results: int = 20) -> list[dict]:
    """Fetch newsletter emails from the last day."""
    items = []
    try:
        results = service.users().messages().list(
            userId="me",
            q="newer_than:1d label:newsletter",
            maxResults=max_results,
        ).execute()

        messages = results.get("messages", [])
        for msg_ref in messages:
            msg = service.users().messages().get(
                userId="me", id=msg_ref["id"], format="full"
            ).execute()

            subject = ""
            sender = ""
            for header in msg["payload"].get("headers", []):
                if header["name"] == "Subject":
                    subject = header["value"]
                if header["name"] == "From":
                    sender = header["value"]

            body_md = _extract_body_markdown(msg["payload"])
            items.append({"title": subject, "source": sender, "content": body_md})
    except Exception as e:
        print(f"Gmail warning: {e}", file=sys.stderr)

    return items


def _extract_body_markdown(payload: dict) -> str:
    """Recursively extract text/html or text/plain body and convert to markdown."""
    mime = payload.get("mimeType", "")
    data = payload.get("body", {}).get("data", "")

    if mime == "text/html" and data:
        import base64
        html = base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
        soup = BeautifulSoup(html, "html.parser")
        # Grab first meaningful paragraphs
        paragraphs = soup.find_all(["p", "h1", "h2", "h3"], limit=10)
        snippet_html = "".join(str(p) for p in paragraphs)
        return markdownify.markdownify(snippet_html, heading_style="ATX").strip()

    if mime == "text/plain" and data:
        import base64
        text = base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
        return text[:800].strip()

    # Recurse into parts
    for part in payload.get("parts", []):
        result = _extract_body_markdown(part)
        if result:
            return result

    return ""


# ─────────────────────────────────────────────────────────────────────────────


def fetch_rss_items(rss_urls: list[str]) -> list[dict]:
    items = []
    for url in rss_urls:
        try:
            feed = feedparser.parse(url)
            feed_title = feed.feed.get("title", url)
            for entry in feed.entries[:5]:
                title = entry.get("title", "Untitled")
                link = entry.get("link", "")
                summary_html = entry.get("summary", entry.get("description", ""))
                summary_md = markdownify.markdownify(summary_html, heading_style="ATX").strip()[:500]
                items.append({
                    "title": title,
                    "source": feed_title,
                    "content": summary_md,
                    "link": link,
                })
        except Exception as e:
            print(f"RSS warning ({url}): {e}", file=sys.stderr)
    return items


# ─────────────────────────────────────────────────────────────────────────────


def build_markdown(gmail_items: list[dict], rss_items: list[dict], is_pro: bool) -> str:
    today = datetime.date.today().strftime("%B %d, %Y")
    lines = [f"# 📰 Newsletter Digest — {today}\n"]

    if gmail_items:
        lines.append("## ✉️ Gmail Newsletters\n")
        for item in gmail_items:
            lines.append(f"### {item['title']}")
            lines.append(f"*From: {item['source']}*\n")
            if item["content"]:
                lines.append(item["content"])
            lines.append("")

    if rss_items:
        lines.append("## 📡 RSS Feeds\n")
        for item in rss_items:
            link_part = f" — [Read more]({item['link']})" if item.get("link") else ""
            lines.append(f"### {item['title']}{link_part}")
            lines.append(f"*Source: {item['source']}*\n")
            if item["content"]:
                lines.append(item["content"])
            lines.append("")

    if is_pro:
        lines.append("\n---\n*Generated by Vibe Digest Pro* 🚀")
    else:
        lines.append("\n---\n*Generated by Vibe Digest — [Upgrade to Pro](https://your-marketplace-link) for multi-account & PDF export.*")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────


def export_pdf(md_path: str, output_path: str) -> None:
    """Convert *md_path* (Markdown) to a PDF written at *output_path*.

    Requires the ``markdown`` and ``weasyprint`` packages (see requirements.txt).
    """
    import markdown as md_lib  # type: ignore[import-untyped]
    from weasyprint import HTML  # type: ignore[import-untyped]

    with open(md_path, "r", encoding="utf-8") as fh:
        md_text = fh.read()

    body_html = md_lib.markdown(md_text, extensions=["extra", "toc"])

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Vibe Digest</title>
  <style>
    body {{
      font-family: Georgia, 'Times New Roman', serif;
      max-width: 800px;
      margin: 0 auto;
      padding: 40px 24px;
      line-height: 1.6;
      color: #222;
    }}
    h1, h2, h3, h4 {{
      font-family: Arial, Helvetica, sans-serif;
      color: #111;
    }}
    pre, code {{
      background: #f4f4f4;
      padding: 2px 6px;
      border-radius: 3px;
      font-size: 0.9em;
    }}
    pre {{ padding: 12px; overflow-x: auto; }}
    a {{ color: #0057b8; }}
  </style>
</head>
<body>
{body_html}
</body>
</html>"""

    HTML(string=full_html).write_pdf(output_path)
    print(output_path)


# ─────────────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Vibe Digest — newsletter aggregator")
    parser.add_argument("--workspace", required=True, help="Workspace folder path")
    parser.add_argument("--rss", default="[]", help="JSON array of RSS URLs")
    parser.add_argument("--license", default="", help="Pro license key")
    parser.add_argument(
        "--export-pdf",
        action="store_true",
        dest="export_pdf",
        help="(Pro) Export the digest as a PDF file",
    )
    args = parser.parse_args(argv)

    workspace = Path(args.workspace)
    license_key: str = args.license.strip()

    if args.export_pdf:
        if not license_key:
            print(
                "PDF export is a Pro feature. Add your license key in settings.",
                file=sys.stderr,
            )
            sys.exit(1)
        md_path = str(workspace / "newsletter-digest.md")
        output_path = str(workspace / "newsletter-digest.pdf")
        export_pdf(md_path, output_path)
        return

    rss_urls: list[str] = json.loads(args.rss)
    is_pro = bool(license_key)  # Simple flag check; extend with real validation

    # Gmail
    gmail_items = []
    try:
        service = get_gmail_service()
        gmail_items = fetch_gmail_items(service)
    except SystemExit:
        pass  # Missing credentials — skip Gmail, continue with RSS

    # RSS
    rss_items = fetch_rss_items(rss_urls)

    # Build + write markdown
    md_content = build_markdown(gmail_items, rss_items, is_pro)
    output_path = str(workspace / "newsletter-digest.md")
    Path(output_path).write_text(md_content, encoding="utf-8")

    # Print path to stdout for the TS layer
    print(output_path)


if __name__ == "__main__":
    main()
