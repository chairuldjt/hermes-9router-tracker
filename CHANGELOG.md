# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning.

## [Unreleased]

### Added

- Placeholder for upcoming improvements.

### Changed

- Placeholder for upcoming behavior or documentation updates.

### Fixed

- Placeholder for upcoming bug fixes.

## [0.1.0] - 2026-06-07

### Added

- Browserless 9Router quota tracking through HTTP API calls
- Hermes `/quota` installer and uninstaller flows
- Direct repo runner flow for Hermes environments without `pip`
- Package-based CLI entry points for managed Python environments
- Telegram-friendly summary and detail output grouped by provider
- Windows PowerShell helper script
- Linux installation guidance
- CI workflow for Python 3.10, 3.11, and 3.12

### Changed

- Public documentation was rewritten to be generic and Hermes-first
- Environment variable names were standardized to `ROUTER_QUOTA_*`

### Compatibility

- Legacy `AI_ITOPS_*` environment variables remain supported as fallback input names
