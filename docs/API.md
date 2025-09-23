# API Documentation

## Overview

This document provides comprehensive API documentation for the Telegram Multi-Account Message Sender application.

## Table of Contents

- [Models](#models)
- [Services](#services)
- [GUI Components](#gui-components)
- [Utilities](#utilities)
- [Configuration](#configuration)

## Models

### Account

Represents a Telegram account in the system.

```python
class Account(BaseModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    phone_number: str = Field(unique=True, index=True)
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    status: AccountStatus = AccountStatus.OFFLINE
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen: Optional[datetime] = None
    session_string: Optional[str] = None
    proxy_type: Optional[ProxyType] = None
    proxy_host: Optional[str] = None
    proxy_port: Optional[int] = None
    proxy_username: Optional[str] = None
    proxy_password: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[str] = Field(default=None, sa_column=JSON)
```

**Methods:**
- `get_tags_list() -> List[str]`: Get list of tags
- `set_tags_list(tags: List[str])`: Set tags from list
- `is_online() -> bool`: Check if account is online
- `get_display_name() -> str`: Get display name for UI

### Campaign

Represents a message campaign.

```python
class Campaign(BaseModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    campaign_type: CampaignType = CampaignType.TEXT
    status: CampaignStatus = CampaignStatus.DRAFT
    message_text: Optional[str] = None
    message_type: MessageType = MessageType.TEXT
    media_path: Optional[str] = None
    caption: Optional[str] = None
    use_spintax: bool = False
    spintax_text: Optional[str] = None
    use_ab_testing: bool = False
    ab_variants: Optional[str] = Field(default=None, sa_column=JSON)
    ab_split_percentages: Optional[str] = Field(default=None, sa_column=JSON)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    timezone: str = "UTC"
    messages_per_minute: int = 1
    messages_per_hour: int = 60
    messages_per_day: int = 1000
    random_jitter_seconds: int = 0
    account_selection_strategy: str = "round_robin"
    account_weights: Optional[str] = Field(default=None, sa_column=JSON)
    max_concurrent_accounts: int = 5
    recipient_source: str = "manual"
    recipient_list_id: Optional[int] = None
    recipient_filters: Optional[str] = Field(default=None, sa_column=JSON)
    dry_run: bool = False
    respect_rate_limits: bool = True
    stop_on_error: bool = False
    max_retries: int = 3
    total_recipients: int = 0
    sent_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    progress_percentage: float = 0.0
    start_time_actual: Optional[datetime] = None
    end_time_actual: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    is_active: bool = True
    tags: Optional[str] = Field(default=None, sa_column=JSON)
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

**Methods:**
- `can_start() -> bool`: Check if campaign can be started
- `can_pause() -> bool`: Check if campaign can be paused
- `can_resume() -> bool`: Check if campaign can be resumed
- `can_stop() -> bool`: Check if campaign can be stopped
- `get_ab_variants_list() -> List[str]`: Get A/B testing variants
- `set_ab_variants_list(variants: List[str])`: Set A/B testing variants
- `get_ab_split_percentages_list() -> List[float]`: Get A/B testing split percentages
- `set_ab_split_percentages_list(percentages: List[float])`: Set A/B testing split percentages
- `get_account_weights_dict() -> Dict[int, float]`: Get account weights
- `set_account_weights_dict(weights: Dict[int, float])`: Set account weights
- `get_recipient_filters_dict() -> Dict[str, Any]`: Get recipient filters
- `set_recipient_filters_dict(filters: Dict[str, Any])`: Set recipient filters
- `get_tags_list() -> List[str]`: Get list of tags
- `set_tags_list(tags: List[str])`: Set tags from list

### MessageTemplate

Represents a message template.

```python
class MessageTemplate(BaseModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    content: str
    template_type: TemplateType = TemplateType.TEXT
    category: TemplateCategory = TemplateCategory.GENERAL
    use_spintax: bool = False
    spintax_text: Optional[str] = None
    variables: Optional[str] = Field(default=None, sa_column=JSON)
    is_active: bool = True
    tags: Optional[str] = Field(default=None, sa_column=JSON)
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

**Methods:**
- `get_variables_list() -> List[str]`: Get list of variables
- `set_variables_list(variables: List[str])`: Set variables from list
- `get_tags_list() -> List[str]`: Get list of tags
- `set_tags_list(tags: List[str])`: Set tags from list

### Recipient

Represents a message recipient.

```python
class Recipient(BaseModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    recipient_type: RecipientType = RecipientType.USER
    phone_number: Optional[str] = None
    username: Optional[str] = None
    user_id: Optional[int] = None
    group_id: Optional[int] = None
    group_type: Optional[str] = None
    member_count: Optional[int] = None
    source: RecipientSource = RecipientSource.MANUAL
    status: RecipientStatus = RecipientStatus.ACTIVE
    tags: Optional[str] = Field(default=None, sa_column=JSON)
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

**Methods:**
- `get_tags_list() -> List[str]`: Get list of tags
- `set_tags_list(tags: List[str])`: Set tags from list
- `get_display_name() -> str`: Get display name for UI

### RecipientList

Represents a collection of recipients.

```python
class RecipientList(BaseModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    recipient_ids: Optional[str] = Field(default=None, sa_column=JSON)
    is_active: bool = True
    tags: Optional[str] = Field(default=None, sa_column=JSON)
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

**Methods:**
- `get_recipient_ids_list() -> List[int]`: Get list of recipient IDs
- `set_recipient_ids_list(recipient_ids: List[int])`: Set recipient IDs from list
- `get_tags_list() -> List[str]`: Get list of tags
- `set_tags_list(tags: List[str])`: Set tags from list

### SendLog

Represents a log entry for sent messages.

```python
class SendLog(BaseModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: Optional[int] = Field(default=None, foreign_key="campaigns.id")
    account_id: Optional[int] = Field(default=None, foreign_key="accounts.id")
    recipient_id: Optional[int] = Field(default=None, foreign_key="recipients.id")
    message_text: str
    message_type: MessageType = MessageType.TEXT
    media_path: Optional[str] = None
    status: SendStatus = SendStatus.PENDING
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

## Services

### CampaignManager

Manages campaign lifecycle and operations.

```python
class CampaignManager:
    def __init__(self):
        self.logger = get_logger()
        self._running_campaigns: Dict[int, threading.Thread] = {}
        self._campaign_stop_events: Dict[int, threading.Event] = {}
        self._campaign_pause_events: Dict[int, threading.Event] = {}
        self._campaign_progress: Dict[int, Dict[str, Any]] = {}
```

**Methods:**
- `start_campaign(campaign_id: int) -> bool`: Start a campaign
- `pause_campaign(campaign_id: int) -> bool`: Pause a running campaign
- `resume_campaign(campaign_id: int) -> bool`: Resume a paused campaign
- `stop_campaign(campaign_id: int) -> bool`: Stop a running campaign
- `retry_campaign(campaign_id: int) -> bool`: Retry a failed campaign
- `duplicate_campaign(campaign_id: int) -> Optional[Campaign]`: Duplicate a completed campaign
- `is_campaign_running(campaign_id: int) -> bool`: Check if campaign is running
- `can_retry_campaign(campaign_id: int) -> bool`: Check if campaign can be retried
- `get_campaign_progress(campaign_id: int) -> Dict[str, Any]`: Get campaign progress
- `_run_campaign(campaign_id: int)`: Internal method to run campaign

### MessageEngine

Handles message sending operations.

```python
class MessageEngine:
    def __init__(self):
        self.logger = get_logger()
        self.client_manager = TelegramClientManager()
```

**Methods:**
- `send_message(account: Account, recipient: Recipient, message: str) -> bool`: Send text message
- `send_media(account: Account, recipient: Recipient, media_path: str, caption: str) -> bool`: Send media message
- `_send_to_user(account: Account, recipient: Recipient, message: str) -> bool`: Send to user
- `_send_to_group(account: Account, recipient: Recipient, message: str) -> bool`: Send to group
- `_send_to_channel(account: Account, recipient: Recipient, message: str) -> bool`: Send to channel

### TelegramClientManager

Manages Telegram client connections.

```python
class TelegramClientManager:
    def __init__(self):
        self.logger = get_logger()
        self._clients: Dict[int, TelegramClient] = {}
        self._client_sessions: Dict[int, str] = {}
```

**Methods:**
- `add_account(phone_number: str, session_string: Optional[str] = None) -> bool`: Add account
- `remove_account(account_id: int) -> bool`: Remove account
- `get_client(account_id: int) -> Optional[TelegramClient]`: Get client for account
- `is_connected(account_id: int) -> bool`: Check if account is connected
- `disconnect_all() -> None`: Disconnect all clients

### TranslationManager

Manages application translations.

```python
class TranslationManager(QObject):
    language_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self._translations: Dict[str, Any] = {}
        self._current_language: str = "en"
```

**Methods:**
- `load_translations(lang_code: str) -> None`: Load translations for language
- `set_language(lang_code: str) -> None`: Set current language
- `translate(key: str) -> str`: Translate a key

## GUI Components

### MainWindow

Main application window.

```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.logger = get_logger()
        self.theme_manager = ThemeManager()
        self.translation_manager = get_translation_manager()
```

**Methods:**
- `setup_ui() -> None`: Set up user interface
- `setup_menu() -> None`: Set up menu bar
- `setup_status_bar() -> None`: Set up status bar
- `on_language_changed(language: str) -> None`: Handle language change
- `on_settings_updated() -> None`: Handle settings update
- `update_status() -> None`: Update status bar
- `get_application_status() -> str`: Get application status
- `format_theme_name(theme: str) -> str`: Format theme name for display

### CampaignWidget

Campaign management widget.

```python
class CampaignWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.campaign_manager = CampaignManager()
        self.setup_ui()
```

**Methods:**
- `setup_ui() -> None`: Set up user interface
- `load_campaigns() -> None`: Load campaigns from database
- `create_campaign() -> None`: Create new campaign
- `edit_campaign() -> None`: Edit selected campaign
- `delete_campaign() -> None`: Delete selected campaign
- `start_campaign() -> None`: Start selected campaign
- `pause_campaign() -> None`: Pause selected campaign
- `stop_campaign() -> None`: Stop selected campaign
- `retry_campaign() -> None`: Retry selected campaign
- `duplicate_campaign() -> None`: Duplicate selected campaign
- `refresh_campaigns() -> None`: Refresh campaign list
- `update_button_states() -> None`: Update button states
- `on_context_menu(position: QPoint) -> None`: Handle context menu
- `on_campaign_selection_changed() -> None`: Handle selection change

### AccountWidget

Account management widget.

```python
class AccountWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.client_manager = TelegramClientManager()
        self.setup_ui()
```

**Methods:**
- `setup_ui() -> None`: Set up user interface
- `load_accounts() -> None`: Load accounts from database
- `add_account() -> None`: Add new account
- `edit_account() -> None`: Edit selected account
- `delete_account() -> None`: Delete selected account
- `authorize_account() -> None`: Authorize selected account
- `refresh_accounts() -> None`: Refresh account list
- `update_button_states() -> None`: Update button states
- `on_context_menu(position: QPoint) -> None`: Handle context menu
- `on_account_selection_changed() -> None`: Handle selection change

## Utilities

### SpintaxProcessor

Processes spintax syntax for message variations.

```python
class SpintaxProcessor:
    def __init__(self):
        self.logger = get_logger()
    
    def validate_spintax(self, text: str) -> Tuple[bool, str, int]:
        """Validate spintax syntax and return validation result."""
        pass
    
    def get_preview_samples(self, text: str, count: int = 5) -> List[str]:
        """Generate preview samples from spintax text."""
        pass
    
    def _extract_variants(self, text: str) -> List[str]:
        """Extract variants from spintax text."""
        pass
```

### ThemeManager

Manages application themes.

```python
class ThemeManager:
    def __init__(self):
        self.settings = get_settings()
        self.current_theme = self.settings.theme.value
        self._load_theme()
    
    def apply_theme(self, theme: str) -> None:
        """Apply theme to application."""
        pass
    
    def get_current_theme(self) -> str:
        """Get current theme."""
        pass
    
    def _load_theme(self) -> None:
        """Load theme from settings."""
        pass
```

## Configuration

### Settings

Application settings management.

```python
class Settings(BaseSettings):
    # Application settings
    debug_mode: bool = False
    window_width: int = 1200
    window_height: int = 800
    maximized_window: bool = False
    
    # Theme settings
    theme: Theme = Theme.AUTO
    
    # Language settings
    language: Language = Language.ENGLISH
    
    # Logging settings
    log_level: LogLevel = LogLevel.INFO
    log_to_file: bool = True
    log_file_max_size: int = 10
    log_file_backup_count: int = 5
    
    # Database settings
    database_url: str = "sqlite:///./telegram_sender.db"
    
    # Telegram API settings
    telegram_api_id: Optional[int] = None
    telegram_api_hash: Optional[str] = None
    
    # Rate limiting settings
    default_rate_limits: int = 1
    max_messages_per_hour: int = 60
    max_messages_per_day: int = 1000
    global_max_concurrency: int = 5
    
    # Warmup settings
    warmup_enabled: bool = False
    warmup_messages: int = 5
    warmup_interval_minutes: int = 60
    
    # Safety settings
    respect_rate_limits: bool = True
    stop_on_error: bool = False
    max_retries: int = 3
    retry_delay_seconds: int = 5
```

## Error Handling

The application uses comprehensive error handling throughout:

- **Database Errors**: Handled with try-catch blocks and proper session management
- **Network Errors**: Handled with retry logic and timeout management
- **Validation Errors**: Handled with input validation and user feedback
- **File Errors**: Handled with proper file existence checks and permissions
- **Threading Errors**: Handled with proper thread management and cleanup

## Logging

The application uses structured logging with different levels:

- **DEBUG**: Detailed information for debugging
- **INFO**: General information about application flow
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for recoverable errors
- **CRITICAL**: Critical errors that may cause application failure

Logs are written to both console and file (if enabled) with rotation support.

## Threading

The application uses threading for:

- **Campaign Execution**: Each campaign runs in its own thread
- **Telegram Operations**: Async operations are handled in separate threads
- **UI Updates**: UI updates are handled in the main thread
- **Background Tasks**: Logging and monitoring run in background threads

Proper thread synchronization is maintained using:
- `threading.Event` for stop/pause signals
- `threading.Lock` for shared resource access
- `pyqtSignal` for thread-safe UI updates
