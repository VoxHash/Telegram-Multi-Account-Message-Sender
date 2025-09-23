# Changelog

All notable changes to the Telegram Multi-Account Message Sender project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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