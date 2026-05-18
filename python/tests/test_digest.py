"""
PyTest suite for digest.py — mocks Gmail API and feedparser.
"""
import json
import pathlib
import sys
import textwrap
import types
from pathlib import Path
from unittest.mock import MagicMock, patch
import unittest.mock as mock

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


def _make_fake_weasyprint(written: list) -> types.ModuleType:
    """Return a minimal fake weasyprint module."""

    class FakeHTML:
        def __init__(self, *, string: str) -> None:
            self._string = string

        def write_pdf(self, path: str) -> None:
            written.append(path)
            with open(path, "wb") as fh:
                fh.write(b"%PDF-1.4 fake")

    mod = types.ModuleType("weasyprint")
    mod.HTML = FakeHTML  # type: ignore[attr-defined]
    return mod


def _make_fake_markdown() -> types.ModuleType:
    """Return a minimal fake markdown module."""
    mod = types.ModuleType("markdown")

    def markdown(text: str, **_kwargs: object) -> str:
        return f"<p>{text}</p>"

    mod.markdown = markdown  # type: ignore[attr-defined]
    return mod


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


# ── PDF export tests ──────────────────────────────────────────────────────────

def test_export_pdf_requires_pro() -> None:
    """export_pdf (via CLI) must be skipped / rejected when no license key is set."""
    from digest import main as digest_main

    with pytest.raises(SystemExit) as exc_info:
        digest_main(["--export-pdf", "--workspace", "/tmp"])

    assert exc_info.value.code != 0, (
        "digest.main should exit with a non-zero code when license key is absent"
    )


def test_export_pdf_creates_file(tmp_path: pathlib.Path) -> None:
    """export_pdf should write a PDF file and print its path to stdout."""
    md_file = tmp_path / "newsletter-digest.md"
    md_file.write_text(
        textwrap.dedent(
            """\
            # Test Digest

            Hello **world**.
            """
        )
    )

    output_pdf = tmp_path / "newsletter-digest.pdf"
    written: list = []

    fake_wp = _make_fake_weasyprint(written)
    fake_md = _make_fake_markdown()

    with (
        mock.patch.dict("sys.modules", {"weasyprint": fake_wp, "markdown": fake_md}),
        mock.patch("builtins.print") as mock_print,
    ):
        from digest import export_pdf
        export_pdf(str(md_file), str(output_pdf))

    mock_print.assert_called_once_with(str(output_pdf))
    assert str(output_pdf) in written


def test_export_pdf_cli_with_license_key(tmp_path: pathlib.Path) -> None:
    """CLI --export-pdf with a valid license key should call export_pdf."""
    md_file = tmp_path / "newsletter-digest.md"
    md_file.write_text("# Digest\nContent here.")

    written: list = []
    fake_wp = _make_fake_weasyprint(written)
    fake_md = _make_fake_markdown()

    with (
        mock.patch.dict("sys.modules", {"weasyprint": fake_wp, "markdown": fake_md}),
        mock.patch("builtins.print"),
    ):
        from digest import main as digest_main
        digest_main(
            [
                "--export-pdf",
                "--workspace",
                str(tmp_path),
                "--license",
                "PRO-KEY-123",
            ]
        )

    expected = str(tmp_path / "newsletter-digest.pdf")
    assert expected in written, f"Expected {expected} to have been written; got {written}"
