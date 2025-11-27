# API Documentation

Complete API reference for Telegram Multi-Account Message Sender.

## Overview

This document provides a comprehensive reference for all public APIs, classes, and functions in the Telegram Multi-Account Message Sender application.

## Core Module (`app.core`)

### Telegram Client Management

#### `TelegramClientManager`

Manages multiple Telegram client connections.

```python
from app.core import TelegramClientManager

manager = TelegramClientManager()
```

**Methods:**
- `get_client(account_id: str) -> TelegramClientWrapper`: Get client for account
- `add_client(account: Account) -> TelegramClientWrapper`: Add new client
- `remove_client(account_id: str) -> None`: Remove client
- `disconnect_all() -> None`: Disconnect all clients

#### `TelegramClientWrapper`

Wrapper for Telethon Telegram client.

```python
from app.core import TelegramClientWrapper

client = TelegramClientWrapper(account_id, api_id, api_hash)
```

**Methods:**
- `connect() -> bool`: Connect to Telegram
- `disconnect() -> None`: Disconnect from Telegram
- `send_message(recipient: str, message: str, media: Optional[str] = None) -> dict`: Send message
- `is_connected() -> bool`: Check connection status

### Message Engine

#### `MessageEngine`

Core message sending engine.

```python
from app.core import MessageEngine

engine = MessageEngine()
```

**Methods:**
- `send_message(account_id: str, recipient: str, message: str, media: Optional[str] = None) -> dict`: Send single message
- `process_spintax(text: str) -> str`: Process spintax syntax
- `validate_message(message: str) -> bool`: Validate message content

#### `CampaignRunner`

Runs message campaigns.

```python
from app.core import CampaignRunner

runner = CampaignRunner(campaign_id)
```

**Methods:**
- `start() -> None`: Start campaign
- `pause() -> None`: Pause campaign
- `stop() -> None`: Stop campaign
- `get_status() -> dict`: Get campaign status

### Rate Limiting

#### `Throttler`

Manages rate limiting and throttling.

```python
from app.core import Throttler

throttler = Throttler(max_messages_per_minute=30)
```

**Methods:**
- `acquire(account_id: str) -> bool`: Acquire permission to send
- `wait_time(account_id: str) -> float`: Get wait time until next send
- `reset(account_id: str) -> None`: Reset rate limit for account

#### `RateLimiter`

Rate limiting implementation.

```python
from app.core import RateLimiter

limiter = RateLimiter(rate=30, per=60)
```

### Spintax Processing

#### `SpintaxProcessor`

Processes spintax syntax for message variations.

```python
from app.core import SpintaxProcessor

processor = SpintaxProcessor()
result = processor.process("Hello {John|Jane|Alex}!")
```

**Methods:**
- `process(text: str) -> str`: Process spintax and return variation
- `validate(text: str) -> bool`: Validate spintax syntax
- `get_variations(text: str, count: int = 10) -> List[str]`: Get multiple variations

### Compliance

#### `ComplianceChecker`

Checks message compliance.

```python
from app.core import ComplianceChecker

checker = ComplianceChecker()
is_compliant = checker.check(message)
```

**Methods:**
- `check(message: str) -> bool`: Check if message is compliant
- `get_violations(message: str) -> List[str]`: Get list of violations
- `fix(message: str) -> str`: Auto-fix compliance issues

#### `SafetyGuard`

Safety and security checks.

```python
from app.core import SafetyGuard

guard = SafetyGuard()
```

**Methods:**
- `check_rate_limit(account_id: str) -> bool`: Check rate limit compliance
- `check_content(message: str) -> bool`: Check content safety
- `check_recipient(recipient: str) -> bool`: Validate recipient

### Analytics

#### `AnalyticsCollector`

Collects campaign analytics.

```python
from app.core import AnalyticsCollector

collector = AnalyticsCollector()
```

**Methods:**
- `collect(campaign_id: str, event: str, data: dict) -> None`: Collect analytics event
- `get_stats(campaign_id: str) -> dict`: Get campaign statistics
- `export(campaign_id: str, format: str = "json") -> str`: Export analytics

#### `CampaignAnalytics`

Campaign analytics data structure.

```python
from app.core import CampaignAnalytics

analytics = CampaignAnalytics(campaign_id)
```

## Models (`app.models`)

### Account Model

#### `Account`

Telegram account model.

```python
from app.models import Account

account = Account(
    phone_number="+1234567890",
    api_id="your_api_id",
    api_hash="your_api_hash"
)
```

**Fields:**
- `id: UUID`: Account ID
- `phone_number: str`: Phone number
- `api_id: str`: Telegram API ID
- `api_hash: str`: Telegram API hash
- `status: AccountStatus`: Account status
- `proxy_type: Optional[ProxyType]`: Proxy type
- `proxy_host: Optional[str]`: Proxy host
- `proxy_port: Optional[int]`: Proxy port
- `created_at: datetime`: Creation timestamp
- `updated_at: datetime`: Update timestamp

#### `AccountStatus`

Account status enumeration.

```python
from app.models import AccountStatus

AccountStatus.ACTIVE
AccountStatus.INACTIVE
AccountStatus.BANNED
AccountStatus.PENDING
```

