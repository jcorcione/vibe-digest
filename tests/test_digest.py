"""
Tests for digest.py
"""

from __future__ import annotations

import os
import sys
import textwrap
import types
import unittest.mock as mock

import pytest

# Make digest importable from the repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import digest  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fake_weasyprint(written: list[str]) -> types.ModuleType:
    """Return a minimal fake weasyprint module."""

    class FakeHTML:  # noqa: D101
        def __init__(self, *, string: str) -> None:
            self._string = string

        def write_pdf(self, path: str) -> None:  # noqa: D102
            written.append(path)
            # Create an empty file so callers can verify it exists
            with open(path, "wb") as fh:
                fh.write(b"%PDF-1.4 fake")

    mod = types.ModuleType("weasyprint")
    mod.HTML = FakeHTML  # type: ignore[attr-defined]
    return mod


def _make_fake_markdown() -> types.ModuleType:
    """Return a minimal fake markdown module."""
    mod = types.ModuleType("markdown")

    def markdown(text: str, **_kwargs: object) -> str:  # noqa: D103
        return f"<p>{text}</p>"

    mod.markdown = markdown  # type: ignore[attr-defined]
    return mod


# ---------------------------------------------------------------------------
# test_export_pdf_requires_pro
# ---------------------------------------------------------------------------

def test_export_pdf_requires_pro() -> None:
    """export_pdf (via CLI) must be skipped / rejected when no license key is set."""

    # Running with --export-pdf but NO --license-key should cause a SystemExit
    with pytest.raises(SystemExit) as exc_info:
        digest.main(["--export-pdf", "--workspace", "/tmp"])

    assert exc_info.value.code != 0, (
        "digest.main should exit with a non-zero code when license key is absent"
    )


# ---------------------------------------------------------------------------
# test_export_pdf_creates_file  (sanity check when a key IS provided)
# ---------------------------------------------------------------------------

def test_export_pdf_creates_file(tmp_path: pytest.fixture) -> None:  # type: ignore[valid-type]
    """export_pdf should write a PDF file and print its path to stdout."""
    # Write a minimal markdown file
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
    written: list[str] = []

    fake_wp = _make_fake_weasyprint(written)
    fake_md = _make_fake_markdown()

    with (
        mock.patch.dict("sys.modules", {"weasyprint": fake_wp, "markdown": fake_md}),
        mock.patch("builtins.print") as mock_print,
    ):
        digest.export_pdf(str(md_file), str(output_pdf))

    # The function should have printed the output path
    mock_print.assert_called_once_with(str(output_pdf))
    # The fake weasyprint should have been asked to write the PDF
    assert str(output_pdf) in written


# ---------------------------------------------------------------------------
# test_export_pdf_cli_with_license_key
# ---------------------------------------------------------------------------

def test_export_pdf_cli_with_license_key(tmp_path: pytest.fixture) -> None:  # type: ignore[valid-type]
    """CLI --export-pdf with a valid license key should call export_pdf."""
    md_file = tmp_path / "newsletter-digest.md"
    md_file.write_text("# Digest\nContent here.")

    written: list[str] = []
    fake_wp = _make_fake_weasyprint(written)
    fake_md = _make_fake_markdown()

    with (
        mock.patch.dict("sys.modules", {"weasyprint": fake_wp, "markdown": fake_md}),
        mock.patch("builtins.print"),
    ):
        digest.main(
            [
                "--export-pdf",
                "--workspace",
                str(tmp_path),
                "--license-key",
                "PRO-KEY-123",
            ]
        )

    expected = str(tmp_path / "newsletter-digest.pdf")
    assert expected in written, f"Expected {expected} to have been written; got {written}"
