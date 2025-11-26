# Installation Guide

Complete installation instructions for Telegram Multi-Account Message Sender.

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Internet connection

## Installation Methods

### Method 1: Using pip (Recommended)

```bash
pip install telegram-multi-account-sender
```

### Method 2: From Source

```bash
git clone https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender.git
cd Telegram-Multi-Account-Message-Sender
pip install -r requirements.txt
```

### Method 3: Development Installation

```bash
git clone https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender.git
cd Telegram-Multi-Account-Message-Sender
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Platform-Specific Instructions

### Windows

1. Download and install Python from [python.org](https://www.python.org/downloads/)
2. Open Command Prompt or PowerShell
3. Run: `pip install telegram-multi-account-sender`
4. Run: `python main.py`

### macOS

1. Install Python using Homebrew: `brew install python3`
2. Run: `pip3 install telegram-multi-account-sender`
3. Run: `python3 main.py`

### Linux

1. Install Python: `sudo apt-get install python3 python3-pip`
2. Run: `pip3 install telegram-multi-account-sender`
3. Run: `python3 main.py`

## Verification

After installation, verify it works:

```bash
python -m app.cli --version
```

Or run the application:

```bash
python main.py
```

## Troubleshooting

See [Troubleshooting Guide](troubleshooting.md) for common installation issues.

## Next Steps

- [Getting Started](getting-started.md)
- [Configuration](configuration.md)
- [Usage Guide](usage.md)