### Campaign Model

#### `Campaign`

Message campaign model.

```python
from app.models import Campaign

campaign = Campaign(
    name="My Campaign",
    campaign_type=CampaignType.BULK,
    message_text="Hello {name}!",
    status=CampaignStatus.PENDING
)
```

**Fields:**
- `id: UUID`: Campaign ID
- `name: str`: Campaign name
- `campaign_type: CampaignType`: Campaign type
- `message_type: MessageType`: Message type
- `message_text: str`: Message content
- `status: CampaignStatus`: Campaign status
- `start_time: Optional[datetime]`: Scheduled start time
- `rate_limit: int`: Messages per minute
- `created_at: datetime`: Creation timestamp
- `updated_at: datetime`: Update timestamp

#### `CampaignStatus`

Campaign status enumeration.

```python
from app.models import CampaignStatus

CampaignStatus.PENDING
CampaignStatus.RUNNING
CampaignStatus.PAUSED
CampaignStatus.COMPLETED
CampaignStatus.FAILED
CampaignStatus.CANCELLED
```

#### `CampaignType`

Campaign type enumeration.

```python
from app.models import CampaignType

CampaignType.BULK
CampaignType.SCHEDULED
CampaignType.RECURRING
```

#### `MessageType`

Message type enumeration.

```python
from app.models import MessageType

MessageType.TEXT
MessageType.MEDIA
MessageType.COMBINED
```

### Recipient Model

#### `Recipient`

Message recipient model.

```python
from app.models import Recipient

recipient = Recipient(
    username="username",
    phone_number="+1234567890",
    recipient_type=RecipientType.USERNAME
)
```

**Fields:**
- `id: UUID`: Recipient ID
- `username: Optional[str]`: Telegram username
- `phone_number: Optional[str]`: Phone number
- `recipient_type: RecipientType`: Recipient type
- `status: RecipientStatus`: Recipient status
- `source: RecipientSource`: Recipient source
- `created_at: datetime`: Creation timestamp
- `updated_at: datetime`: Update timestamp

#### `RecipientList`

Recipient list model.

```python
from app.models import RecipientList

recipient_list = RecipientList(name="My List")
```

**Fields:**
- `id: UUID`: List ID
- `name: str`: List name
- `description: Optional[str]`: List description
- `created_at: datetime`: Creation timestamp
- `updated_at: datetime`: Update timestamp

### Template Model

#### `MessageTemplate`

Message template model.

```python
from app.models import MessageTemplate

template = MessageTemplate(
    name="Welcome Template",
    content="Hello {name}, welcome!",
    template_type=TemplateType.SPINTAX
)
```

**Fields:**
- `id: UUID`: Template ID
- `name: str`: Template name
- `content: str`: Template content
- `template_type: TemplateType`: Template type
- `category: Optional[TemplateCategory]`: Template category
- `created_at: datetime`: Creation timestamp
- `updated_at: datetime`: Update timestamp

### Send Log Model

#### `SendLog`

Message send log model.

```python
from app.models import SendLog

log = SendLog(
    campaign_id=campaign_id,
    account_id=account_id,
    recipient=recipient,
    status=SendStatus.SUCCESS
)
```

**Fields:**
- `id: UUID`: Log ID
- `campaign_id: UUID`: Campaign ID
- `account_id: UUID`: Account ID
- `recipient: str`: Recipient identifier
- `status: SendStatus`: Send status
- `message: Optional[str]`: Error message
- `sent_at: Optional[datetime]`: Send timestamp
- `created_at: datetime`: Creation timestamp

## Services (`app.services`)

### Settings Service

#### `get_settings() -> Settings`

Get application settings.

```python
from app.services import get_settings

settings = get_settings()
api_id = settings.telegram_api_id
```

#### `Settings`

Application settings class.

```python
from app.services import Settings

settings = Settings()
```

**Fields:**
- `telegram_api_id: str`: Telegram API ID
- `telegram_api_hash: str`: Telegram API hash
- `theme: Theme`: UI theme
- `language: Language`: UI language
- `log_level: LogLevel`: Logging level
- `start_with_windows: bool`: Start with Windows
- `rate_limit_per_minute: int`: Default rate limit

#### `reload_settings() -> Settings`

Reload settings from configuration.

```python
from app.services import reload_settings

settings = reload_settings()
```

### Database Service

#### `initialize_database() -> None`

Initialize database connection.

```python
from app.services import initialize_database

initialize_database()
```

#### `get_session() -> Session`

Get database session.

```python
from app.services import get_session

with get_session() as session:
    accounts = session.query(Account).all()
```

#### `get_async_session() -> AsyncSession`

Get async database session.

```python
from app.services import get_async_session

async with get_async_session() as session:
    result = await session.execute(select(Account))
```

#### `health_check() -> bool`

Check database health.

```python
from app.services import health_check

is_healthy = health_check()
```

#### `backup_database(path: str) -> bool`

Backup database.

```python
from app.services import backup_database

success = backup_database("backup.db")
```

#### `restore_database(path: str) -> bool`

Restore database from backup.

