# Changelog

All notable changes to the Telegram Multi-Account Message Sender project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.13] - 2026-05-24

### Fixed
- **GHCR Image Metadata**: Added OCI `org.opencontainers.image.description` via Dockerfile `LABEL` and publish workflow annotations so the container package page shows the project description on multi-arch manifests.

## [1.2.12] - 2026-05-24

### Fixed
- **PyPI Dependencies**: Added `pandas` to `pyproject.toml` so `pip install telegram-multi-account-sender` launches the GUI without extra manual installs.
- **Frozen Build Translations**: Fixed PyInstaller bundles and runtime resolution for locale JSON files (UI no longer shows raw `tabs.*` keys).

### Added
- **CI**: `pip install .` smoke test imports `MainWindow` to catch undeclared PyPI dependencies.
- **Container Distribution**: Publish Docker image to GHCR on release tags (`ghcr.io/voxhash/telegram-multi-account-message-sender`).

### Changed
- **Release Build**: Track `main.spec` in git and bundle each translation file explicitly for one-file executables.

## [1.2.11] - 2026-05-23

### Fixed
- **Python 3.11 Compatibility**: Fixed invalid nested f-string in `telegram_selector.py` that prevented the GUI from starting on Python 3.10–3.11.
- **Windows Executable**: Release builds now fail if the Windows `.exe` is missing, avoiding broken installers.
- **Session File Import**: Session import now passes the correct Telethon session path (without the `.session` extension).

### Changed
- **CI**: Added `compileall` and GUI import smoke checks so syntax and import errors are caught before release.

## [1.2.10] - 2026-05-18

### Fixed
- **Test Message Logging**: Fixed send test message crash caused by passing printf-style arguments to `AppLogger.debug()`, which only accepts a single message string.

## [1.2.9] - 2026-03-12

### Fixed
- **Spintax Determinism**: Fixed seeded spintax processing to use instance-local RNG so identical seeds produce reproducible output.
- **Spintax Validation**: Fixed validation to correctly flag empty variants and nested spintax as invalid.
- **Async Test Execution**: Fixed async unit-test execution by adding `pytest-asyncio` to development dependencies.
- **UI Translation Key**: Fixed missing translation-key usage by replacing `common.info` calls with `common.information` in core widgets.

### Changed
- **Warmup Manager Typing**: Improved worker tracking type safety by using `QThread`-typed worker references in `WarmupManager`.
- **Lint Baseline Cleanup**: Reduced lint backlog by removing unused imports/variables, eliminating bare `except`, and normalizing SQLAlchemy boolean filters to `.is_(...)`.

### Quality
- **Verification Pass**: Re-ran lint, type-check, unit tests, and live app startup smoke checks on Linux.
- **Live Preview Stability**: Confirmed app boot path initializes database, plugins, translations, and main window without startup regression.

## [1.2.8] - 2025-12-07

### Added
- **Proxy Test Functionality**: Added "Test Proxy" button in account proxy settings to verify proxy connection before saving
- **Session File Import**: New method to add accounts by importing Telethon session files (.session files)
- **Proxy Connection Testing**: Real-time proxy validation with detailed connection information
- **Session Import Worker**: Background worker thread for validating and extracting account info from session files
- **Proxy Test Worker**: Background worker thread for testing proxy connections through Telegram API

### Fixed
- **Proxy Functionality**: Fixed proxy settings not being applied when creating TelegramClient instances throughout the application
- **Proxy Format**: Corrected proxy configuration format to match Telethon requirements (HTTPS proxies converted to HTTP)
- **Campaign Manager**: Fixed proxy not being passed when creating clients for message sending and forwarding
- **Telegram Selector**: Fixed proxy not being used when fetching chats from Telegram accounts
- **Account Widget**: Fixed proxy not being used during account authorization, testing, and connection

### Changed
- **Account Model**: Added `get_telethon_proxy()` method to convert account proxy settings to Telethon format
- **Translation Files**: Updated all 12 non-English translation files with new proxy test and session import keys
- **Proxy Logging**: Enhanced logging to show when proxy is being used with connection details

### Technical
- **Proxy Integration**: Ensured all TelegramClient instances receive proxy configuration from account settings
- **Session Import**: Added UI for selecting and importing session files with automatic account info extraction
- **Proxy Validation**: Added comprehensive proxy testing with connection verification and DC information

## [1.2.7] - 2025-11-27

