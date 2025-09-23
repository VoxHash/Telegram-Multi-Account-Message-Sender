# Telegram Multi-Account Message Sender

A professional-grade desktop application for managing and sending messages across multiple Telegram accounts with advanced features like scheduling, spintax, media support, and compliance controls.

## Features

### 🚀 Core Functionality
- **Multi-Account Management**: Manage multiple Telegram accounts simultaneously
- **Campaign Management**: Create, schedule, and manage message campaigns
- **Template System**: Create and manage message templates with spintax support
- **Recipient Management**: Organize and manage recipient lists
- **Message Testing**: Test messages before sending campaigns
- **Comprehensive Logging**: Track all activities with detailed logs

### 🎨 User Interface
- **Modern UI**: Clean, intuitive interface with multiple themes
- **Multi-Language Support**: Available in 8 languages
- **Responsive Design**: Adapts to different screen sizes
- **Dark/Light Themes**: Multiple theme options including Dracula theme

### 🔧 Advanced Features
- **Spintax Support**: Create message variations using spintax syntax
- **A/B Testing**: Test different message variants
- **Scheduling**: Schedule campaigns for specific times
- **Rate Limiting**: Respect Telegram's rate limits
- **Retry Logic**: Automatic retry for failed messages
- **Media Support**: Send text, media, and combined messages

### 🛡️ Safety & Compliance
- **Rate Limiting**: Built-in rate limiting to prevent account bans
- **Error Handling**: Comprehensive error handling and recovery
- **Dry Run Mode**: Test campaigns without sending actual messages
- **Compliance Controls**: Built-in controls for responsible messaging

## Installation

### Prerequisites
- Python 3.10 or higher
- PyQt5
- Telegram API credentials (API ID and API Hash)

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender.git
   cd Telegram-Multi-Account-Message-Sender
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment:**
   ```bash
   cp example_files/env_template.txt .env
   # Edit .env with your Telegram API credentials
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```

### Platform-Specific Installation

#### Windows
- Download the installer from the [Releases](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/releases) page
- Run `TelegramMultiAccountSender-1.0.0-Setup.exe`
- Follow the installation wizard

#### macOS
- Download the DMG file from the [Releases](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/releases) page
- Mount the DMG and drag the app to your Applications folder
- The app will be available in your Applications folder

#### Linux

**Debian/Ubuntu:**
```bash
sudo dpkg -i telegram-multi-account-sender_1.0.0-1_amd64.deb
```

**Arch Linux:**
```bash
pacman -U telegram-multi-account-sender-1.0.0-linux-x86_64.tar.gz
```

**Generic Linux:**
```bash
tar -xzf telegram-multi-account-sender-1.0.0-linux-x86_64.tar.gz
./telegram-sender
```

## Configuration

### Environment Variables
Create a `.env` file in the project root with the following variables:

```env
# Telegram API Configuration
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash

# Database Configuration
DATABASE_URL=sqlite:///./telegram_sender.db

# Logging Configuration
LOG_LEVEL=INFO
LOG_TO_FILE=true
LOG_FILE_MAX_SIZE=10
LOG_FILE_BACKUP_COUNT=5

# Application Configuration
WINDOW_WIDTH=1200
WINDOW_HEIGHT=800
THEME=auto
LANGUAGE=en
```

