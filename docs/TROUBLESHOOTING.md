# Troubleshooting Guide

This guide helps you resolve common issues with the Telegram Multi-Account Message Sender application.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Configuration Issues](#configuration-issues)
- [Account Issues](#account-issues)
- [Campaign Issues](#campaign-issues)
- [Message Sending Issues](#message-sending-issues)
- [UI Issues](#ui-issues)
- [Performance Issues](#performance-issues)
- [Database Issues](#database-issues)
- [Logging Issues](#logging-issues)
- [Common Error Messages](#common-error-messages)

## Installation Issues

### Python Version Compatibility

**Problem**: Application fails to start with Python version error.

**Solution**: Ensure you have Python 3.10 or higher installed.

```bash
python --version
```

If you have an older version, install Python 3.10+ from [python.org](https://www.python.org/downloads/).

### Missing Dependencies

**Problem**: ImportError when starting the application.

**Solution**: Install all required dependencies.

```bash
pip install -r requirements.txt
```

If you encounter permission issues on Linux/macOS:

```bash
pip install --user -r requirements.txt
```

### PyQt5 Installation Issues

**Problem**: PyQt5 installation fails.

**Solution**: Try different installation methods:

```bash
# Method 1: Using pip
pip install PyQt5

# Method 2: Using conda
conda install pyqt

# Method 3: Using system package manager (Linux)
sudo apt-get install python3-pyqt5  # Ubuntu/Debian
sudo yum install python3-qt5        # CentOS/RHEL
```

### Windows-specific Issues

**Problem**: Application won't start on Windows.

**Solution**: 
1. Ensure you have Visual C++ Redistributable installed
2. Try running as administrator
3. Check Windows Defender/antivirus settings

## Configuration Issues

### Environment Variables Not Loading

**Problem**: Settings not being loaded from .env file.

**Solution**: 
1. Ensure .env file is in the project root directory
2. Check file format (no spaces around =)
3. Restart the application after changes

```env
TELEGRAM_API_ID=123456
TELEGRAM_API_HASH=your_hash_here
```

### Database Connection Issues

**Problem**: Database connection errors.

**Solution**: 
1. Check database URL in .env file
2. Ensure database directory exists and is writable
3. Try using absolute path for database file

```env
DATABASE_URL=sqlite:///C:/path/to/telegram_sender.db
```

### Invalid API Credentials

**Problem**: Telegram API credentials not working.

**Solution**: 
1. Verify API ID and API Hash from [my.telegram.org](https://my.telegram.org)
2. Ensure credentials are correct and not expired
3. Check if your IP is blocked by Telegram

## Account Issues

### Account Authorization Fails

**Problem**: Cannot authorize Telegram account.

**Solution**: 
1. Check phone number format (include country code)
2. Ensure you have internet connection
3. Try using a different phone number
4. Check if your phone number is banned by Telegram

### Account Goes Offline

**Problem**: Account status shows as offline.

**Solution**: 
1. Check internet connection
2. Verify API credentials
3. Try re-authorizing the account
4. Check if account is banned or restricted

### Session String Issues

**Problem**: Session string not working.

**Solution**: 
1. Delete the session file and re-authorize
2. Check if session string is corrupted
3. Ensure proper file permissions

## Campaign Issues

### Campaign Won't Start

**Problem**: Campaign status remains as "Draft" or "Scheduled".

**Solution**: 
1. Check if campaign has recipients
2. Verify start time is in the future
3. Ensure at least one account is online
4. Check campaign configuration

### Campaign Stops Unexpectedly

**Problem**: Campaign stops without user intervention.

**Solution**: 
1. Check logs for error messages
2. Verify account status
3. Check rate limiting settings
4. Ensure sufficient disk space

### Campaign Progress Not Updating

**Problem**: Progress counters not updating.

**Solution**: 
1. Refresh the campaigns tab
2. Check database connection
3. Restart the application
4. Check for database locks

## Message Sending Issues

### Messages Not Sending

**Problem**: Messages remain in "Pending" status.

**Solution**: 
1. Check account authorization
2. Verify recipient information
3. Check rate limiting settings
4. Ensure message content is valid

### Media Upload Fails

**Problem**: Media files not uploading.

**Solution**: 
1. Check file path and permissions
2. Verify file format is supported
3. Check file size limits
4. Ensure stable internet connection

### Spintax Not Working

**Problem**: Spintax variations not generating.

**Solution**: 
1. Check spintax syntax
2. Verify spintax is enabled in template
3. Test with simple spintax first
4. Check for syntax errors

## UI Issues

### Application Won't Start

**Problem**: Application crashes on startup.

**Solution**: 
1. Check Python version compatibility
2. Verify all dependencies are installed
3. Check for conflicting applications
4. Try running from command line for error details

### UI Elements Not Responding

**Problem**: Buttons and menus not working.

**Solution**: 
1. Restart the application
2. Check for UI thread issues
3. Verify PyQt5 installation
4. Check system resources

### Theme Not Applying

**Problem**: Theme changes not visible.

**Solution**: 
1. Restart the application
2. Check theme file exists
3. Verify theme settings
4. Clear application cache

### Language Not Changing

**Problem**: Language changes not applied.

**Solution**: 
1. Restart the application
2. Check translation files exist
3. Verify language settings
4. Clear application cache

## Performance Issues

### Slow Application Startup

**Problem**: Application takes long to start.

**Solution**: 
1. Check database size
2. Verify system resources
3. Disable unnecessary startup processes
4. Check for corrupted files

### High Memory Usage

**Problem**: Application uses too much memory.

**Solution**: 
1. Close unused tabs
2. Clear logs regularly
3. Restart the application
4. Check for memory leaks

### Slow Campaign Execution

**Problem**: Campaigns run slowly.

**Solution**: 
1. Adjust rate limiting settings
2. Increase concurrent accounts
3. Check system performance
4. Optimize message content

## Database Issues

### Database Locked

**Problem**: Database is locked error.

**Solution**: 
1. Close all application instances
2. Check for running processes
3. Restart the system
4. Check file permissions

### Database Corruption

**Problem**: Database corruption errors.

**Solution**: 
1. Create database backup
2. Try database repair
3. Restore from backup
4. Recreate database

### Migration Errors

**Problem**: Database migration fails.

**Solution**: 
1. Check database version
2. Verify migration scripts
3. Backup data before migration
4. Contact support if needed

## Logging Issues

### Logs Not Appearing

**Problem**: Log messages not showing.

**Solution**: 
1. Check log level settings
2. Verify log file permissions
3. Check log file location
4. Restart logging service

### Log Files Too Large

**Problem**: Log files consuming too much disk space.

**Solution**: 
1. Enable log rotation
2. Reduce log level
3. Clear old logs
4. Adjust log file settings

### Debug Information Missing

**Problem**: Not enough debug information.

**Solution**: 
1. Set log level to DEBUG
2. Enable debug mode
3. Check log configuration
4. Verify logging setup

## Common Error Messages

### "Database engine not initialized"

**Solution**: 
1. Check database URL configuration
2. Ensure database file exists
3. Verify file permissions
4. Restart the application

### "Account not found"

**Solution**: 
1. Check account ID
2. Verify account exists in database
3. Refresh account list
4. Re-add account if needed

### "Campaign not found"

**Solution**: 
1. Check campaign ID
2. Verify campaign exists in database
3. Refresh campaign list
4. Re-create campaign if needed

### "Recipient not found"

**Solution**: 
1. Check recipient ID
2. Verify recipient exists in database
3. Refresh recipient list
4. Re-add recipient if needed

### "Invalid API credentials"

**Solution**: 
1. Verify API ID and API Hash
2. Check credentials format
3. Ensure credentials are not expired
4. Re-enter credentials

### "Rate limit exceeded"

**Solution**: 
1. Wait for rate limit to reset
2. Adjust rate limiting settings
3. Reduce message frequency
4. Check account status

### "Network error"

**Solution**: 
1. Check internet connection
2. Verify network settings
3. Check firewall settings
4. Try different network

### "File not found"

**Solution**: 
1. Check file path
2. Verify file exists
3. Check file permissions
4. Use absolute path

### "Permission denied"

**Solution**: 
1. Check file permissions
2. Run as administrator (Windows)
3. Use sudo (Linux/macOS)
4. Check file ownership

### "Out of memory"

**Solution**: 
1. Close unused applications
2. Restart the application
3. Check system memory
4. Optimize application settings

## Getting Help

If you're still experiencing issues:

1. **Check the logs**: Look for error messages in the application logs
2. **Search the documentation**: Check this guide and the main documentation
3. **Check GitHub issues**: Look for similar issues on the GitHub repository
4. **Create a new issue**: If the problem persists, create a new issue with:
   - Detailed description of the problem
   - Steps to reproduce
   - Error messages and logs
   - System information
   - Application version

## System Requirements

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

## Performance Optimization

### Database Optimization
- Regular database maintenance
- Index optimization
- Query optimization
- Regular backups

### Memory Optimization
- Close unused tabs
- Clear logs regularly
- Optimize message content
- Monitor memory usage

### Network Optimization
- Use stable internet connection
- Optimize rate limiting
- Monitor network usage
- Check for network issues

## Security Considerations

### Account Security
- Use strong passwords
- Enable 2FA on Telegram
- Regular account monitoring
- Secure session storage

### Data Security
- Regular backups
- Secure file permissions
- Encrypted storage
- Access control

### Network Security
- Use secure connections
- Monitor network traffic
- Check for vulnerabilities
- Regular updates
