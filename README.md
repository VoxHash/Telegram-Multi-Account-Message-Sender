# 🚀 Telegram Multi-Account Message Sender

> **Professional-grade desktop application for managing and sending messages across multiple Telegram accounts safely with advanced features like scheduling, spintax, media support, and compliance controls.**

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://python.org/)
[![PyQt5](https://img.shields.io/badge/pyqt5-5.15+-blue.svg)](https://pypi.org/project/PyQt5/)

## ✨ Features

### 🏦 **Account Management**
- **Multi-Account Support**: Manage unlimited Telegram accounts
- **Proxy Support**: SOCKS5/HTTP proxy configuration per account
- **Rate Limiting**: Per-account and global rate limiting
- **Account Warmup**: Gradual account warming for new accounts
- **Status Monitoring**: Real-time account status and health tracking
- **Secure Storage**: Encrypted session and credential storage

### 📢 **Campaign System**
- **Campaign Builder**: Intuitive campaign creation with tabbed interface
- **Message Editor**: Rich text editor with spintax support
- **A/B Testing**: Multi-variant testing with split percentages
- **Scheduling**: Advanced scheduling with timezone support
- **Media Support**: Attach images, videos, and documents
- **Template System**: Reusable message templates with variables

### 👥 **Recipient Management**
- **Individual Management**: Add, edit, and organize recipients
- **CSV Import**: Bulk import with column mapping
- **Tag System**: Organize recipients with custom tags
- **Search & Filter**: Advanced filtering and search capabilities
- **Status Tracking**: Track message delivery and engagement

### 📊 **Analytics & Logging**
- **Real-time Logs**: Live application and send logs
- **Analytics Dashboard**: Campaign performance metrics
- **Export Functionality**: CSV export for external analysis
- **Status Tracking**: Detailed delivery status and error reporting
- **Audit Trail**: Complete activity logging for compliance

### 🔒 **Safety & Compliance**
- **Rate Limiting**: Respect Telegram's rate limits
- **Compliance Checking**: Built-in spam detection and warnings
- **Safety Guardrails**: Conservative defaults and safety controls
- **Dry Run Mode**: Test campaigns without sending messages
- **Error Handling**: Comprehensive error handling and recovery

### 🎨 **User Interface**
- **Modern GUI**: Professional PyQt5 interface
- **Theme Support**: Light/dark theme with system detection
- **Responsive Design**: Adaptive layout for different screen sizes
- **Keyboard Shortcuts**: Efficient keyboard navigation
- **Real-time Updates**: Live status updates and notifications

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+**
- **Windows 10/11, macOS 10.15+, or Linux**
- **Telegram API credentials** (get from [my.telegram.org](https://my.telegram.org))

### Installation

#### Method 1: Clone and Install
```bash
# Clone the repository
git clone https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender.git
cd Telegram-Multi-Account-Message-Sender

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

#### Method 2: Development Installation
```bash
# Install in development mode
pip install -e .

# Run the application
python main.py
```

### Configuration

1. **Copy environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` file** with your Telegram API credentials:
   ```ini
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   ```

3. **Launch the application**:
   ```bash
   python main.py
   ```

## 📖 Usage

### Adding Accounts
1. Go to **Accounts** tab
2. Click **Add Account**
3. Enter account details (phone, API credentials)
4. Configure proxy settings (optional)
5. Set rate limits and warmup settings
6. Click **Save**

### Creating Campaigns
1. Go to **Campaigns** tab
2. Click **Create Campaign**
3. Fill in campaign details:
   - **Basic Info**: Name, description, type
   - **Message**: Text with spintax support
   - **Scheduling**: Start time and rate limits
   - **Recipients**: Select recipient source
4. Click **Save** and **Start**

### Managing Recipients
1. Go to **Recipients** tab
2. **Add manually** or **Import CSV**
3. Organize with tags and notes
4. Use search and filters to find specific recipients

### Monitoring Logs
1. Go to **Logs** tab
2. View **Application Logs** for system events
3. View **Send Logs** for message delivery status
4. Use filters to find specific events
5. Export logs for analysis

## 🛠️ Development

### Project Structure
```
app/
├── core/           # Core business logic
│   ├── engine.py   # Main orchestration
│   ├── telethon_client.py  # Telegram client management
│   ├── throttler.py        # Rate limiting
│   ├── spintax.py          # Message personalization
│   ├── compliance.py       # Safety checks
│   └── analytics.py        # Performance tracking
├── gui/            # User interface
│   ├── main.py     # Main window
│   ├── theme.py    # Theme management
│   └── widgets/    # UI components
├── models/         # Database models
├── services/       # Core services
└── utils/          # Utility functions
```

### Building
```bash
# Install build dependencies
pip install -r requirements.txt

# Run tests
pytest

# Build with Nuitka
python scripts/build_nuitka.py
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 📋 Requirements

### System Requirements
- **Python**: 3.10 or higher
- **OS**: Windows 10+, macOS 10.15+, or Linux
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 100MB for application, additional for media

### Dependencies
- **PyQt5**: GUI framework
- **Telethon**: Telegram API client
- **SQLModel**: Database ORM
- **Pydantic**: Settings management
- **Rich**: Logging and console output
- **Pandas**: Data processing
- **Cryptography**: Secure storage

## 🔒 Security

### Data Protection
- **Encrypted Storage**: All sensitive data is encrypted
- **Secure Sessions**: Telegram sessions stored securely
- **No Cloud Storage**: All data stays on your device
- **Privacy First**: No data collection or tracking

### Best Practices
- Use strong passwords for Telegram accounts
- Enable 2FA on all accounts
- Use proxies for additional security
- Monitor account health regularly
- Respect Telegram's terms of service

## 📚 Documentation

- **[Installation Guide](docs/README.md)**: Detailed setup instructions
- **[Contributing Guide](CONTRIBUTING.md)**: How to contribute to the project
- **[Development Roadmap](ROADMAP.md)**: Future development plans
- **[Changelog](CHANGELOG.md)**: Version history and updates

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Areas for Contribution
- **Bug Fixes**: Report and fix issues
- **Features**: Add new functionality
- **Documentation**: Improve documentation
- **Testing**: Add tests and improve coverage
- **UI/UX**: Improve user experience

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/issues)
- **Discussions**: [GitHub Discussions](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/discussions)
- **Email**: contact@voxhash.dev

## ⚠️ Disclaimer

This application is for educational and legitimate business purposes only. Users are responsible for complying with Telegram's Terms of Service and applicable laws. The developers are not responsible for any misuse of this software.

## 🎉 Acknowledgments

- **Telethon**: Telegram API client
- **PyQt5**: GUI framework
- **SQLModel**: Database ORM
- **Pydantic**: Settings management
- **Rich**: Beautiful logging
- **Community**: Feedback and contributions

---

**Made with ❤️ by VoxHash**

*Professional Telegram automation made simple!* 🚀