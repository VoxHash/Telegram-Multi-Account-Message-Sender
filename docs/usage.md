# Usage Guide

Complete guide to using Telegram Multi-Account Message Sender.

## Overview

The application provides a graphical interface for managing multiple Telegram accounts and sending messages.

## Main Features

### Account Management

- Add multiple Telegram accounts
- Manage account settings
- Monitor account status
- Configure rate limits

### Template Management

- Create message templates
- Use spintax for variations
- A/B testing support
- Template organization

### Recipient Management

- Add individual recipients
- Import from CSV
- Organize by groups
- Manage recipient lists

### Campaign Management

- Create campaigns
- Schedule messages
- Monitor campaign status
- Pause/resume campaigns

### Message Testing

- Test messages before sending
- Preview message content
- Validate templates
- Check recipient information

## Basic Workflow

1. **Setup**: Configure API credentials and settings
2. **Add Accounts**: Add and authorize Telegram accounts
3. **Create Templates**: Create message templates
4. **Add Recipients**: Add or import recipients
5. **Create Campaigns**: Create and launch campaigns
6. **Monitor**: Track campaign progress and logs

## Cloud Backup (Google Drive)

1. Configure `GOOGLE_DRIVE_CLIENT_ID` and `GOOGLE_DRIVE_CLIENT_SECRET` in `.env` (see [Configuration Guide](configuration.md)).
2. Install optional cloud packages: `pip install '.[cloud]'`.
3. Open **Settings → Cloud Backup**.
4. Click **Connect Google Drive** and approve access in your browser.
5. Optionally set an encryption password, then click **Backup Now** to upload a `.tmas-backup.zip` to Drive.
6. Use **Refresh List** to see remote backups; select one and click **Restore Selected Backup** to replace the local database (a pre-restore snapshot is saved under `app_data/`).
7. **Restart the application** after a restore so all components reload the database.
8. Restore and list/upload require network access to Google Drive. If you are offline or Drive is unreachable, the app shows a clear warning and **does not** replace the local database.

## Analytics export (Dashboard)

From the **Dashboard** header:

1. Click **Export CSV…** or **Export JSON…**.
2. Choose a save path. The export includes a campaign summary table plus flattened metrics (CSV) or a structured overview with per-campaign reports (JSON).
3. Empty databases (no campaigns) show a notice instead of writing a file.

## Advanced Features

### Spintax

Create message variations using spintax syntax:

```
Hello {John|Jane|Alex}, welcome to {our|my} service!
```

### Scheduling

Schedule campaigns for specific times with timezone support.

### Rate Limiting

Configure rate limits to respect Telegram's limits and prevent account bans.

## Account Health (Dashboard)

The **Dashboard** tab includes an Account Health section that scores each account (0–100) from connection status, success rate, recent 24h errors, warmup progress, and activity.

- Summary cards show average score, healthy accounts, accounts that need attention, and critical/offline counts.
- The table lists worst scores first; select a row for warnings and recommended actions (also available as row tooltips).
- Offline, error, suspended, and inactive accounts get clear status labels and next-step guidance (reconnect, test connection, finish warmup).

## Best Practices

- Start with conservative rate limits
- Test messages before sending campaigns
- Monitor account health on the Dashboard and act on warnings before large campaigns
- Use warmup for new accounts
- Keep templates organized

## Examples

See [Examples](examples/example-01.md) for practical usage examples.

## Troubleshooting

See [Troubleshooting Guide](troubleshooting.md) for common issues.

