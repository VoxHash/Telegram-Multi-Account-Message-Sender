# Example Files

This directory contains example files to help you get started with the Telegram Multi-Account Message Sender application.

## 📁 File Overview

### Configuration Files

#### `env_template.txt`
- **Purpose**: Environment configuration template
- **Usage**: Copy to root directory as `.env` and fill in your values
- **Contains**: All available environment variables with descriptions
- **Required**: Yes, for basic functionality

### CSV Import Files

#### `recipients_example.csv`
- **Purpose**: Example recipients data for import
- **Usage**: Use "Import CSV" in Recipients tab
- **Contains**: Sample users, groups, and channels
- **Fields**: All recipient fields including type-specific data

#### `templates_example.csv`
- **Purpose**: Example message templates for import
- **Usage**: Use "Import CSV" in Templates tab
- **Contains**: Various message templates with spintax and variables
- **Features**: Welcome messages, product launches, follow-ups, events, thank you

#### `campaigns_example.csv`
- **Purpose**: Example campaigns data for import
- **Usage**: Use "Import CSV" in Campaigns tab
- **Contains**: Sample campaigns with different statuses and configurations
- **Features**: Mass messages, scheduled campaigns, A/B testing

#### `accounts_example.csv`
- **Purpose**: Example accounts data for import
- **Usage**: Use "Import CSV" in Accounts tab
- **Contains**: Sample Telegram accounts with different configurations
- **Features**: Different account types, proxy settings, rate limits

## 🚀 Quick Start Guide

### 1. Environment Setup
```bash
# Copy the environment template
cp examples/env_template.txt .env

# Edit the .env file with your values
# At minimum, set:
# - TELEGRAM_API_ID
# - TELEGRAM_API_HASH
```

### 2. Import Sample Data
1. Start the application
2. Go to each tab (Accounts, Recipients, Templates, Campaigns)
3. Click "Import CSV" button
4. Select the corresponding example file from this directory

### 3. Test the Application
1. Go to the "Testing" tab
2. Select an account and recipient
3. Choose a template or enter custom message
4. Send a test message

## 📋 Data Structure

### Recipients
- **USER**: Individual users with username, phone, email
- **GROUP**: Telegram groups with group_id, title, username
- **CHANNEL**: Telegram channels with channel_id, title, username

### Templates
- **Variables**: Use `{variable_name}` for personalization
- **Spintax**: Use `{option1|option2|option3}` for variations
- **A/B Testing**: Multiple variants with split percentages

### Campaigns
- **Types**: MASS_MESSAGE, SCHEDULED, FOLLOW_UP
- **Status**: DRAFT, RUNNING, PAUSED, COMPLETED, ERROR
- **Rate Limiting**: Per-minute, per-hour, per-day limits
- **Account Selection**: ROUND_ROBIN, WEIGHTED, RANDOM

### Accounts
- **Status**: ONLINE, OFFLINE, CONNECTING, ERROR
- **Proxy Support**: HTTP, SOCKS4, SOCKS5
- **Rate Limits**: Custom limits per account
- **Warmup**: Gradual message increase for new accounts

## 🔧 Customization

### Adding Your Own Data
1. Create new CSV files based on the examples
2. Follow the same column structure
3. Use appropriate data types and formats
4. Import using the application's CSV import feature

### Environment Variables
- Modify `.env` file for your specific needs
- All variables have default values
- See `env_template.txt` for complete list

## ⚠️ Important Notes

### Security
- Never commit your actual `.env` file to version control
- Use strong, unique API credentials
- Keep session files secure

### Data Validation
- CSV files must match exact column names
- Required fields cannot be empty
- Data types must be correct (dates, numbers, etc.)

### Rate Limits
- Start with conservative rate limits
- Monitor account health
- Adjust based on Telegram's response

## 🆘 Troubleshooting

### Common Issues
1. **Import Errors**: Check CSV format and column names
2. **API Errors**: Verify API credentials in `.env`
3. **Rate Limits**: Reduce message frequency
4. **Account Issues**: Check phone number format and session files

### Getting Help
- Check the main README.md for detailed documentation
- Review application logs for error details
- Ensure all dependencies are installed

## 📝 License

These example files are provided under the same license as the main application (BSD-3-Clause).