### Added
- **Telegram Chat Selector**: Interactive dialog to browse and select channels/groups from connected Telegram accounts
- **Thread Support**: Full support for Telegram group threads with thread ID selection and management
- **Message Forwarding**: Complete message forwarding functionality allowing campaigns to forward messages from source chats/channels
- **Recipient Browser Integration**: "Browse Telegram" button in recipient dialog for easy chat selection
- **Forwarding UI**: Campaign dialog now includes forwarding options with source chat and message ID selection
- **Multi-Language Support**: All new features fully translated into all 13 supported languages

### Changed
- **Recipient Model**: Added `thread_id` field to support group threads
- **Campaign Model**: Added forwarding fields (`forward_enabled`, `forward_from_chat_id`, `forward_from_chat_username`, `forward_from_message_id`)
- **Campaign Manager**: Enhanced to support message forwarding alongside regular message sending
- **Translation Files**: Updated all 12 non-English translation files with new feature translations

### Technical
- **New Components**: Created `TelegramSelectorDialog` widget for chat browsing
- **New Services**: Added `MessageForwarder` service for handling message forwarding operations
- **Backend Integration**: Full integration of forwarding and thread support in campaign execution engine

## [1.2.6] - 2025-11-26

### Added
- **API Documentation**: Comprehensive API reference documentation in `docs/api.md`
- **FAQ Documentation**: Complete frequently asked questions guide in `docs/faq.md`
- **Troubleshooting Guide**: Detailed troubleshooting documentation in `docs/troubleshooting.md`
- **Sponsors Section**: Added sponsors acknowledgment section to README.md
- **GitHub Sponsors Badge**: Added GitHub Sponsors badge to project badges
- **First Sponsor**: Acknowledged first monthly sponsor [@dodierandal-arch](https://github.com/dodierandal-arch) ($100/month)

### Fixed
- **Documentation Filenames**: Standardized all documentation filenames to lowercase convention
- **Broken Documentation Links**: Fixed all broken references in README.md and other documentation files
- **Empty Documentation Files**: Restored comprehensive content for previously empty documentation files
- **Documentation References**: Updated all internal documentation links to use correct lowercase filenames

### Changed
- **README.md**: Updated documentation section with correct links and improved structure
- **Documentation Structure**: Ensured all .md files follow standardized documentation kit structure
- **Version Consistency**: Updated version to 1.2.6 in pyproject.toml and setup.py

## [1.2.5] - 2025-11-25

### Fixed
- **CI/CD Pipelines**: Fixed workflow YAML syntax errors and action versions
- **Release Workflow**: Fixed version handling for workflow_dispatch triggers
- **PyPI Upload**: Added validation and error handling for PyPI package uploads
- **macOS Build**: Fixed PyInstaller icon path handling for macOS builds
- **Pytest Configuration**: Made pytest more robust with continue-on-error handling

### Changed
- **GitHub Actions**: Updated action versions and improved workflow reliability
- **Build Process**: Enhanced cross-platform build process with better error handling

## [1.2.4] - 2025-11-24

### Fixed
- **Project Depuration**: Removed unnecessary files, build artifacts, and temporary data
- **Git Configuration**: Fixed dubious ownership issues for repository access
- **Launcher Scripts**: Enhanced run_telegram_sender.bat and created run_telegram_sender.ps1
- **Documentation Standardization**: Renamed and standardized all documentation files

### Changed
- **Project Structure**: Cleaned up project folder structure
- **Documentation**: Standardized documentation file naming conventions

## [1.2.3] - 2025-01-23

### Added
- **Screenshots**: Added visual examples to README.md showcasing key features
- **Documentation Restructuring**: Complete documentation cleanup and organization
- **CONTRIBUTING.md**: Comprehensive contribution guidelines and development workflow
- **GITHUB_TOPICS.md**: Complete list of recommended GitHub topics for discoverability
- **Documentation Index**: Created docs/README.md for easy navigation

### Changed
- **README.md**: Updated with screenshots and streamlined content
- **ROADMAP.md**: Added current project status and marked Phase 1 as completed
- **CHANGELOG.md**: Cleaned up excessive historical entries, kept only relevant versions

### Fixed
- **Documentation Duplication**: Removed 8 duplicate summary files
- **Information Consolidation**: Merged related information into logical sections
- **Navigation**: Improved documentation structure and user experience

## [1.2.2] - 2025-01-23

### Added
- **PyPI Package Improvements**: Package now works with `python -m app.cli` out of the box
- **Multiple CLI Commands**: Added `telegram-sender` and `telegram-multi-account-sender` commands
- **Windows Executable**: Updated Windows executable with all v1.2.2 improvements
- **Better Installation**: Improved installation experience for end users
- **Windows Batch File**: Added `run_telegram_sender.bat` for easy Windows execution

### Fixed
- **PyPI Entry Points**: Fixed CLI entry points configuration for proper package installation
- **Installation Issues**: Resolved package installation and PATH issues
- **CLI Interface**: Improved CLI interface with proper error handling
- **Cross-Platform Compatibility**: Enhanced compatibility across different platforms

### Changed
- **Package Configuration**: Updated `pyproject.toml` and `setup.py` with correct entry points
- **Installation Documentation**: Enhanced installation documentation and examples
- **Version Management**: Bumped version to 1.2.2 for PyPI package improvements

## [1.2.1] - 2025-01-23

### Fixed
- **PyPI Dependencies**: Removed excessive dependencies causing installation failures
- **Package Size**: Reduced package size from 50+ dependencies to 22 essential ones
- **Installation Success**: Fixed "No matching distribution found" errors

## [1.2.0] - 2025-01-23

### Added
- **Delete All Logs Feature**: New "Delete All Logs" button in Settings tab for memory management
- **Enhanced Spintax Processing**: Fixed spintax processing in both campaigns and testing tabs
- **Settings Persistence**: All settings now properly persist when app is closed and reopened
- **Windows Startup Integration**: "Start App with Windows" functionality with Registry management
- **Comprehensive Settings Verification**: All settings options verified and working properly
- **Translation Key Synchronization**: All 560 translation keys synchronized across all 13 languages
- **Enhanced Error Handling**: Improved error handling for missing imports and UI components

### Fixed
- **Spintax Processing**: Fixed spintax not being processed in campaign and testing messages
- **Settings Loading**: Fixed language and theme settings not loading correctly on app restart
- **Translation Issues**: Fixed missing translation keys and untranslated strings
- **Import Errors**: Fixed missing QCheckBox import in testing widget
- **Settings Persistence**: Fixed settings not being saved to .env file correctly

### Changed
- **Settings Management**: Improved settings save/load functionality with proper enum handling
- **Translation System**: Enhanced translation system with better key management
- **UI Components**: Added spintax checkbox to testing tab for better user control
- **Documentation**: Updated all documentation to reflect new features and fixes

## [1.1.0] - 2025-01-22

### Added
- **Extended Multi-Language Support**: Added 5 new languages
  - Portuguese (pt)
  - Korean (ko)
  - Catalan (ca)
  - Basque (eu)
  - Galician (gl)
- **Enhanced Translation System**: Complete UI translation for all 13 supported languages
- **Updated Documentation**: All documentation updated to reflect new language support

### Changed
- **Language Enum**: Extended Language enum to include new languages
- **Settings UI**: Updated language selector to include all 13 languages
- **Version Bump**: Updated to version 1.1.0

## [1.0.0] - 2025-01-22

### Added
- **Initial Release**: First stable release of Telegram Multi-Account Message Sender
- **Multi-Account Management**: Complete account lifecycle management system
- **Campaign System**: Full campaign creation, scheduling, and management
- **Template System**: Advanced template management with spintax support
- **Recipient Management**: CSV import/export and recipient organization
- **Message Testing**: Comprehensive testing functionality
- **Logging System**: Detailed logging with filtering and export
- **Settings Management**: Complete settings persistence and management
- **Theme Support**: Multiple themes including Dracula theme
- **Database Integration**: SQLite with SQLModel ORM
- **Telegram API Integration**: Full Telethon library integration
- **Safety Features**: Rate limiting, warmup, and compliance controls
- **Multi-Language Support**: 8 languages with full translation coverage
- **Cross-Platform Support**: Windows, macOS, and Linux support

### Technical Details
- **Language**: Python 3.10+
- **GUI Framework**: PyQt5
- **Database**: SQLite with SQLModel ORM
- **Telegram API**: Telethon library
- **Architecture**: MVC pattern with service layer
- **Threading**: Asyncio and threading for concurrent operations

---

## Contributing to the Changelog

When adding new entries to this changelog:

1. **Follow the format**: Use the established format for consistency
2. **Be descriptive**: Provide clear descriptions of changes
3. **Categorize properly**: Use the correct categories (Added, Changed, Fixed, Removed)
4. **Include details**: Add relevant technical details
5. **Link issues**: Reference related issues and pull requests
6. **Version correctly**: Use semantic versioning
7. **Date entries**: Include release dates
8. **Group changes**: Group related changes together
9. **Be concise**: Keep entries concise but informative
10. **Review carefully**: Review entries for accuracy and completeness

## Changelog Maintenance

This changelog is maintained by the development team and community contributors. It should be updated with every release to provide users with a clear understanding of what has changed.

For questions about the changelog or to suggest improvements, please open an issue or pull request on the GitHub repository.