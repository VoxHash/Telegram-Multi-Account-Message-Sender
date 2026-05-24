# Configuration Guide

Learn how to configure Telegram Multi-Account Message Sender.

## Application Settings

### Accessing Settings

1. Launch the application
2. Go to the Settings tab
3. Configure your preferences

### Basic Configuration

#### Telegram API Credentials

- **API ID**: Your Telegram API ID (from my.telegram.org)
- **API Hash**: Your Telegram API Hash (from my.telegram.org)

#### Theme Settings

- **Theme**: Choose from Light, Dark, Auto, or Dracula
- **Language**: Select from 13 supported languages

#### Logging Settings

- **Log Level**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Log File Location**: Default is `app_data/logs/`

## Environment Variables

You can configure the application using environment variables. See `example_files/env_template.txt` for all available options.

### Key Environment Variables

- `TELEGRAM_API_ID`: Your Telegram API ID
- `TELEGRAM_API_HASH`: Your Telegram API Hash
- `DATABASE_URL`: Database connection string
- `LOG_LEVEL`: Logging level
- `THEME`: Application theme
- `GOOGLE_DRIVE_CLIENT_ID`: OAuth client ID for Google Drive cloud backups
- `GOOGLE_DRIVE_CLIENT_SECRET`: OAuth client secret for Google Drive cloud backups

### Google Drive Cloud Backup (optional)

Install cloud dependencies:

```bash
pip install '.[cloud]'
```

1. Create an OAuth 2.0 **Desktop** client in [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
2. Add the client ID and secret to `.env`:

```env
GOOGLE_DRIVE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_DRIVE_CLIENT_SECRET=your-client-secret
```

3. In the app, open **Settings → Cloud Backup** and click **Connect Google Drive**.
4. Complete the browser OAuth flow; tokens are stored encrypted under `app_data/cloud/`.

## Account Configuration

### Adding Accounts

1. Go to Accounts tab
2. Click "Add Account"
3. Enter phone number
4. Complete authorization

### Account Settings

- **Rate Limits**: Messages per minute/hour/day
- **Proxy Settings**: Optional proxy configuration
- **Warmup Settings**: Account warmup configuration

## Campaign Configuration

### Campaign Settings

- **Rate Limiting**: Global rate limits
- **Scheduling**: Campaign scheduling options
- **Retry Logic**: Retry configuration

## Database Configuration

The application uses SQLite by default. Database location: `app_data/app.db`

## Advanced Configuration

For advanced configuration options, see the [API Documentation](api.md).

## Troubleshooting

See [Troubleshooting Guide](troubleshooting.md) for configuration issues.

