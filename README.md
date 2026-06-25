# Telegram Multi-Account Message Sender

[![CI/CD Pipeline](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/actions/workflows/ci.yml/badge.svg)](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/actions/workflows/ci.yml)
[![License: EPL-2.0](https://img.shields.io/badge/License-EPL--2.0-blue.svg)](https://opensource.org/licenses/EPL-2.0)
[![Made with ❤️ by VoxHash](https://img.shields.io/badge/Made%20with%20❤️%20by-VoxHash%20Technologies-red.svg)](https://voxhash.dev)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)](https://www.docker.com/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![Telethon](https://img.shields.io/badge/Telethon-1.24+-orange.svg)](https://github.com/LonamiWebs/Telethon)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-1674b1.svg)](https://github.com/pycqa/isort)
[![GitHub Sponsors](https://img.shields.io/github/sponsors/VoxHash?label=Sponsors&logo=github&color=ea4aaa)](https://github.com/sponsors/VoxHash)

A professional-grade desktop application for managing and sending messages across multiple Telegram accounts with advanced features like scheduling, spintax, media support, and compliance controls.

---

## ☁️ SendGram — Hosted Telegram Campaign SaaS

**Run multi-account Telegram outreach in the cloud — no desktop install, no server maintenance.**

[SendGram](https://www.sendgram.pro) is the managed SaaS edition built on the same pacing discipline and campaign workflow as this project. Teams that outgrow a single desktop get multi-tenant hosting, role-based access, and production-grade delivery infrastructure.

### Why teams choose SendGram over self-hosting

- **Multi-tenant Telegram campaign automation** — connect accounts, recipients, and paced sends from one secure web app
- **Team collaboration built in** — owner, admin, and operator roles with per-org encryption at rest
- **Hosted delivery workers** — background Telethon send jobs, scheduling, pause/resume, and delivery analytics without managing Fly.io or VPS
- **Enterprise-ready integrations** — API keys, HMAC webhooks, and dual billing (LicenseChain Pay)
- **Self-serve growth tools** — recipient segments, campaign templates, usage alerts, and guided onboarding
- **Production SLA path** — live at [sendgram.pro](https://www.sendgram.pro) with CI/CD, Supabase Postgres, and platform admin controls

> **Prefer the desktop app?** Keep using TMMS locally. **Need a team, API, or always-on delivery?** SendGram is the upgrade path.


|     |
| --- |
|     |


**Start free — no credit card required**

[→ Launch SendGram](https://www.sendgram.pro)



**Compare plans & features**

[→ View pricing](https://www.sendgram.pro/#pricing)



---

## ✨ Features

### 🚀 Core Functionality

- **Multi-Account Management**: Manage multiple Telegram accounts simultaneously with proxy support
- **Account Import Methods**: Add accounts via phone number or by importing Telethon session files
- **Proxy Support**: Full proxy support (HTTP, HTTPS, SOCKS4, SOCKS5) with connection testing
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

Campaign Management
*Comprehensive campaign management with scheduling, status tracking, and bulk operations*

### Template System

Template System
*Advanced template management with spintax support and A/B testing capabilities*

### Settings & Configuration

Settings
*Complete settings management with multi-language support, themes, and safety controls*

### Message Testing

Testing Interface
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

#### Option 3: Using Docker

```bash
# Build the Docker image
docker build -t telegram-sender .

# Run the container
docker run -it --rm \
  -v $(pwd)/app_data:/app/app_data \
  -v $(pwd)/.env:/app/.env \
  telegram-sender
```

#### Option 4: Using installers

Download the appropriate installer from the [Releases](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/releases) page.

### Configuration

1. **Get Telegram API Credentials**:
  - Go to [my.telegram.org](https://my.telegram.org)
  - Log in with your phone number
  - Go to "API development tools"
  - Create a new application
  - Copy the API ID and API Hash
2. **Set Up Environment Variables**:
  ```bash
   # Copy the example environment file
   cp example_files/env_template.txt .env

   # Edit .env and add your credentials
   # ⚠️ SENSITIVE: TELEGRAM_API_ID and TELEGRAM_API_HASH must be kept secret
  ```
3. **Configure Application**:
  - Open the Settings tab
  - Enter your API credentials (or they'll be loaded from .env)
  - Set your preferred theme and language
  - Save your settings
4. **Add Your First Account**:
  - Go to the Accounts tab
  - Click "Add Account"
  - Enter your phone number
  - Follow the authorization process

## 📖 Documentation

- **[Documentation Index](docs/index.md)**: Complete documentation overview
- **[Quick Start Guide](docs/quick-start.md)**: Get up and running in minutes
- **[Usage Guide](docs/usage.md)**: Comprehensive user guide
- **[API Documentation](docs/api.md)**: Complete API reference
- **[Configuration Guide](docs/configuration.md)**: Environment variables and settings
- **[Troubleshooting](docs/troubleshooting.md)**: Common issues and solutions
- **[FAQ](docs/faq.md)**: Frequently asked questions
- **[Contributing](CONTRIBUTING.md)**: How to contribute to the project
- **[Roadmap](ROADMAP.md)**: Future development plans including AI features
- **[Development Goals](DEVELOPMENT_GOALS.md)**: Performance and accessibility targets

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

This project is licensed under the Eclipse Public License 2.0 (EPL-2.0) - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This application is for educational and legitimate business purposes only. Users are responsible for complying with Telegram's Terms of Service and applicable laws. The developers are not responsible for any misuse of this application.

## 🆘 Support

- **Documentation**: [GitHub Wiki](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/wiki)
- **Issues**: [GitHub Issues](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/issues)
- **Discussions**: [GitHub Discussions](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/discussions)
- **Email**: [contact@voxhash.dev](mailto:contact@voxhash.dev)

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

## 💖 Sponsors

We're incredibly grateful to our sponsors who help support the development and maintenance of this project!

### 🌟 Monthly Sponsors

- **[@dodierandal-arch](https://github.com/dodierandal-arch)** - $100/month (Premium Sponsor) 🎉

Thank you for your generous support! Your contributions help us continue improving the project and adding new features.

**Interested in becoming a sponsor?** [Support us on GitHub Sponsors](https://github.com/sponsors/VoxHash) and help make this project even better!

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

- **SendGram (hosted SaaS)**: [sendgram.pro](https://www.sendgram.pro) — managed cloud edition for teams
- **Repository**: [GitHub](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender)
- **Documentation**: [GitHub Wiki](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/wiki)
- **Issues**: [GitHub Issues](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/issues)
- **Discussions**: [GitHub Discussions](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/discussions)
- **Releases**: [GitHub Releases](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/releases)
- **PyPI**: [PyPI Package](https://pypi.org/project/telegram-multi-account-sender/)

## 🌟 Star History

[Star History Chart](https://star-history.com/#VoxHash/Telegram-Multi-Account-Message-Sender&Date)

---

Made with ❤️ by [VoxHash](https://voxhash.dev)