```python
from app.services import restore_database

success = restore_database("backup.db")
```

### Campaign Manager Service

#### `get_campaign_manager() -> CampaignManager`

Get campaign manager instance.

```python
from app.services import get_campaign_manager

manager = get_campaign_manager()
```

#### `CampaignManager`

Manages message campaigns.

```python
from app.services import CampaignManager

manager = CampaignManager()
```

**Methods:**
- `create_campaign(data: dict) -> Campaign`: Create new campaign
- `start_campaign(campaign_id: str) -> bool`: Start campaign
- `pause_campaign(campaign_id: str) -> bool`: Pause campaign
- `stop_campaign(campaign_id: str) -> bool`: Stop campaign
- `get_campaign(campaign_id: str) -> Optional[Campaign]`: Get campaign
- `list_campaigns() -> List[Campaign]`: List all campaigns
- `delete_campaign(campaign_id: str) -> bool`: Delete campaign

### Logger Service

#### `get_logger() -> AppLogger`

Get application logger.

```python
from app.services import get_logger

logger = get_logger()
logger.info("Application started")
```

#### `AppLogger`

Application logger class.

```python
from app.services import AppLogger

logger = AppLogger()
```

**Methods:**
- `info(message: str) -> None`: Log info message
- `warning(message: str) -> None`: Log warning message
- `error(message: str) -> None`: Log error message
- `debug(message: str) -> None`: Log debug message
- `critical(message: str) -> None`: Log critical message

#### `setup_logging(level: LogLevel = LogLevel.INFO) -> None`

Setup logging configuration.

```python
from app.services import setup_logging, LogLevel

setup_logging(LogLevel.DEBUG)
```

### Warmup Manager Service

#### `get_warmup_manager() -> WarmupManager`

Get warmup manager instance.

```python
from app.services import get_warmup_manager

manager = get_warmup_manager()
```

#### `WarmupManager`

Manages account warmup process.

```python
from app.services import WarmupManager

manager = WarmupManager()
```

**Methods:**
- `start_warmup(account_id: str, duration: int = 7) -> bool`: Start warmup
- `stop_warmup(account_id: str) -> bool`: Stop warmup
- `get_warmup_status(account_id: str) -> dict`: Get warmup status
- `is_warming_up(account_id: str) -> bool`: Check if account is warming up

## GUI Module (`app.gui`)

### Main Window

#### `MainWindow`

Main application window.

```python
from app.gui.main import MainWindow

window = MainWindow()
window.show()
```

**Methods:**
- `setup_ui() -> None`: Setup user interface
- `setup_menu() -> None`: Setup menu bar
- `setup_status_bar() -> None`: Setup status bar
- `update_status() -> None`: Update status bar
- `on_language_changed() -> None`: Handle language change

### Theme Manager

#### `ThemeManager`

Manages application themes.

```python
from app.gui.theme import ThemeManager

theme_manager = ThemeManager()
theme_manager.apply_theme(Theme.DARK)
```

**Methods:**
- `apply_theme(theme: Theme) -> None`: Apply theme
- `get_current_theme() -> Theme`: Get current theme
- `get_theme_stylesheet(theme: Theme) -> str`: Get theme stylesheet

## Utilities (`app.utils`)

### Windows Startup

#### `add_to_startup(app_name: str, app_path: str) -> bool`

Add application to Windows startup.

```python
from app.utils.windows_startup import add_to_startup

success = add_to_startup("Telegram Sender", "C:\\path\\to\\app.exe")
```

#### `remove_from_startup(app_name: str) -> bool`

Remove application from Windows startup.

```python
from app.utils.windows_startup import remove_from_startup

success = remove_from_startup("Telegram Sender")
```

#### `is_in_startup(app_name: str) -> bool`

Check if application is in Windows startup.

```python
from app.utils.windows_startup import is_in_startup

in_startup = is_in_startup("Telegram Sender")
```

### File Utilities

#### `read_file(path: str) -> str`

Read file content.

```python
from app.utils.files import read_file

content = read_file("data.txt")
```

#### `write_file(path: str, content: str) -> bool`

Write file content.

```python
from app.utils.files import write_file

success = write_file("data.txt", "content")
```

### Crypto Utilities

#### `encrypt(data: str, key: str) -> str`

Encrypt data.

```python
from app.utils.crypto import encrypt

encrypted = encrypt("sensitive data", "secret_key")
```

#### `decrypt(encrypted_data: str, key: str) -> str`

Decrypt data.

```python
from app.utils.crypto import decrypt

decrypted = decrypt(encrypted_data, "secret_key")
```

## Error Handling

All API methods may raise the following exceptions:

- `ValueError`: Invalid input parameters
- `ConnectionError`: Network connection issues
- `AuthenticationError`: Authentication failures
- `RateLimitError`: Rate limit exceeded
- `ComplianceError`: Compliance check failures

## Examples

See [Examples](examples/example-01.md) and [Examples](examples/example-02.md) for practical usage examples.

## See Also

- [Architecture Documentation](architecture.md) for system design
- [CLI Reference](cli.md) for command-line interface
- [Usage Guide](usage.md) for user documentation

