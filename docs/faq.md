# Frequently Asked Questions (FAQ)

Common questions and answers about Telegram Multi-Account Message Sender.

## General Questions

### What is Telegram Multi-Account Message Sender?

Telegram Multi-Account Message Sender is a professional-grade desktop application for managing and sending messages across multiple Telegram accounts. It provides features like scheduling, spintax support, media handling, and compliance controls.

### What platforms are supported?

The application supports:
- Windows 10/11
- macOS 10.15+
- Linux (Ubuntu 18.04+)

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

### Is the application free?

Yes, the application is open-source and free to use under the BSD 3-Clause License.

## Installation

### How do I install the application?

You can install the application in three ways:

1. **Using pip (Recommended):**
   ```bash
   pip install telegram-multi-account-sender
   ```

2. **From source:**
   ```bash
   git clone https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender.git
   cd Telegram-Multi-Account-Message-Sender
   pip install -r requirements.txt
   python main.py
   ```

3. **Using installers:**
   Download the appropriate installer from the [Releases](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/releases) page.

### Do I need to install Python?

If you use the Windows installer (.exe), you don't need to install Python separately. If you install from source or via pip, you need Python 3.10 or higher.

### How do I get Telegram API credentials?

1. Go to [my.telegram.org](https://my.telegram.org)
2. Log in with your phone number
3. Go to "API development tools"
4. Create a new application
5. Copy the API ID and API Hash

## Usage

### How do I add a Telegram account?

1. Go to the Accounts tab
2. Click "Add Account"
3. Enter your phone number
4. Follow the authorization process
5. Enter the verification code when prompted

### How do I create a message campaign?

1. Go to the Campaigns tab
2. Click "Create Campaign"
3. Enter campaign name and message content
4. Select recipients
5. Configure scheduling and rate limits
6. Click "Start Campaign"

### What is spintax?

Spintax is a syntax for creating message variations. For example:

```
Hello {John|Jane|Alex}, welcome to {our|my} {amazing|fantastic} service!
```

This generates variations like:
- "Hello John, welcome to our amazing service!"
- "Hello Jane, welcome to my fantastic service!"
- "Hello Alex, welcome to our amazing service!"

### How do optional AI copy tools work?

They are opt-in. Set your own `AI_API_KEY` in Settings (or `.env`) and choose a provider preset (`openai`, `azure`, or `anthropic`). Templates then offer rewrite, spintax conversion, and variations over HTTPS. Azure uses the deployments path + `api-version`; Anthropic uses the Messages API headers. No AI SDK is installed; leave the key empty to disable the feature.

### How does the plugin registry work?

Open **Plugins → Browse Registry** to discover curated plugins from the official catalog (`registry/catalog.json`, Ed25519-signed). Install downloads a SHA-256–verified `.py` file into `app_data/plugins/`; you still enable it manually after review. Offline, the app uses the bundled catalog. Override the catalog URL with `PLUGIN_REGISTRY_URL`; set `PLUGIN_REGISTRY_REQUIRE_SIGNATURE=true` to reject unsigned catalogs.

### How do I submit or validate a registry plugin?

1. Start from `registry/templates/sample_filter_plugin.py` or `sample_analytics_plugin.py` (absolute imports only).
2. Add the `.py` under `registry/plugins/`.
3. Generate an entry with `telegram-sender plugin-catalog-entry path/to/plugin.py` (optionally `--append-to registry/catalog.json`).
4. Run `telegram-sender plugin-validate path/to/plugin.py` and `telegram-sender plugin-validate registry/catalog.json --plugins-dir registry/plugins`.
5. Open a pull request (or a **Plugin registry submission** issue). Install never auto-enables third-party code. Maintainers re-sign the official catalog after merge.

### What is the web companion?

An optional **read-only** local monitor (`telegram-sender web-monitor` or Settings → Start & Open). It serves account health, campaign status, recent activity, and **live SVG charts** (hourly activity, send-status and health donuts, campaign bars) over stdlib HTTP — no extra packages, no send/control APIs. Chart JSON is also at `/api/charts`. Enable **Auto-start with GUI** / `WEB_COMPANION_AUTO_START` to start it in the background when the desktop app launches (no browser popup; Status in Settings). Keep the default `127.0.0.1` bind. Set `WEB_COMPANION_TOKEN` (or `--token`) for Bearer / `X-TMAS-Token` / `?token=` auth; non-localhost binds require a token. Prefer a TLS reverse proxy in front of localhost — see [Configuration](configuration.md).

### Can I back up to S3 instead of Google Drive?

Yes. Install `pip install '.[cloud]'`, set `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, and `S3_BUCKET` (optional `S3_ENDPOINT_URL` for MinIO / R2 / Wasabi / B2), then choose **S3-Compatible** under **Settings → Cloud Backup** and click **Verify S3 Credentials**. Google Drive, Dropbox, and OneDrive remain available as other providers. See [Configuration](configuration.md) and [Usage](usage.md).

### Can I back up to Dropbox?

Yes. Set `DROPBOX_ACCESS_TOKEN` (optional `DROPBOX_FOLDER`, default `/TMAS/backups`) from the [Dropbox App Console](https://www.dropbox.com/developers/apps), then choose **Dropbox** under **Settings → Cloud Backup** and click **Verify Dropbox Token**. Dropbox uses stdlib HTTP (no extra package). See [Configuration](configuration.md) and [Usage](usage.md).

### Can I back up to OneDrive?

Yes. Set `ONEDRIVE_ACCESS_TOKEN` (optional `ONEDRIVE_FOLDER`, default `TMAS/backups`) from a Microsoft Entra app with Graph delegated **Files.ReadWrite**, then choose **OneDrive** under **Settings → Cloud Backup** and click **Verify OneDrive Token**. OneDrive uses stdlib HTTP to Microsoft Graph (no extra package). See [Configuration](configuration.md) and [Usage](usage.md).

### How do I hand off my workspace to another machine?

Desktop TMAS is **single-operator**. Use **Settings → Cloud Backup → Export for Handoff…** (or `telegram-sender handoff-export`) for a full `.tmas-backup.zip` (database, safe settings, Telethon sessions), or **Export Templates/Campaigns…** / `--entities templates,campaigns` for a selective package. Entity imports support **merge** (upsert by name) or **replace**. Prefer an encryption password for off-machine transfer. Multi-user roles belong to [SendGram](https://www.sendgram.pro).

### How do I schedule a campaign?

When creating a campaign, set the "Start Time" field to schedule the campaign for a specific time. The campaign will start automatically at the scheduled time.

### How do I test a message before sending?

1. Go to the Testing tab
2. Enter your message content
3. Select a recipient
4. Click "Test Message"
5. Review the preview and results

## Account Management

### How many accounts can I manage?

There is no hard limit on the number of accounts you can manage. However, performance may vary based on your system resources.

### Can I use the same account on multiple devices?

Yes, Telegram allows the same account to be used on multiple devices. However, be careful with rate limits to avoid account restrictions.

### What happens if my account gets banned?

If your account gets banned, you'll need to contact Telegram support. The application includes rate limiting and compliance features to help prevent bans, but cannot guarantee account safety.

### How do I remove an account?

1. Go to the Accounts tab
2. Select the account you want to remove
3. Click "Remove Account"
4. Confirm the removal

## Campaign Management

### How do I pause a running campaign?

1. Go to the Campaigns tab
2. Select the campaign you want to pause
3. Click "Pause Campaign"

### How do I resume a paused campaign?

1. Go to the Campaigns tab
2. Select the paused campaign
3. Click "Resume Campaign"

### Can I edit a campaign after it's started?

You can pause a campaign, make changes, and resume it. However, some changes may not apply to messages already queued.

### How do I delete a campaign?

1. Go to the Campaigns tab
2. Select the campaign you want to delete
3. Click "Delete Campaign"
4. Confirm the deletion

## Rate Limiting

### What is rate limiting?

Rate limiting controls how many messages you send per minute to prevent account bans and comply with Telegram's limits.

### What rate limit should I use?

Start with a conservative rate limit (10-20 messages per minute) and gradually increase if needed. The default is 30 messages per minute.

### Can I disable rate limiting?

Rate limiting is recommended to prevent account bans. However, you can set a very high rate limit if needed, though this is not recommended.

## Templates

### How do I create a template?

1. Go to the Templates tab
2. Click "Create Template"
3. Enter template name and content
4. Select template type (Text, Spintax, etc.)
5. Save the template

### Can I use variables in templates?

Yes, you can use spintax syntax for variations. For recipient-specific variables, use placeholders like `{name}` or `{username}`.

### How do I organize templates?

Templates can be organized by category. Create categories in the Templates tab and assign templates to categories.

## Recipients

### How do I add recipients?

1. Go to the Recipients tab
2. Click "Add Recipient"
3. Enter username or phone number
4. Add to a recipient list (optional)

### Can I import recipients from a file?

Yes, you can import recipients from CSV files. Go to the Recipients tab and click "Import from CSV".

### What is a recipient list?

A recipient list is a collection of recipients that you can use for campaigns. This makes it easier to manage and organize recipients.

### How do I remove a recipient?

1. Go to the Recipients tab
2. Select the recipient you want to remove
3. Click "Remove Recipient"
4. Confirm the removal

## Troubleshooting

### The application won't start

- Check that Python 3.10+ is installed
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check the logs for error messages
- See [Troubleshooting Guide](troubleshooting.md) for more details

### I can't connect my Telegram account

- Verify your API credentials are correct
- Check your internet connection
- Ensure you're using the correct phone number format (with country code)
- Try disconnecting and reconnecting the account

### Messages aren't sending

- Check your internet connection
- Verify the recipient username or phone number is correct
- Check if rate limiting is preventing sends
- Review the logs for error messages
- Ensure your account is not restricted

### The application is slow

- Close other applications to free up resources
- Reduce the number of active campaigns
- Lower the rate limit
- Check your internet connection speed

### I'm getting rate limit errors

- Reduce the rate limit in campaign settings
- Increase delays between messages
- Use account warmup for new accounts
- Spread campaigns across multiple accounts

## Security and Privacy

### Is my data secure?

Yes, the application stores data locally on your computer. API credentials are encrypted. However, always follow best security practices.

### Are my messages encrypted?

Messages are sent through Telegram's encrypted network. The application itself does not store message content after sending (only logs).

### Can I use a proxy?

Yes, you can configure proxy settings for each account in the Accounts tab.

## Support

### Where can I get help?

- **Documentation**: See [Documentation Index](index.md)
- **Issues**: [GitHub Issues](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/issues)
- **Discussions**: [GitHub Discussions](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/discussions)
- **Email**: contact@voxhash.dev

### How do I report a bug?

Use the [Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.md) on GitHub Issues.

### How do I request a feature?

Use the [Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.md) on GitHub Issues.

## Contributing

### How can I contribute?

See the [Contributing Guide](../CONTRIBUTING.md) for details on how to contribute to the project.

### Do you accept pull requests?

Yes! We welcome pull requests. Please follow the contributing guidelines.

## Legal

### Is this legal?

The application is a tool. You are responsible for using it in compliance with Telegram's Terms of Service and applicable laws. Always respect recipients' privacy and follow anti-spam regulations.

### Can I use this for spam?

No. The application is designed for legitimate business purposes. Spam is illegal and violates Telegram's Terms of Service. Users are responsible for their actions.

## See Also

- [Troubleshooting Guide](troubleshooting.md) for common issues
- [Usage Guide](usage.md) for detailed usage instructions
- [API Documentation](api.md) for API reference
- [Configuration Guide](configuration.md) for configuration options

