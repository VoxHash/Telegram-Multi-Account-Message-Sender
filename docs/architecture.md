# Architecture

System architecture and design documentation for Telegram Multi-Account Message Sender.

## Overview

Telegram Multi-Account Message Sender is built with a modular architecture using Python and PyQt5.

## Architecture Layers

### Presentation Layer

- **GUI**: PyQt5-based graphical interface
- **Widgets**: Reusable UI components
- **Themes**: Theme system for UI customization

### Business Logic Layer

- **Engine**: Core message sending engine
- **Campaign Manager**: Campaign management logic
- **Throttler**: Rate limiting and throttling
- **Compliance**: Compliance and safety controls

### Data Layer

- **Models**: SQLModel-based data models
- **Database**: SQLite database
- **Services**: Database and service layer

## Key Components

### Core Components

- `app/core/engine.py`: Message sending engine
- `app/core/throttler.py`: Rate limiting
- `app/core/compliance.py`: Compliance controls
- `app/core/spintax.py`: Spintax processing

### Services

- `app/services/db.py`: Database service
- `app/services/campaign_manager.py`: Campaign management
- `app/services/logger.py`: Logging service
- `app/services/settings.py`: Settings management

### Models

- `app/models/account.py`: Account model
- `app/models/campaign.py`: Campaign model
- `app/models/recipient.py`: Recipient model
- `app/models/template.py`: Template model

## Data Flow

1. User interacts with GUI
2. GUI calls service layer
3. Service layer processes business logic
4. Data layer persists changes
5. Updates reflected in GUI

## Design Patterns

- **MVC**: Model-View-Controller pattern
- **Service Layer**: Business logic separation
- **Repository Pattern**: Data access abstraction

## Dependencies

- **PyQt5**: GUI framework
- **Telethon**: Telegram client library
- **SQLModel**: Database ORM
- **asyncio**: Asynchronous operations
- **tmms_native** (optional): Rust sidecar for parallel spintax and pacing

## Native accelerator (Rust)

Hot paths that are CPU-bound and parallelizable without touching Telethon live in a small Rust binary (`native/tmms_native`, installed as `bin/tmms_native`):

| Path | Role |
| --- | --- |
| Parallel spintax batch expand | Rayon workers expand `{a\|b\|c}` templates for N recipients before the send loop |
| Multi-account pace schedule | Compact wait/account slots for rate limits + jitter |

Python calls the sidecar once per batch via JSON on stdin/stdout (`app/core/native_accel.py`). GUI, SQLModel, and Telethon stay in Python. If the binary is absent or `TMMS_NATIVE_ACCEL=0`, the same APIs use pure Python.

**Expected benefit (local desktop):** bulk spintax prep uses OS threads without holding the GIL; schedule construction avoids large transient Python object graphs for long recipient lists, so the app competes less for RAM/CPU with other programs during campaign start.

## Cloud backup (Google Drive)

Optional encrypted backup/restore lives under `app/services/cloud/`:

| Component | Role |
| --- | --- |
| `BackupPackageBuilder` | Builds/verifies `.tmas-backup.zip` (SQLite + safe settings; optional Telethon sessions) |
| `GoogleDriveProvider` | OAuth desktop flow + Drive upload/list/download (`drive.file` scope) |
| `CloudBackupService` | Orchestrates Drive backup/list/restore and local handoff / entity export/import |
| `entity_transfer` | Selective templates/campaigns `entities.json` collect + merge/replace import |
| `handoff` CLI | `telegram-sender handoff-export` / `handoff-import` (`--entities`, `--mode`) |
| Settings UI | **Settings → Cloud Backup** (`cloud_backup_widget.py`) — Drive + **Export for Handoff…** |

Google API client libraries are optional (`pip install '.[cloud]'`). Tokens are encrypted under `app_data/cloud/`. Desktop remains single-operator; multi-user roles belong to SendGram.

## Web companion (read-only)

Optional local monitor in `app/services/web_companion.py` (stdlib `http.server` only — no web framework dependency):

| Piece | Role |
| --- | --- |
| Snapshot builders | Account health, campaign status, activity, analytics overview, live chart series from the SQLite DB |
| HTML dashboard | Summary cards + SVG live charts (hourly activity, status/health donuts, campaign bars); 15s refresh |
| `WebCompanionHandler` | GET/HEAD/OPTIONS only; mutating methods → `405`; optional Bearer / `X-TMAS-Token` / `?token=` auth |
| CLI / Settings | `telegram-sender web-monitor [--token …]` or **Settings → Start & Open in Browser**; optional `WEB_COMPANION_AUTO_START` / Auto-start with GUI (background; stop on app exit) |

Default bind is `127.0.0.1:8765`. Non-loopback binds require `WEB_COMPANION_TOKEN`. Prefer a TLS reverse proxy in front of localhost. Desktop remains the control surface.

## See Also

- [API Documentation](api.md) for API details
- [Development Guide](../CONTRIBUTING.md) for development setup
- [Installation](installation.md#optional-rust-native-accelerator) for the build step

