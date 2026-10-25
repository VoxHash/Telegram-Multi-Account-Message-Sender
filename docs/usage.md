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
- Optional AI rewrite / spintax / variations (user-supplied API key)
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

## Plugin Registry

1. Open **Plugins → Browse Registry**.
2. Search or filter by type; the catalog source (remote or bundled offline) is shown above the list.
3. Select **Install** on an available entry. The app downloads the plugin into `app_data/plugins/` and verifies SHA-256 when the catalog provides it.
4. Back on the Plugins list, **Enable** the plugin after reviewing the file. Install never auto-enables third-party code.
5. Optional: set `PLUGIN_REGISTRY_URL` in Settings / `.env` to point at a mirror. See [Configuration Guide](configuration.md) and [API Reference](api.md).

Sideloading with **Load Plugin** remains available for local `.py` files that are not in the catalog.

### Submitting a registry plugin

1. Copy `registry/templates/sample_filter_plugin.py` and use absolute imports only (`from app.core.plugin import …`).
2. Place the installable `.py` under `registry/plugins/` and add a catalog entry in `registry/catalog.json` (HTTPS `download_url`, bare `filename`, `sha256`).
3. Validate: `telegram-sender plugin-validate your_plugin.py` and `telegram-sender plugin-validate registry/catalog.json --plugins-dir registry/plugins`.
4. Open a pull request. See [CLI](cli.md) and [API](api.md).

## Web Companion (read-only monitoring, optional)

Monitor account health, campaign status, and recent activity in a browser without giving the companion send/control powers.

1. Open **Settings → General → Web Companion**, keep host `127.0.0.1`, optionally set/generate an auth token, then click **Start & Open in Browser**.
2. Optional: enable **Auto-start with GUI** (or `WEB_COMPANION_AUTO_START=true`) so launching the desktop app starts the companion in the background — no browser popup; check the Status line in Settings. Closing the app stops a GUI-started companion.
3. Or run headless: `telegram-sender web-monitor` (add `--token` for non-localhost; see [CLI Reference](cli.md) and [Configuration](configuration.md)).
4. Dashboard: `http://127.0.0.1:8765/` (append `?token=` when auth is enabled). Live SVG charts auto-refresh every 15s. JSON: `/api/status`, `/api/accounts`, `/api/campaigns`, `/api/activity`, `/api/overview`, `/api/charts`.
5. Mutating HTTP methods (`POST`/`PUT`/`PATCH`/`DELETE`) return **405**. Non-localhost binds require a token; prefer localhost behind Caddy/nginx with TLS.

## AI Copy Tools (optional)

1. Set `AI_API_KEY` (and optionally `AI_BASE_URL` / `AI_MODEL`) in `.env` or **Settings → General → AI Copy Tools**. See [Configuration Guide](configuration.md).
2. Open **Templates → Add/Edit Template**.
3. Enter draft text, then choose **Rewrite with AI**, **AI → Spintax**, or **AI variations**.
4. Review the result before saving. Placeholders like `{name}` are preserved when the model follows instructions.
5. With no API key configured, the buttons show a setup message and make no network calls.

## Cloud Backup (Google Drive + S3-compatible + Dropbox + OneDrive)

1. Install optional cloud packages for Drive/S3: `pip install '.[cloud]'`. Dropbox and OneDrive use stdlib HTTP (no extra package).
2. Configure Google Drive OAuth (`GOOGLE_DRIVE_CLIENT_ID` / `GOOGLE_DRIVE_CLIENT_SECRET`), S3 credentials (`S3_ACCESS_KEY_ID` / `S3_SECRET_ACCESS_KEY` / `S3_BUCKET`, optional `S3_ENDPOINT_URL` / `S3_REGION` / `S3_PREFIX`), Dropbox (`DROPBOX_ACCESS_TOKEN`, optional `DROPBOX_FOLDER`), and/or OneDrive (`ONEDRIVE_ACCESS_TOKEN`, optional `ONEDRIVE_FOLDER`) in `.env` — see [Configuration Guide](configuration.md).
3. Open **Settings → Cloud Backup** and choose the provider (Google Drive, S3-Compatible, Dropbox, or OneDrive).
4. **Google Drive**: click **Connect Google Drive** and approve access in your browser. **S3**: click **Verify S3 Credentials**. **Dropbox**: click **Verify Dropbox Token**. **OneDrive**: click **Verify OneDrive Token**.
5. Optionally set an encryption password, then click **Backup Now** to upload a `.tmas-backup.zip`.
6. Use **Refresh List** to see remote backups; select one and click **Restore Selected Backup** to replace the local database (a pre-restore snapshot is saved under `app_data/`).
7. **Offline / local restore**: use **Restore from Local File…**, or open a `.tmas-backup.zip` via OS file association (Linux MIME / macOS UTI after packaging install). No cloud connection required.
8. **Operator handoff (no cloud)**: click **Export for Handoff…** for a full `.tmas-backup.zip` (database, safe settings, Telethon sessions), or **Export Templates/Campaigns…** for a selective `entities.json` package. On restore, entity-only packages prompt for **merge** (upsert by name) or **replace** (soft-delete those kinds, then import). CLI: `handoff-export --entities …` and `handoff-import --mode merge|replace`. Desktop remains single-operator; multi-user roles belong to [SendGram](https://www.sendgram.pro). Prefer an encryption password for off-machine transfer.
9. **Restart the application** after a restore so all components reload the database.
10. Cloud restore and list/upload require network access to the selected provider. If you are offline or the provider is unreachable, the app shows a clear warning and **does not** replace the local database (local-file restore / handoff still work).

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

