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

## Best Practices

- Start with conservative rate limits
- Test messages before sending campaigns
- Monitor account health
- Use warmup for new accounts
- Keep templates organized

## Examples

See [Examples](examples/example-01.md) for practical usage examples.

## Troubleshooting

See [Troubleshooting Guide](troubleshooting.md) for common issues.

