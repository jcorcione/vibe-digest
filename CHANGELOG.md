# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **PDF export (Pro feature):** New command `newsletter.exportPdf` ("Export Digest as PDF") with keybinding `Ctrl+Alt+P` (`Cmd+Alt+P` on Mac). Converts the workspace digest Markdown to a styled PDF using `markdown` and `weasyprint`. Requires a valid `vibeDigest.licenseKey` in settings.

## [0.1.0] - 2026-05-18

### Added
- Initial extension scaffold (digest generation, Pro license-key check).
