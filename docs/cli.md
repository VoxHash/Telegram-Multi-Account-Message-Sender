# CLI Reference

Command-line interface documentation for Telegram Multi-Account Message Sender.

## Running the Application

### GUI Mode (Default)

```bash
python main.py
```

Or if installed via pip:

```bash
python -m app.cli
```

### Command Line Options

The application primarily uses a GUI interface. For programmatic access, use the Python API.

### Read-only web companion

Start a local stdlib HTTP monitor (no extra dependencies). Desktop remains primary; this process only serves status JSON and a small dashboard.

```bash
telegram-sender web-monitor
telegram-sender web-monitor --host 127.0.0.1 --port 8765
telegram-sender web-monitor --host 0.0.0.0 --port 8765 --token "$(openssl rand -hex 32)"
python -m app.cli web-monitor
```

| Flag | Description |
| --- | --- |
| `--host` / `-H` | Bind address (default from settings / `127.0.0.1`) |
| `--port` / `-p` | Port (default `8765`) |
| `--token` / `-t` | Bearer token (required for non-localhost binds) |

| Path | Description |
| --- | --- |
| `/` | Minimal HTML dashboard |
| `/api/status` | App / companion metadata |
| `/api/accounts` | Account health summary + rows |
| `/api/campaigns` | Campaign status list |
| `/api/activity` | Recent send-log activity |
| `/api/overview` | Combined snapshot (includes `charts`) |
| `/api/charts` | Live chart series (hourly activity, status/health donuts, campaign bars) |

Write methods are rejected (`405`). Prefer `127.0.0.1` behind a TLS reverse proxy; see [Configuration](configuration.md) for auth and proxy guidance.

### Operator handoff (export / import)

Move a single-operator workspace between machines without Google Drive. Multi-user roles belong to [SendGram](https://www.sendgram.pro).

```bash
telegram-sender handoff-export ./operator-handoff.tmas-backup.zip
telegram-sender handoff-export ./handoff.tmas-backup.zip --password 'secret'
telegram-sender handoff-export ./db-only.tmas-backup.zip --no-sessions
telegram-sender handoff-import ./operator-handoff.tmas-backup.zip --password 'secret'
```

| Flag | Description |
| --- | --- |
| path | Output file/dir (export) or package to restore (import) |
| `--password` / `-p` | Optional encryption password (prompted on TTY if omitted) |
| `--no-sessions` | Export database + settings only (omit Telethon sessions) |
| `--sessions` | Include session files (default for export) |

Packages use the same `.tmas-backup.zip` format as Cloud Backup. Handoff exports default to including Telethon sessions so the same operator can continue on another machine. Treat packages as secret. After import, restart the app.

## Python API

### Basic Usage

```python
from app.services import initialize_database, get_settings
from app.models import Account, Campaign

# Initialize database
initialize_database()

# Get settings
settings = get_settings()

# Access models
accounts = Account.get_all()
campaigns = Campaign.get_all()
```

## Environment Variables

Configure the application using environment variables:

```bash
export TELEGRAM_API_ID="your_api_id"
export TELEGRAM_API_HASH="your_api_hash"
export LOG_LEVEL="INFO"
```

## Scripting Examples

### Example: Send a Message

```python
from app.core.engine import MessageEngine
from app.models import Account, Recipient

engine = MessageEngine()
account = Account.get_by_id(1)
recipient = Recipient.get_by_id(1)

engine.send_message(
    account=account,
    recipient=recipient,
    message="Hello, World!"
)
```

## See Also

- [API Documentation](api.md) for complete API reference
- [Usage Guide](usage.md) for GUI usage
- [Examples](examples/example-01.md) for more examples

