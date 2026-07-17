# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Project scaffolding: README, LICENSE, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY.
- Build configuration: `pyproject.toml`, `requirements.txt`, `.gitignore`.
- Configuration template: `config.example.json`.
- Core bot client (`moderation/bot.py`) with startup, logging, config loading, extension loader, ready event, and graceful shutdown.
- Package initialization (`moderation/__init__.py`) with version metadata and public API exposure.

### Changed
- Complete rewrite of the original moderation module from scratch.

### Deprecated
- All previous versions of the moderation module.

### Removed
- Legacy codebase and dependencies from the previous version.

### Fixed
- N/A (initial release).

### Security
- N/A (initial release).

---

## Release History

> Future releases will be documented here as they are published.

### [1.0.0] - Target: TBD
- Core moderation commands (kick, ban, timeout, warn, unban, purge, slowmode, nickname, lock/unlock, role).

### [1.1.0] - Target: TBD
- Case system, mod logs, appeals, automod, permission hierarchy, configuration manager.

### [1.2.0] - Target: TBD
- Audit integrations, plugin API, localization, dashboard API.

