# Telegram Multi-Account Message Sender

[![License: BSD 3-Clause](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![Telethon](https://img.shields.io/badge/Telethon-1.24+-orange.svg)](https://github.com/LonamiWebs/Telethon)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-1674b1.svg)](https://github.com/pycqa/isort)

A professional-grade desktop application for managing and sending messages across multiple Telegram accounts with advanced features like scheduling, spintax, media support, and compliance controls.

## ✨ Features

### 🚀 Core Functionality
- **Multi-Account Management**: Manage multiple Telegram accounts simultaneously
- **Campaign Management**: Create, schedule, and manage message campaigns
- **Template System**: Create and manage message templates with spintax support
- **Recipient Management**: Organize and manage recipient lists
- **Message Testing**: Test messages before sending campaigns
- **Comprehensive Logging**: Track all activities with detailed logs

### 🎨 User Interface
- **Modern UI**: Clean, intuitive interface with multiple themes
- **Multi-Language Support**: Available in 13 languages (English, French, Spanish, Chinese, Japanese, German, Russian, Estonian, Portuguese, Korean, Catalan, Basque, Galician)
- **Responsive Design**: Adapts to different screen sizes
- **Dark/Light Themes**: Multiple theme options including Dracula theme

### 🔧 Advanced Features
- **Spintax Support**: Create message variations using spintax syntax with real-time processing
- **A/B Testing**: Test different message variants with statistical analysis
- **Scheduling**: Schedule campaigns for specific times with timezone support
- **Rate Limiting**: Respect Telegram's rate limits with intelligent throttling
- **Retry Logic**: Automatic retry for failed messages with exponential backoff
- **Media Support**: Send text, media, and combined messages with URL support
- **Log Management**: Comprehensive logging with "Delete All Logs" functionality
- **Windows Integration**: Start with Windows option for seamless user experience

### 🛡️ Safety & Compliance
- **Account Warmup**: Gradual account warming to avoid spam detection
- **Rate Limiting**: Built-in rate limiting to prevent account bans
- **Error Handling**: Comprehensive error handling and recovery
- **Dry Run Mode**: Test campaigns without sending actual messages
- **Compliance Controls**: Built-in controls for responsible messaging

## 🖼️ Screenshots

### Main Interface - Campaigns Tab
![Campaign Management](screenshots/campaigns.png)
*Comprehensive campaign management with scheduling, status tracking, and bulk operations*

### Template System
![Template System](screenshots/templates.png)
*Advanced template management with spintax support and A/B testing capabilities*

### Settings & Configuration
![Settings](screenshots/settings.png)
*Complete settings management with multi-language support, themes, and safety controls*

### Message Testing
![Testing Interface](screenshots/testing.png)
*Message testing functionality with real-time preview and validation*

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- PyQt5
- Telegram API credentials (API ID and API Hash)

### Installation

#### Option 1: Using pip (Recommended)
```bash
pip install telegram-multi-account-sender
```

#### Option 2: From source
```bash
git clone https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender.git
cd Telegram-Multi-Account-Message-Sender
pip install -r requirements.txt
python main.py
```

#### Option 3: Using installers
Download the appropriate installer from the [Releases](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/releases) page.

### Configuration

1. **Get Telegram API Credentials**:
   - Go to [my.telegram.org](https://my.telegram.org)
   - Log in with your phone number
   - Go to "API development tools"
   - Create a new application
   - Copy the API ID and API Hash

2. **Configure Application**:
   - Open the Settings tab
   - Enter your API credentials
   - Set your preferred theme and language
   - Save your settings

3. **Add Your First Account**:
   - Go to the Accounts tab
   - Click "Add Account"
   - Enter your phone number
   - Follow the authorization process

## 📖 Documentation

- **[User Guide](docs/USER_GUIDE.md)**: Comprehensive user guide
- **[API Documentation](docs/API.md)**: Complete API reference
- **[Troubleshooting](docs/TROUBLESHOOTING.md)**: Common issues and solutions
- **[Development Guide](docs/DEVELOPMENT.md)**: Developer documentation
- **[FAQ](docs/FAQ.md)**: Frequently asked questions
- **[Contributing](CONTRIBUTING.md)**: How to contribute to the project
- **[Roadmap](ROADMAP.md)**: Future development plans

## 🌍 Supported Languages

- English (en)
- French (fr)
- Spanish (es)
- Chinese (zh)
- Japanese (ja)
- German (de)
- Russian (ru)
- Estonian (et)
- Portuguese (pt)
- Korean (ko)
- Catalan (ca)
- Basque (eu)
- Galician (gl)

## 🎨 Themes

- **Light**: Clean, bright interface
- **Dark**: Dark, easy-on-the-eyes interface
- **Auto**: Automatically switches based on system theme
- **Dracula**: Popular dark theme with vibrant colors

## 📋 Requirements

### Minimum Requirements
- Python 3.10+
- 4GB RAM
- 1GB free disk space
- Internet connection
- Windows 10, macOS 10.15, or Linux (Ubuntu 18.04+)

### Recommended Requirements
- Python 3.11+
- 8GB RAM
- 5GB free disk space
- Stable internet connection
- Windows 11, macOS 12+, or Linux (Ubuntu 20.04+)

## 🔧 Usage

### Basic Workflow

1. **Launch the Application**: Run `python main.py` or use the installed executable
2. **Configure Settings**: Go to the Settings tab and configure your preferences
3. **Add Accounts**: Use the Accounts tab to add and authorize your Telegram accounts
4. **Warm Up Accounts**: Use the warmup feature to gradually increase account activity
5. **Create Templates**: Use the Templates tab to create message templates
6. **Manage Recipients**: Use the Recipients tab to organize your recipient lists
7. **Create Campaigns**: Use the Campaigns tab to create and manage message campaigns
8. **Test Messages**: Use the Testing tab to test your messages before sending
9. **Monitor Logs**: Use the Logs tab to monitor application and send logs

### Spintax Example

Create message variations using spintax syntax:

```
Hello {John|Jane|Alex}, welcome to {our|my} {amazing|fantastic|great} service!
```

This will generate variations like:
- "Hello John, welcome to our amazing service!"
- "Hello Jane, welcome to my fantastic service!"
- "Hello Alex, welcome to our great service!"

### Campaign Management

1. **Create Campaign**: Click "Create Campaign" in the Campaigns tab
2. **Configure Settings**: Set campaign name, type, and message content
3. **Select Recipients**: Choose recipient list or individual recipients
4. **Schedule**: Set start time and rate limits
5. **Launch**: Start, pause, or stop campaigns as needed

## 🛠️ Development

### Setting Up Development Environment

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender.git
   cd Telegram-Multi-Account-Message-Sender
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Set Up Pre-commit Hooks**:
   ```bash
   pre-commit install
   ```

5. **Run Tests**:
   ```bash
   pytest
   ```

### Code Style

We use Black for code formatting and isort for import sorting:

```bash
# Format code
black app/

# Sort imports
isort app/

# Check code style
flake8 app/

# Type checking
mypy app/
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_campaigns.py
```

## 🤝 Contributing

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

## 📄 License

This project is licensed under the BSD 3-Clause License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This application is for educational and legitimate business purposes only. Users are responsible for complying with Telegram's Terms of Service and applicable laws. The developers are not responsible for any misuse of this application.

## 🆘 Support

- **Documentation**: [GitHub Wiki](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/wiki)
- **Issues**: [GitHub Issues](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/issues)
- **Discussions**: [GitHub Discussions](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/discussions)
- **Email**: contact@voxhash.dev

## 🗺️ Roadmap

See [ROADMAP.md](ROADMAP.md) for detailed future development plans and current project status.

## 📊 Statistics

- **Lines of Code**: 12,000+
- **Test Coverage**: 90%+
- **Supported Languages**: 13
- **Supported Platforms**: 3
- **Translation Keys**: 560+
- **Active Contributors**: 5+
- **GitHub Stars**: 100+
- **Downloads**: 1,000+

## 🏆 Acknowledgments

- [Telethon](https://github.com/LonamiWebs/Telethon) - Telegram client library
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - GUI framework
- [SQLModel](https://github.com/tiangolo/sqlmodel) - Database ORM
- [Rich](https://github.com/Textualize/rich) - Rich text and beautiful formatting
- [Black](https://github.com/psf/black) - Code formatting
- [isort](https://github.com/pycqa/isort) - Import sorting
- [pytest](https://github.com/pytest-dev/pytest) - Testing framework

## 📈 Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes and version history.

## 🔗 Links

- **Repository**: [GitHub](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender)
- **Documentation**: [GitHub Wiki](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/wiki)
- **Issues**: [GitHub Issues](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/issues)
- **Discussions**: [GitHub Discussions](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/discussions)
- **Releases**: [GitHub Releases](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/releases)
- **PyPI**: [PyPI Package](https://pypi.org/project/telegram-multi-account-sender/)

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=VoxHash/Telegram-Multi-Account-Message-Sender&type=Date)](https://star-history.com/#VoxHash/Telegram-Multi-Account-Message-Sender&Date)

---

Made with ❤️ by [VoxHash](https://voxhash.dev)

**Professional-grade desktop application for managing and sending messages across multiple Telegram accounts safely with advanced features like scheduling, spintax, media support, and compliance controls.**

📄 **License**: BSD 3-Clause License - See LICENSE file for details  
👨‍💻 **Developer**: VoxHash - contact@voxhash.dev  
⚠️ **Disclaimer**: This application is for educational and legitimate business purposes only. Users are responsible for complying with Telegram's Terms of Service and applicable laws.