### Telegram API Setup
1. Go to [my.telegram.org](https://my.telegram.org)
2. Log in with your phone number
3. Go to "API development tools"
4. Create a new application
5. Copy the API ID and API Hash to your `.env` file

## Usage

### Getting Started

1. **Launch the Application**: Run `python main.py` or use the installed executable
2. **Configure Settings**: Go to the Settings tab and configure your preferences
3. **Add Accounts**: Use the Accounts tab to add and authorize your Telegram accounts
4. **Create Templates**: Use the Templates tab to create message templates
5. **Manage Recipients**: Use the Recipients tab to organize your recipient lists
6. **Create Campaigns**: Use the Campaigns tab to create and manage message campaigns
7. **Test Messages**: Use the Testing tab to test your messages before sending
8. **Monitor Logs**: Use the Logs tab to monitor application and send logs

### Account Management

1. **Add Account**: Click "Add Account" in the Accounts tab
2. **Enter Phone Number**: Enter your phone number with country code
3. **Authorize**: Follow the authorization process
4. **Verify**: Enter the verification code sent to your phone
5. **Complete**: Your account will be added and ready to use

### Campaign Management

1. **Create Campaign**: Click "Create Campaign" in the Campaigns tab
2. **Configure Settings**: Set campaign name, type, and message content
3. **Select Recipients**: Choose recipient list or individual recipients
4. **Schedule**: Set start time and rate limits
5. **Launch**: Start, pause, or stop campaigns as needed

### Template System

1. **Create Template**: Click "Create Template" in the Templates tab
2. **Enter Content**: Write your message content with spintax if desired
3. **Configure Settings**: Set template type, category, and tags
4. **Test**: Use the preview feature to test your template
5. **Save**: Save your template for use in campaigns

### Spintax Support

Spintax allows you to create message variations. Use the following syntax:

```
Hello {John|Jane|Alex}, welcome to {our|my} {amazing|fantastic|great} service!
```

This will generate variations like:
- "Hello John, welcome to our amazing service!"
- "Hello Jane, welcome to my fantastic service!"
- "Hello Alex, welcome to our great service!"

## API Reference

### Models

#### Account
```python
class Account(BaseModel):
    phone_number: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    status: AccountStatus = AccountStatus.OFFLINE
    # ... other fields
```

#### Campaign
```python
class Campaign(BaseModel):
    name: str
    description: Optional[str] = None
    campaign_type: CampaignType = CampaignType.TEXT
    status: CampaignStatus = CampaignStatus.DRAFT
    # ... other fields
```

#### MessageTemplate
```python
class MessageTemplate(BaseModel):
    name: str
    content: str
    template_type: TemplateType = TemplateType.TEXT
    category: TemplateCategory = TemplateCategory.GENERAL
    # ... other fields
```

### Services

#### CampaignManager
```python
class CampaignManager:
    def start_campaign(self, campaign_id: int) -> bool
    def pause_campaign(self, campaign_id: int) -> bool
    def stop_campaign(self, campaign_id: int) -> bool
    def retry_campaign(self, campaign_id: int) -> bool
    def duplicate_campaign(self, campaign_id: int) -> Optional[Campaign]
```

#### MessageEngine
```python
class MessageEngine:
    def send_message(self, account: Account, recipient: Recipient, message: str) -> bool
    def send_media(self, account: Account, recipient: Recipient, media_path: str, caption: str) -> bool
```

## Development

### Setting Up Development Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender.git
   cd Telegram-Multi-Account-Message-Sender
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Set up pre-commit hooks:**
   ```bash
   pre-commit install
   ```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_campaigns.py

# Run with coverage
pytest --cov=app tests/
```

### Code Style

The project uses the following tools for code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking

Run these tools before committing:

```bash
black app/
isort app/
flake8 app/
mypy app/
```

### Building

```bash
# Build package
python -m build

# Build installers
python build_installers.py
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### How to Contribute

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `pytest`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Reporting Issues

Please use our [Issue Templates](.github/ISSUE_TEMPLATE/) when reporting bugs or requesting features.

## License

This project is licensed under the BSD 3-Clause License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This application is for educational and legitimate business purposes only. Users are responsible for complying with Telegram's Terms of Service and applicable laws. The developers are not responsible for any misuse of this application.

## Support

- **Documentation**: [GitHub Wiki](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/wiki)
- **Issues**: [GitHub Issues](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/issues)
- **Discussions**: [GitHub Discussions](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/discussions)
- **Email**: contact@voxhash.dev

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes and version history.

## Acknowledgments

- [Telethon](https://github.com/LonamiWebs/Telethon) - Telegram client library
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - GUI framework
- [SQLModel](https://github.com/tiangolo/sqlmodel) - Database ORM
- [Rich](https://github.com/Textualize/rich) - Rich text and beautiful formatting

---

Made with ❤️ by [VoxHash](https://voxhash.dev)