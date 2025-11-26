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

