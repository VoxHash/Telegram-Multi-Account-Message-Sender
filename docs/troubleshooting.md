# Troubleshooting Guide

Common issues and solutions for Telegram Multi-Account Message Sender.

## Installation Issues

### Python Not Found

**Problem:** `python: command not found` or `Python was not found`

**Solutions:**
1. Install Python 3.10+ from [python.org](https://www.python.org/downloads/)
2. Add Python to PATH during installation
3. Verify installation: `python --version`
4. On Windows, try `py` instead of `python`

### Dependencies Installation Fails

**Problem:** `pip install` fails with errors

**Solutions:**
1. Update pip: `python -m pip install --upgrade pip`
2. Use virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Install dependencies individually to identify the problematic package
4. Check Python version compatibility

### PyQt5 Installation Issues

**Problem:** PyQt5 fails to install

**Solutions:**
1. Install system dependencies:
   - **Ubuntu/Debian:** `sudo apt-get install python3-pyqt5`
   - **macOS:** `brew install pyqt5`
   - **Windows:** Usually works with pip
2. Try: `pip install --upgrade PyQt5`
3. Use pre-built wheels: `pip install PyQt5 --only-binary :all:`

## Application Startup Issues

### Application Won't Start

**Problem:** Application crashes on startup or doesn't launch

**Solutions:**
1. Check Python version: `python --version` (must be 3.10+)
2. Verify all dependencies: `pip list | grep -i pyqt5`
3. Check logs in `app_data/logs/` directory
4. Run from command line to see error messages:
   ```bash
   python main.py
   ```
5. Try running with debug mode:
   ```bash
   python -u main.py
   ```

### GUI Not Displaying

**Problem:** Application runs but no window appears

**Solutions:**
1. Check if window is minimized or off-screen
2. Verify display settings and resolution
3. Try running with environment variable:
   ```bash
   QT_QPA_PLATFORM=offscreen python main.py
   ```
4. Check for multiple displays and window positioning
5. Restart the application

### Import Errors

**Problem:** `ModuleNotFoundError` or `ImportError`

**Solutions:**
1. Verify installation: `pip install -r requirements.txt`
2. Check Python path: `python -c "import sys; print(sys.path)"`
3. Reinstall the package: `pip uninstall telegram-multi-account-sender && pip install telegram-multi-account-sender`
4. Check for virtual environment activation

## Account Connection Issues

### Cannot Connect to Telegram

**Problem:** Account connection fails

**Solutions:**
1. Verify API credentials (API ID and API Hash)
2. Check internet connection
3. Verify phone number format (include country code, e.g., +1234567890)
4. Try disconnecting and reconnecting the account
5. Check if Telegram service is accessible in your region
6. Verify firewall/antivirus isn't blocking the connection

### Authorization Code Not Received

**Problem:** SMS or phone call code not received

**Solutions:**
1. Check phone number is correct
2. Wait a few minutes and try again
3. Request phone call instead of SMS
4. Check if phone has signal
5. Verify phone number format includes country code
6. Try from a different network if possible

### Account Gets Disconnected

**Problem:** Account disconnects frequently

**Solutions:**
1. Check internet connection stability
2. Verify API credentials are still valid
3. Check for account restrictions on Telegram
4. Reduce number of simultaneous connections
5. Check system resources (RAM, CPU)
6. Review logs for specific error messages

## Message Sending Issues

### Messages Not Sending

**Problem:** Messages fail to send

**Solutions:**
1. Check internet connection
2. Verify recipient username or phone number is correct
3. Check if account is connected: Go to Accounts tab
4. Review rate limiting settings
5. Check logs for specific error messages
6. Verify account is not restricted or banned
7. Try sending a test message manually

### Rate Limit Errors

**Problem:** "Rate limit exceeded" or "Too many requests"

**Solutions:**
1. Reduce rate limit in campaign settings
2. Increase delay between messages
3. Use account warmup for new accounts
4. Spread messages across multiple accounts
5. Wait before retrying
6. Check Telegram's current rate limits

### Invalid Recipient Errors

**Problem:** "User not found" or "Invalid recipient"

**Solutions:**
1. Verify recipient username is correct (without @)
2. Check if recipient has privacy settings blocking messages
3. Verify phone number format if using phone number
4. Ensure recipient exists and is accessible
5. Try sending a test message first

### Media Not Sending

**Problem:** Media files fail to attach or send

**Solutions:**
1. Verify media file exists and is accessible
2. Check file size (Telegram has size limits)
3. Verify file format is supported (images, videos, documents)
4. Check file permissions
5. Try a different media file
6. Use media URL instead of file path if supported

## Campaign Issues

### Campaign Won't Start

**Problem:** Campaign remains in "Pending" status

**Solutions:**
1. Check if at least one account is connected
2. Verify recipients are selected
3. Check campaign settings are valid
4. Review logs for error messages
5. Try creating a new campaign
6. Verify start time is not in the past

### Campaign Stops Unexpectedly

**Problem:** Campaign stops before completion

**Solutions:**
1. Check logs for error messages
2. Verify account is still connected
3. Check for rate limit issues
4. Verify internet connection is stable
5. Check system resources
6. Review campaign settings

### Campaign Performance Issues

**Problem:** Campaign runs very slowly

**Solutions:**
1. Reduce rate limit
2. Close other applications
3. Check system resources (CPU, RAM)
4. Reduce number of simultaneous campaigns
5. Check internet connection speed
6. Optimize recipient lists

## Database Issues

### Database Errors

**Problem:** Database-related errors

**Solutions:**
1. Check database file permissions
2. Verify disk space is available
3. Try backing up and restoring database
4. Check for database corruption
5. Reinitialize database (backup first):
   ```python
   from app.services import initialize_database
   initialize_database()
   ```

### Data Loss

**Problem:** Data disappears or is lost

**Solutions:**
1. Check if database file exists: `app_data/app.db`
2. Restore from backup if available
3. Check for soft-deleted records (they may be recoverable)
4. Verify you're looking at the correct database file
5. Check application logs for clues

## Performance Issues

### Application is Slow

**Problem:** Application runs slowly or freezes

**Solutions:**
1. Close other applications
2. Reduce number of active campaigns
3. Lower rate limits
4. Check system resources (Task Manager / Activity Monitor)
5. Restart the application
6. Check for memory leaks in logs
7. Update to latest version

### High Memory Usage

**Problem:** Application uses too much memory

**Solutions:**
1. Reduce number of active campaigns
2. Clear old logs
3. Restart the application periodically
4. Check for memory leaks
5. Reduce number of connected accounts
6. Close unused tabs/widgets

### High CPU Usage

**Problem:** Application uses too much CPU

**Solutions:**
1. Reduce rate limits
2. Reduce number of simultaneous operations
3. Check for infinite loops in logs
4. Update to latest version
5. Restart the application

## UI/Display Issues

### Interface Not Displaying Correctly

**Problem:** UI elements are misaligned or missing

**Solutions:**
1. Try different theme
2. Check display scaling settings
3. Restart the application
4. Update PyQt5: `pip install --upgrade PyQt5`
5. Check for custom stylesheet issues
6. Try resetting settings

### Language Not Changing

**Problem:** Language setting doesn't apply

**Solutions:**
1. Restart the application after changing language
2. Verify translation files exist: `app/translations/`
3. Check language code is correct (e.g., "en", "es", "fr")
4. Clear application cache
5. Reinstall the application

### Theme Not Applying

**Problem:** Theme doesn't change or looks wrong

**Solutions:**
1. Restart the application
2. Try a different theme
3. Check theme files exist
4. Clear application cache
5. Reset to default theme

## Logging Issues

### Logs Not Generated

**Problem:** No log files are created

**Solutions:**
1. Check `app_data/logs/` directory exists
2. Verify write permissions
3. Check disk space
4. Review logging configuration in settings
5. Check application logs for errors

### Logs Too Large

**Problem:** Log files are very large

**Solutions:1. Configure log rotation in settings
2. Delete old log files manually
3. Reduce log level (INFO instead of DEBUG)
4. Use "Delete All Logs" feature
5. Set up automatic log cleanup

## Network Issues

### Connection Timeouts

**Problem:** Frequent connection timeouts

**Solutions:**
1. Check internet connection stability
2. Verify firewall settings
3. Check proxy configuration if using proxy
4. Try different network
5. Increase timeout settings if available
6. Check Telegram service status

### Proxy Issues

**Problem:** Proxy not working

**Solutions:**
1. Verify proxy settings (host, port, type)
2. Check proxy credentials if required
3. Test proxy connection separately
4. Try different proxy
5. Check if proxy supports Telegram protocol
6. Verify proxy is not blocked

## Getting Help

### Still Having Issues?

If you're still experiencing problems:

1. **Check Documentation:**
   - [FAQ](faq.md) for common questions
   - [Usage Guide](usage.md) for usage instructions
   - [API Documentation](api.md) for API reference

2. **Review Logs:**
   - Check `app_data/logs/` for error messages
   - Look for specific error codes or messages
   - Note when the issue occurs

3. **Gather Information:**
   - Application version
   - Operating system and version
   - Python version
   - Error messages from logs
   - Steps to reproduce the issue

4. **Report the Issue:**
   - Use [Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.md)
   - Include all gathered information
   - Provide steps to reproduce
   - Attach relevant log files (remove sensitive data)

5. **Contact Support:**
   - [GitHub Issues](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/issues)
   - [GitHub Discussions](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/discussions)
   - Email: contact@voxhash.dev

## Prevention Tips

### Best Practices

1. **Regular Backups:** Backup your database regularly
2. **Monitor Logs:** Check logs periodically for warnings
3. **Update Regularly:** Keep the application updated
4. **Test First:** Always test messages before large campaigns
5. **Rate Limits:** Use conservative rate limits
6. **Account Warmup:** Warm up new accounts gradually
7. **System Maintenance:** Keep your system updated and optimized

### Common Mistakes to Avoid

1. **Too High Rate Limits:** Can lead to account bans
2. **Not Testing:** Always test before sending to many recipients
3. **Ignoring Errors:** Address errors promptly
4. **No Backups:** Always backup important data
5. **Using Banned Accounts:** Check account status regularly
6. **Invalid Recipients:** Verify recipients before campaigns

## See Also

- [FAQ](faq.md) for frequently asked questions
- [Usage Guide](usage.md) for usage instructions
- [Configuration Guide](configuration.md) for configuration options
- [Support](../SUPPORT.md) for additional help resources

