# Frequently Asked Questions (FAQ)

This document answers common questions about the Telegram Multi-Account Message Sender application.

## Table of Contents

- [General Questions](#general-questions)
- [Installation Questions](#installation-questions)
- [Account Questions](#account-questions)
- [Campaign Questions](#campaign-questions)
- [Message Questions](#message-questions)
- [Technical Questions](#technical-questions)
- [Troubleshooting Questions](#troubleshooting-questions)
- [Security Questions](#security-questions)
- [Legal Questions](#legal-questions)

## General Questions

### What is the Telegram Multi-Account Message Sender?

The Telegram Multi-Account Message Sender is a professional-grade desktop application that allows you to manage multiple Telegram accounts and send messages with advanced features like scheduling, spintax, media support, and compliance controls.

### Who is this application for?

This application is designed for:
- Businesses that need to send messages to multiple recipients
- Marketers who want to manage multiple Telegram accounts
- Developers who need to integrate Telegram messaging
- Anyone who needs to send messages responsibly and efficiently

### Is this application free?

Yes, this application is open-source and free to use under the BSD 3-Clause License.

### What platforms are supported?

The application supports:
- Windows 10/11
- macOS 10.15+
- Linux (Ubuntu 18.04+, CentOS 7+, Arch Linux)

### What are the system requirements?

**Minimum Requirements:**
- Python 3.10+
- 4GB RAM
- 1GB free disk space
- Internet connection

**Recommended Requirements:**
- Python 3.11+
- 8GB RAM
- 5GB free disk space
- Stable internet connection

## Installation Questions

### How do I install the application?

**Option 1: Using pip (Python package)**
```bash
pip install telegram-multi-account-sender
```

**Option 2: From source**
```bash
git clone https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender.git
cd Telegram-Multi-Account-Message-Sender
pip install -r requirements.txt
python main.py
```

**Option 3: Using installers**
Download the appropriate installer from the [Releases](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/releases) page.

### Do I need to install Python separately?

If you're using the Python package or source code, yes. If you're using the installers, Python is included.

### What if I get a "Python not found" error?

1. Install Python 3.10+ from [python.org](https://www.python.org/downloads/)
2. Make sure Python is added to your PATH
3. Restart your terminal/command prompt

### Can I run this on a server without a GUI?

The application requires a GUI (PyQt5), so it needs a desktop environment. However, you can run it on a server with X11 forwarding or a virtual display.

## Account Questions

### How many accounts can I manage?

There's no hard limit, but we recommend:
- 5-10 accounts for personal use
- 10-50 accounts for small businesses
- 50+ accounts for enterprise use (with proper infrastructure)

### Do I need separate phone numbers for each account?

Yes, each Telegram account requires a unique phone number.

### Can I use virtual phone numbers?

Telegram's terms of service require real phone numbers. Using virtual numbers may result in account bans.

### What happens if my account gets banned?

If your account gets banned by Telegram, you'll need to:
1. Contact Telegram support
2. Wait for the ban to be lifted
3. Use a different account

### Can I import accounts from another application?

Currently, you need to add accounts manually. We're working on import functionality for future versions.

## Campaign Questions

### How many campaigns can I run simultaneously?

The number depends on your system resources and rate limits. We recommend:
- 1-5 campaigns for personal use
- 5-20 campaigns for small businesses
- 20+ campaigns for enterprise use

### Can I schedule campaigns for specific times?

Yes, you can schedule campaigns to start at specific times with timezone support.

### What happens if a campaign fails?

The application will:
1. Log the error
2. Retry according to your retry settings
3. Continue with other recipients
4. Show the error in the logs

### Can I pause and resume campaigns?

Yes, you can pause running campaigns and resume them later.

### How do I stop a campaign?

Click the "Stop" button in the Campaigns tab. The campaign will stop sending new messages but will complete current messages.

### Can I duplicate a completed campaign?

Yes, you can duplicate completed campaigns to create new draft campaigns with the same settings.

## Message Questions

### What types of messages can I send?

You can send:
- Text messages
- Images
- Videos
- Documents
- Audio files
- Combined messages (media with captions)

### What is spintax?

Spintax is a syntax that allows you to create message variations. For example:
```
Hello {John|Jane|Alex}, welcome to {our|my} {amazing|fantastic|great} service!
```

This will generate variations like:
- "Hello John, welcome to our amazing service!"
- "Hello Jane, welcome to my fantastic service!"
- "Hello Alex, welcome to our great service!"

### How do I use spintax?

1. Enable spintax in your template or campaign
2. Write your message using spintax syntax: `{option1|option2|option3}`
3. Test your spintax using the preview feature
4. Save and use in your campaigns

### What file formats are supported for media?

Supported formats include:
- **Images**: JPG, PNG, GIF, WebP
- **Videos**: MP4, AVI, MOV, WebM
- **Documents**: PDF, DOC, DOCX, TXT
- **Audio**: MP3, WAV, OGG

### What are the file size limits?

File size limits depend on Telegram's limits:
- **Images**: Up to 10MB
- **Videos**: Up to 2GB
- **Documents**: Up to 2GB
- **Audio**: Up to 50MB

### Can I send messages to groups and channels?

Yes, you can send messages to:
- Individual users
- Groups
- Channels

## Technical Questions

### What database does the application use?

The application uses SQLite by default, but you can configure it to use other databases like PostgreSQL or MySQL.

### Can I backup my data?

Yes, you can backup your data by:
1. Copying the database file
2. Exporting data to CSV
3. Using the built-in backup features

### How do I update the application?

**If installed via pip:**
```bash
pip install --upgrade telegram-multi-account-sender
```

**If installed from source:**
```bash
git pull origin main
pip install -r requirements.txt
```

**If installed via installer:**
Download and run the new installer.

### Can I run this on a VPS or cloud server?

Yes, but you need a desktop environment or X11 forwarding. Consider using:
- VNC server
- X11 forwarding over SSH
- Virtual display (Xvfb)

### What programming language is this written in?

The application is written in Python 3.10+ using:
- PyQt5 for the GUI
- SQLModel for database operations
- Telethon for Telegram API
- Rich for logging

## Troubleshooting Questions

### The application won't start. What should I do?

1. Check Python version: `python --version`
2. Install dependencies: `pip install -r requirements.txt`
3. Check for error messages in the terminal
4. Try running as administrator (Windows)

### My accounts keep going offline. Why?

This could be due to:
1. Network connectivity issues
2. Invalid API credentials
3. Account restrictions
4. Rate limiting

### Messages are not sending. What's wrong?

Check:
1. Account status (should be online)
2. Recipient information (phone number, username, etc.)
3. Rate limiting settings
4. Network connection
5. Error logs

### The UI is not responding. What should I do?

1. Restart the application
2. Check system resources (RAM, CPU)
3. Close other applications
4. Check for error messages

### I'm getting database errors. How do I fix this?

1. Check database file permissions
2. Ensure sufficient disk space
3. Try recreating the database
4. Check for database corruption

### The application is using too much memory. What can I do?

1. Close unused tabs
2. Clear logs regularly
3. Restart the application
4. Check for memory leaks

## Security Questions

### Is my data secure?

Yes, the application:
- Stores data locally on your computer
- Uses secure database connections
- Encrypts sensitive information
- Follows security best practices

### Are my API credentials safe?

Yes, API credentials are:
- Stored securely in the database
- Not transmitted over the network
- Protected by file permissions
- Encrypted when possible

### Can others access my accounts?

No, only you can access your accounts through the application on your computer.

### Should I share my API credentials?

No, never share your API credentials with anyone. Keep them secure and private.

### What if I suspect a security breach?

1. Change your API credentials immediately
2. Revoke access to suspicious applications
3. Check your account activity
4. Contact Telegram support if needed

## Legal Questions

### Is this application legal?

Yes, the application is legal when used responsibly and in compliance with:
- Telegram's Terms of Service
- Applicable local laws
- Privacy regulations

### Can I use this for spam?

No, this application is not designed for spam. It's for legitimate business purposes only.

### What are the terms of use?

The application is provided under the BSD 3-Clause License. Users must comply with:
- Telegram's Terms of Service
- Applicable laws and regulations
- Responsible messaging practices

### Can I use this commercially?

Yes, you can use this application commercially, but you must comply with all applicable terms and laws.

### What happens if I misuse the application?

Misuse may result in:
- Account bans by Telegram
- Legal consequences
- Loss of access to the application

### Do I need permission to send messages?

Yes, you need:
- Recipient consent for marketing messages
- Compliance with local laws
- Respect for recipient preferences

## Support Questions

### How can I get help?

You can get help by:
1. Checking the documentation
2. Searching GitHub issues
3. Creating a new issue
4. Contacting support

### Where can I report bugs?

Report bugs on the [GitHub Issues](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/issues) page.

### How can I request features?

Request features on the [GitHub Issues](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/issues) page.

### Is there a community forum?

Yes, you can join discussions on [GitHub Discussions](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/discussions).

### Can I contribute to the project?

Yes, contributions are welcome! See our [Contributing Guide](CONTRIBUTING.md) for details.

## Performance Questions

### How can I improve performance?

1. Use SSD storage
2. Increase RAM
3. Optimize rate limiting
4. Close unused applications
5. Regular database maintenance

### What's the maximum sending rate?

The maximum rate depends on:
- Telegram's rate limits
- Your account status
- Network conditions
- System performance

### Can I run this 24/7?

Yes, but consider:
- System resources
- Rate limiting
- Account health
- Monitoring needs

### How much disk space does it need?

The application needs:
- ~100MB for the application
- Additional space for logs and database
- Space for media files

## Integration Questions

### Can I integrate this with other applications?

Yes, the application provides:
- Database access
- API endpoints
- Export/import functionality
- Webhook support

### Is there an API?

Yes, the application provides a REST API for integration.

### Can I automate this application?

Yes, you can automate it using:
- Scripts
- Cron jobs
- Task schedulers
- API calls

### Can I use this with webhooks?

Yes, webhook support is available for real-time notifications.

## Conclusion

If you have questions not covered in this FAQ, please:

1. Check the documentation
2. Search existing issues
3. Create a new issue
4. Contact support

Remember: This application is for educational and legitimate business purposes only. Always comply with Telegram's Terms of Service and applicable laws.
