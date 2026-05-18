"""
Vibe Digest – digest.py

Generates a newsletter-style digest for vibe projects.

CLI usage
---------
Normal digest generation (existing behaviour):
    python digest.py --workspace <path> --license-key <key>

Pro: export digest as PDF:
    python digest.py --export-pdf --workspace <path> --license-key <key>
"""

from __future__ import annotations

import argparse
import os
import sys


# ---------------------------------------------------------------------------
# Pro guard
# ---------------------------------------------------------------------------

def _require_pro(license_key: str | None, feature: str = "This feature") -> None:
    """Raise SystemExit if no license key is provided."""
    if not license_key:
        print(
            f"{feature} is a Pro feature. Add your license key in settings.",
            file=sys.stderr,
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# PDF export
# ---------------------------------------------------------------------------

def export_pdf(md_path: str, output_path: str) -> None:
    """Convert *md_path* (Markdown) to a PDF written at *output_path*.

    Requires the ``markdown`` and ``weasyprint`` packages (see requirements.txt).
    """
    import markdown  # type: ignore[import-untyped]
    from weasyprint import HTML  # type: ignore[import-untyped]

    with open(md_path, "r", encoding="utf-8") as fh:
        md_text = fh.read()

    body_html = markdown.markdown(md_text, extensions=["extra", "toc"])

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


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Vibe Digest – newsletter digest generator"
    )
    parser.add_argument(
        "--workspace",
        default=os.getcwd(),
        help="Path to the workspace folder (default: current directory)",
    )
    parser.add_argument(
        "--license-key",
        default="",
        dest="license_key",
        help="Pro license key",
    )
    parser.add_argument(
        "--export-pdf",
        action="store_true",
        dest="export_pdf",
        help="(Pro) Export the digest as a PDF file",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    workspace: str = args.workspace
    license_key: str = args.license_key.strip()

    if args.export_pdf:
        _require_pro(license_key, "PDF export")
        md_path = os.path.join(workspace, "newsletter-digest.md")
        output_path = os.path.join(workspace, "newsletter-digest.pdf")
        export_pdf(md_path, output_path)
        return

    # Default behaviour: generate the digest markdown (Pro-gated).
    _require_pro(license_key)
    print(f"Generating digest in {workspace} …")
    # TODO: implement digest generation logic here.


if __name__ == "__main__":
    main()
