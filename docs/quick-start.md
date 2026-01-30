# Quick Start Guide

Get up and running with Telegram Multi-Account Message Sender in minutes!

## Prerequisites

- Python 3.10 or higher
- Internet connection
- Telegram API credentials (API ID and API Hash)

## Installation

### Option 1: Using pip (Recommended)
```bash
pip install telegram-multi-account-sender
```

### Option 2: From source
```bash
git clone https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender.git
cd Telegram-Multi-Account-Message-Sender
pip install -r requirements.txt
```

### Option 3: Using Docker
```bash
docker build -t telegram-sender .
docker run -it --rm \
  -v $(pwd)/app_data:/app/app_data \
  -v $(pwd)/.env:/app/.env \
  telegram-sender
```

## Quick Setup

1. **Get Telegram API credentials**:
   - Visit [my.telegram.org](https://my.telegram.org)
   - Log in with your phone number
   - Go to "API development tools"
   - Create a new application
   - Copy your API ID and API Hash

2. **Configure environment variables**:
   ```bash
   # Copy the example environment file
   cp example_files/env_template.txt .env
   
   # Edit .env and add your credentials
   # ⚠️ SENSITIVE: TELEGRAM_API_ID and TELEGRAM_API_HASH must be kept secret
   ```

3. **Launch the application**:
   ```bash
   python main.py
   ```
   Or if installed via pip:
   ```bash
   python -m app.cli
   ```

4. **Configure settings**:
   - Open the Settings tab
   - Enter your API credentials (or they'll be loaded from .env)
   - Set your preferred theme and language
   - Save settings

5. **Add your first account**:
   - Go to the Accounts tab
   - Click "Add Account"
   - Enter your phone number
   - Complete the authorization process

## Basic Usage

1. **Start the application**: Run `python main.py` or use the installed executable

2. **Add accounts**: Use the Accounts tab to add and authorize your Telegram accounts

3. **Create templates**: Use the Templates tab to create message templates with spintax support

4. **Manage recipients**: Use the Recipients tab to organize your recipient lists

5. **Create campaigns**: Use the Campaigns tab to create and manage message campaigns

6. **Test messages**: Use the Testing tab to test your messages before sending

7. **Monitor logs**: Use the Logs tab to monitor application and send logs

## Example: Send a Test Message

1. Go to the Testing tab
2. Select an account
3. Select a recipient
4. Choose or enter a message
5. Click "Send Test Message"

## Spintax Example

Create message variations using spintax syntax:

```
Hello {John|Jane|Alex}, welcome to {our|my} {amazing|fantastic|great} service!
```

This will generate variations like:
- "Hello John, welcome to our amazing service!"
- "Hello Jane, welcome to my fantastic service!"
- "Hello Alex, welcome to our great service!"

## Next Steps

- Read the [Usage Guide](usage.md) for comprehensive usage instructions
- Check out [Examples](examples/example-01.md) for practical examples
- Review the [Configuration Guide](configuration.md) for advanced settings
- See [Troubleshooting](troubleshooting.md) if you encounter issues
- Visit [FAQ](faq.md) for common questions

