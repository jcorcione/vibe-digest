"""
PyTest suite for digest.py — mocks Gmail API and feedparser.
"""
import json
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

# Make digest importable without installing all deps
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_gmail_message(subject: str, body_text: str) -> dict:
    import base64
    encoded = base64.urlsafe_b64encode(body_text.encode()).decode()
    return {
        "payload": {
            "headers": [
                {"name": "Subject", "value": subject},
                {"name": "From", "value": "test@example.com"},
            ],
            "mimeType": "text/plain",
            "body": {"data": encoded},
            "parts": [],
        }
    }


# ── tests ─────────────────────────────────────────────────────────────────────

def test_build_markdown_contains_headings():
    from digest import build_markdown
    gmail = [{"title": "Weekly AI Digest", "source": "ai@newsletter.com", "content": "Cool AI stuff."}]
    rss = [{"title": "Tech News", "source": "TechFeed", "content": "Latest tech.", "link": "https://example.com"}]
    md = build_markdown(gmail, rss, is_pro=False)
    assert "# 📰 Newsletter Digest" in md
    assert "## ✉️ Gmail Newsletters" in md
    assert "## 📡 RSS Feeds" in md
    assert "Weekly AI Digest" in md
    assert "Tech News" in md


def test_build_markdown_pro_badge():
    from digest import build_markdown
    md = build_markdown([], [], is_pro=True)
    assert "Pro" in md


def test_fetch_rss_items_empty_on_bad_url():
    from digest import fetch_rss_items
    items = fetch_rss_items(["https://this-url-does-not-exist.invalid/feed"])
    assert isinstance(items, list)  # Should not raise, just warn


def test_extract_body_markdown_plain():
    import base64
    from digest import _extract_body_markdown
    text = "Hello, this is a newsletter."
    encoded = base64.urlsafe_b64encode(text.encode()).decode()
    payload = {"mimeType": "text/plain", "body": {"data": encoded}, "parts": []}
    result = _extract_body_markdown(payload)
    assert "Hello" in result


def test_extract_body_markdown_html():
    import base64
    from digest import _extract_body_markdown
    html = "<h1>Breaking News</h1><p>Something happened today.</p>"
    encoded = base64.urlsafe_b64encode(html.encode()).decode()
    payload = {"mimeType": "text/html", "body": {"data": encoded}, "parts": []}
    result = _extract_body_markdown(payload)
    assert "Breaking News" in result or "Something happened" in result
