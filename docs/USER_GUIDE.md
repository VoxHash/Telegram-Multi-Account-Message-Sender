# User Guide

This guide will help you get started with the Telegram Multi-Account Message Sender application.

## Table of Contents

- [Getting Started](#getting-started)
- [Account Management](#account-management)
- [Template Management](#template-management)
- [Recipient Management](#recipient-management)
- [Campaign Management](#campaign-management)
- [Message Testing](#message-testing)
- [Logging and Monitoring](#logging-and-monitoring)
- [Settings and Configuration](#settings-and-configuration)
- [Advanced Features](#advanced-features)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Getting Started

### First Launch

1. **Start the Application**: Run `python main.py` or launch the installed executable
2. **Configure Settings**: Go to the Settings tab and configure your preferences
3. **Set Up API Credentials**: Enter your Telegram API ID and API Hash
4. **Add Your First Account**: Use the Accounts tab to add and authorize your Telegram account

### Initial Setup

1. **Get Telegram API Credentials**:
   - Go to [my.telegram.org](https://my.telegram.org)
   - Log in with your phone number
   - Go to "API development tools"
   - Create a new application
   - Copy the API ID and API Hash

2. **Configure Application Settings**:
   - Open the Settings tab
   - Enter your API credentials
   - Set your preferred theme and language
   - Configure logging settings
   - Save your settings

## Account Management

### Adding Accounts

1. **Open Accounts Tab**: Click on the "Accounts" tab
2. **Click "Add Account"**: Click the "Add Account" button
3. **Enter Phone Number**: Enter your phone number with country code (e.g., +1234567890)
4. **Authorize Account**: Follow the authorization process
5. **Enter Verification Code**: Enter the code sent to your phone
6. **Complete Setup**: Your account will be added and ready to use

### Managing Accounts

- **View Account Status**: See which accounts are online/offline
- **Edit Account Details**: Click "Edit" to modify account information
- **Delete Accounts**: Remove accounts you no longer need
- **Re-authorize**: Re-authorize accounts if needed

### Account Status

- **Online**: Account is connected and ready to send messages
- **Offline**: Account is not connected
- **Error**: Account has an error and needs attention

## Template Management

### Creating Templates

1. **Open Templates Tab**: Click on the "Templates" tab
2. **Click "Create Template"**: Click the "Create Template" button
3. **Enter Template Details**:
   - **Name**: Give your template a descriptive name
   - **Content**: Write your message content
   - **Type**: Choose text, media, or combined
   - **Category**: Select a category for organization
4. **Configure Spintax** (optional):
   - Enable spintax if you want message variations
   - Use spintax syntax: `{option1|option2|option3}`
5. **Save Template**: Click "Save" to create your template

### Spintax Syntax

Spintax allows you to create message variations:

```
Hello {John|Jane|Alex}, welcome to {our|my} {amazing|fantastic|great} service!
```

This will generate variations like:
- "Hello John, welcome to our amazing service!"
- "Hello Jane, welcome to my fantastic service!"
- "Hello Alex, welcome to our great service!"

### Template Categories

- **General**: General purpose templates
- **Marketing**: Marketing and promotional messages
- **Support**: Customer support messages
- **Notification**: Notification messages
- **Custom**: Custom categories you define

### Managing Templates

- **Edit Templates**: Click "Edit" to modify existing templates
- **Delete Templates**: Remove templates you no longer need
- **Import/Export**: Use CSV import/export for bulk operations
- **Search Templates**: Use the search field to find specific templates

## Recipient Management

### Adding Recipients

1. **Open Recipients Tab**: Click on the "Recipients" tab
2. **Click "Add Recipient"**: Click the "Add Recipient" button
3. **Enter Recipient Details**:
   - **Name**: Enter recipient name
   - **Type**: Choose User, Group, or Channel
   - **Contact Info**: Enter phone number, username, or user ID
   - **Additional Info**: Add group type, member count, etc.
4. **Save Recipient**: Click "Save" to add the recipient

### Recipient Types

- **User**: Individual Telegram users
- **Group**: Telegram groups
- **Channel**: Telegram channels

### Managing Recipients

- **Edit Recipients**: Click "Edit" to modify recipient information
- **Delete Recipients**: Remove recipients you no longer need
- **Import/Export**: Use CSV import/export for bulk operations
- **Search Recipients**: Use the search field to find specific recipients

### Recipient Lists

- **Create Lists**: Organize recipients into lists
- **Add to Lists**: Add recipients to specific lists
- **Manage Lists**: Edit, delete, and organize recipient lists

## Campaign Management

### Creating Campaigns

1. **Open Campaigns Tab**: Click on the "Campaigns" tab
2. **Click "Create Campaign"**: Click the "Create Campaign" button
3. **Enter Campaign Details**:
   - **Name**: Give your campaign a descriptive name
   - **Description**: Add a description (optional)
   - **Type**: Choose text, media, or combined
   - **Message Content**: Enter your message content
4. **Configure Recipients**:
   - **Source**: Choose manual selection or recipient list
   - **Recipients**: Select specific recipients or lists
5. **Set Scheduling**:
   - **Start Time**: Set when the campaign should start
   - **Timezone**: Choose your timezone
6. **Configure Rate Limiting**:
   - **Messages per Minute**: Set sending rate
   - **Messages per Hour**: Set hourly limit
   - **Messages per Day**: Set daily limit
7. **Save Campaign**: Click "Save" to create your campaign

### Campaign Types

- **Text**: Send text messages only
- **Media**: Send media files (images, videos, documents)
- **Combined**: Send media with text captions

### Campaign Status

- **Draft**: Campaign is being created/edited
- **Scheduled**: Campaign is scheduled to start
- **Running**: Campaign is currently running
- **Paused**: Campaign is paused
- **Completed**: Campaign has finished successfully
- **Failed**: Campaign encountered errors
- **Stopped**: Campaign was stopped by user

### Campaign Actions

- **Start**: Start a draft or scheduled campaign
- **Pause**: Pause a running campaign
- **Resume**: Resume a paused campaign
- **Stop**: Stop a running campaign
- **Retry**: Retry a failed campaign
- **Duplicate**: Create a copy of a completed campaign

### Campaign Monitoring

- **Progress**: Track sending progress
- **Statistics**: View sent, failed, and skipped counts
- **Logs**: Monitor campaign activity
- **Real-time Updates**: See live progress updates

## Message Testing

### Testing Messages

1. **Open Testing Tab**: Click on the "Testing" tab
2. **Select Account**: Choose which account to use for testing
3. **Select Recipient**: Choose a test recipient
4. **Enter Message**: Type your test message
5. **Send Test**: Click "Send Test" to send the message

### Test Features

- **Preview Messages**: See how messages will look
- **Test Spintax**: Test spintax variations
- **Test Media**: Test media uploads
- **Test Different Recipients**: Test with different recipient types

## Logging and Monitoring

### Application Logs

- **View Logs**: Go to the Logs tab
- **Filter Logs**: Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **Search Logs**: Search for specific log entries
- **Clear Logs**: Clear old log entries

### Send Logs

- **View Send Logs**: See all sent messages
- **Filter by Campaign**: Filter logs by campaign
- **Filter by Account**: Filter logs by account
- **Filter by Status**: Filter logs by send status
- **Export Logs**: Export logs to CSV

### Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General information about application flow
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for recoverable errors
- **CRITICAL**: Critical errors that may cause application failure

## Settings and Configuration

### Application Settings

- **Debug Mode**: Enable/disable debug mode
- **Window Settings**: Configure window size and behavior
- **Theme Settings**: Choose application theme
- **Language Settings**: Select application language

### Logging Settings

- **Log Level**: Set the minimum log level
- **Log to File**: Enable/disable file logging
- **Log File Size**: Set maximum log file size
- **Log Backup Count**: Set number of log file backups

### Database Settings

- **Database URL**: Configure database connection
- **Database Maintenance**: Perform database maintenance tasks

### Telegram API Settings

- **API ID**: Your Telegram API ID
- **API Hash**: Your Telegram API Hash

### Rate Limiting Settings

- **Default Rate Limits**: Set default sending rates
- **Max Messages per Hour**: Set hourly message limit
- **Max Messages per Day**: Set daily message limit
- **Global Max Concurrency**: Set maximum concurrent accounts

### Safety Settings

- **Respect Rate Limits**: Enable/disable rate limiting
- **Stop on Error**: Stop campaigns on first error
- **Max Retries**: Set maximum retry attempts
- **Retry Delay**: Set delay between retries

## Advanced Features

### A/B Testing

1. **Enable A/B Testing**: Turn on A/B testing in campaign settings
2. **Create Variants**: Create different message variants
3. **Set Split Percentages**: Configure how variants are distributed
4. **Monitor Results**: Track performance of different variants

### Spintax Processing

1. **Enable Spintax**: Turn on spintax in template settings
2. **Write Spintax**: Use spintax syntax in your messages
3. **Test Variations**: Preview spintax variations
4. **Validate Syntax**: Check spintax syntax for errors

### Media Handling

1. **Supported Formats**: Images, videos, documents, audio
2. **File Size Limits**: Respect Telegram's file size limits
3. **Caption Support**: Add captions to media messages
4. **Batch Upload**: Upload multiple media files

### Scheduling

1. **Start Time**: Set when campaigns should start
2. **Timezone Support**: Choose your timezone
3. **Recurring Campaigns**: Set up recurring campaigns
4. **Time-based Rules**: Create time-based sending rules

## Best Practices

### Account Management

- **Use Legitimate Accounts**: Only use accounts you own
- **Respect Rate Limits**: Don't exceed Telegram's rate limits
- **Monitor Account Health**: Check account status regularly
- **Rotate Accounts**: Use different accounts for different campaigns

### Message Content

- **Write Clear Messages**: Make your messages clear and concise
- **Test Before Sending**: Always test messages before campaigns
- **Use Spintax Wisely**: Don't overuse spintax variations
- **Respect Recipients**: Don't send spam or unwanted messages

### Campaign Management

- **Start Small**: Begin with small test campaigns
- **Monitor Progress**: Watch campaign progress closely
- **Handle Errors**: Address errors promptly
- **Backup Data**: Regular backups of your data

### Security

- **Protect API Credentials**: Keep your API credentials secure
- **Use Strong Passwords**: Use strong passwords for accounts
- **Enable 2FA**: Enable two-factor authentication on Telegram
- **Regular Updates**: Keep the application updated

## Troubleshooting

### Common Issues

1. **Account Authorization Fails**: Check phone number format and internet connection
2. **Messages Not Sending**: Verify account status and recipient information
3. **Campaign Won't Start**: Check campaign configuration and account status
4. **UI Not Responding**: Restart the application
5. **Database Errors**: Check database connection and permissions

### Getting Help

1. **Check Logs**: Look for error messages in the logs
2. **Search Documentation**: Check this guide and the main documentation
3. **Check GitHub Issues**: Look for similar issues on GitHub
4. **Create New Issue**: If the problem persists, create a new issue

### System Requirements

- **Python 3.10+**: Ensure you have the correct Python version
- **PyQt5**: Required for the GUI
- **Internet Connection**: Required for Telegram API
- **Sufficient Disk Space**: At least 1GB free space
- **Adequate RAM**: At least 4GB recommended

## Tips and Tricks

### Efficiency Tips

- **Use Templates**: Create reusable message templates
- **Organize Recipients**: Use recipient lists for better organization
- **Batch Operations**: Use import/export for bulk operations
- **Monitor Logs**: Keep an eye on logs for issues

### Performance Tips

- **Optimize Rate Limits**: Set appropriate rate limits
- **Use Multiple Accounts**: Distribute load across accounts
- **Monitor Resources**: Watch system resource usage
- **Regular Maintenance**: Perform regular database maintenance

### Safety Tips

- **Test First**: Always test before sending campaigns
- **Respect Limits**: Don't exceed rate limits
- **Monitor Accounts**: Watch for account issues
- **Backup Data**: Regular backups are essential

## Support

If you need help:

1. **Check Documentation**: Read this guide and the main documentation
2. **Search Issues**: Look for similar issues on GitHub
3. **Create Issue**: Create a new issue with detailed information
4. **Contact Support**: Reach out to the development team

Remember: This application is for educational and legitimate business purposes only. Always comply with Telegram's Terms of Service and applicable laws.
