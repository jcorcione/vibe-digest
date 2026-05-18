"""
Tests for python/digest.py

Mocks the Gmail API and feedparser so tests run without network access or
real OAuth credentials.
"""

import json
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure the python/ directory is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

import digest  # noqa: E402 (import after sys.path manipulation)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_gmail_message(subject: str, html_body: str) -> dict:
    """Return a minimal Gmail API message structure."""
    import base64

    encoded = base64.urlsafe_b64encode(html_body.encode()).decode()
    return {
        "payload": {
            "mimeType": "text/html",
            "headers": [{"name": "Subject", "value": subject}],
            "body": {"data": encoded},
            "parts": [],
        }
    }


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

class TestIsProLicense:
    def test_valid_pro_key(self):
        assert digest._is_pro("VIBE-PRO-ABC123") is True

    def test_empty_key(self):
        assert digest._is_pro("") is False

    def test_invalid_key(self):
        assert digest._is_pro("FREE-KEY-XYZ") is False

    def test_none_like_empty(self):
        assert digest._is_pro("   ") is False


class TestHtmlToMarkdown:
    def test_simple_paragraph(self):
        result = digest._html_to_markdown("<p>Hello world</p>")
        assert "Hello world" in result

    def test_heading_converted(self):
        result = digest._html_to_markdown("<h1>My Newsletter</h1>")
        assert "# My Newsletter" in result

    def test_nav_stripped(self):
        html = "<nav>Skip to content</nav><p>Real content</p>"
        result = digest._html_to_markdown(html)
        assert "Skip to content" not in result
        assert "Real content" in result

    def test_empty_string(self):
        assert digest._html_to_markdown("") == ""


class TestBuildDigest:
    def _emails(self):
        return [{"subject": "Weekly Tech Roundup", "body": "Some interesting articles."}]

    def _articles(self):
        return [
            {
                "feed": "Hacker News",
                "title": "Top story",
                "link": "https://example.com",
                "summary": "A great read.",
            }
        ]

    def test_contains_newsletters_heading(self):
        result = digest._build_digest(self._emails(), [], False)
        assert "## 📬 Newsletters" in result

    def test_contains_rss_heading(self):
        result = digest._build_digest([], self._articles(), False)
        assert "## 📡 RSS Feeds" in result

    def test_email_subject_appears(self):
        result = digest._build_digest(self._emails(), [], False)
        assert "Weekly Tech Roundup" in result

    def test_rss_article_title_appears(self):
        result = digest._build_digest([], self._articles(), False)
        assert "Top story" in result

    def test_pro_badge_shown_when_pro(self):
        result = digest._build_digest([], [], True)
        assert "Vibe Digest Pro" in result

    def test_pro_badge_hidden_when_free(self):
        result = digest._build_digest([], [], False)
        assert "Vibe Digest Pro" not in result

    def test_no_emails_placeholder(self):
        result = digest._build_digest([], [], False)
        assert "No newsletter emails found" in result

    def test_no_rss_placeholder(self):
        result = digest._build_digest([], [], False)
        assert "No RSS feeds configured" in result


class TestFetchRssFeeds:
    def test_returns_articles_from_feed(self):
        mock_entry = MagicMock()
        mock_entry.get = lambda key, default="": {
            "title": "Article Title",
            "link": "https://example.com/article",
            "summary": "<p>Summary text</p>",
        }.get(key, default)

        mock_feed = MagicMock()
        mock_feed.feed.get = lambda key, default="": {"title": "Test Feed"}.get(key, default)
        mock_feed.entries = [mock_entry]

        with patch("digest.feedparser.parse", return_value=mock_feed):
            articles = digest._fetch_rss_feeds(["https://example.com/feed"])

        assert len(articles) == 1
        assert articles[0]["feed"] == "Test Feed"
        assert articles[0]["title"] == "Article Title"

    def test_handles_bad_feed_gracefully(self):
        with patch("digest.feedparser.parse", side_effect=Exception("network error")):
            articles = digest._fetch_rss_feeds(["https://broken.example.com/feed"])
        assert len(articles) == 1
        assert "Error fetching feed" in articles[0]["title"]


class TestFetchNewsletters:
    def test_fetches_and_decodes_messages(self):
        import base64

        html = "<h1>Newsletter Heading</h1><p>Body text</p>"
        encoded = base64.urlsafe_b64encode(html.encode()).decode()

        mock_list = MagicMock()
        mock_list.execute.return_value = {"messages": [{"id": "msg1"}]}

        mock_get = MagicMock()
        mock_get.execute.return_value = _make_gmail_message("Test Newsletter", html)

        mock_messages = MagicMock()
        mock_messages.list.return_value = mock_list
        mock_messages.get.return_value = mock_get

        mock_users = MagicMock()
        mock_users.messages.return_value = mock_messages

        mock_service = MagicMock()
        mock_service.users.return_value = mock_users

        with patch("digest._get_gmail_service", return_value=mock_service):
            emails = digest._fetch_newsletters()

        assert len(emails) == 1
        assert emails[0]["subject"] == "Test Newsletter"
        assert "Newsletter Heading" in emails[0]["body"]


class TestMainIntegration:
    """Integration test: run main() with mocked I/O and verify output file."""

    def test_main_writes_digest_file(self, tmp_path):
        mock_feed = MagicMock()
        mock_feed.feed.get = lambda key, default="": {"title": "Mock Feed"}.get(key, default)
        mock_entry = MagicMock()
        mock_entry.get = lambda key, default="": {
            "title": "Mock Article",
            "link": "https://mock.example.com",
            "summary": "<p>Mock summary</p>",
        }.get(key, default)
        mock_feed.entries = [mock_entry]

        with patch("sys.argv", [
            "digest.py",
            "--workspace", str(tmp_path),
            "--rss", json.dumps(["https://mock.example.com/feed"]),
        ]), patch("digest._fetch_newsletters", return_value=[]), \
           patch("digest.feedparser.parse", return_value=mock_feed):
            digest.main()

        output = tmp_path / "newsletter-digest.md"
        assert output.exists(), "Digest file was not created"
        content = output.read_text()
        assert "## 📬 Newsletters" in content
        assert "## 📡 RSS Feeds" in content

    def test_main_prints_output_path(self, tmp_path, capsys):
        with patch("sys.argv", [
            "digest.py",
            "--workspace", str(tmp_path),
            "--rss", "[]",
        ]), patch("digest._fetch_newsletters", return_value=[]):
            digest.main()

        captured = capsys.readouterr()
        printed_path = captured.out.strip()
        assert printed_path.endswith("newsletter-digest.md")
        assert Path(printed_path).exists()
