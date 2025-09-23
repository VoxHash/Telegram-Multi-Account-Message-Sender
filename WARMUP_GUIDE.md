# Account Warmup Guide

## Overview

The Account Warmup feature is designed to gradually increase the activity of your Telegram accounts to avoid spam detection and rate limiting. This is especially important for new accounts or accounts that haven't been used for a while.

## How It Works

1. **Gradual Message Sending**: The warmup process sends test messages to your own "Saved Messages" at regular intervals
2. **Progressive Increase**: Message frequency gradually increases over time to simulate natural usage
3. **Safety First**: Messages are only sent to yourself, so there's no risk of spamming others
4. **Automatic Management**: The system automatically manages the warmup process based on your settings

## Setting Up Warmup

### 1. Enable Warmup for an Account

1. Go to the **Accounts** tab
2. Click **Edit** on the account you want to warm up
3. In the **Warmup Settings** section:
   - Check **Enable Warmup**
   - Set **Target Messages** (e.g., 50-100 messages)
   - Set **Interval** (e.g., 5-10 minutes between messages)
4. Click **Save Account**

### 2. Configure Global Warmup Settings

1. Go to the **Settings** tab
2. In the **Rate Limiting** section:
   - Set **Warmup Messages** (total messages to send)
   - Set **Warmup Interval** (minutes between messages)
3. Click **Save Changes**

## Using Warmup Controls

### In Settings Tab

The **Safety** tab contains warmup controls:

- **Start Warmup for All Accounts**: Begins warmup for all eligible accounts
- **Stop All Warmup**: Stops all warmup processes
- **Reset Warmup Progress**: Resets warmup progress for all accounts

### Account Status

You can monitor warmup progress in the **Accounts** tab:
- **Warmup Messages Sent**: Shows how many warmup messages have been sent
- **Warmup Target**: Shows the target number of messages
- **Warmup Status**: Shows if warmup is complete or in progress

## Warmup Process

### Phase 1: Initial Messages (Days 1-3)
- Sends 1-2 messages per day
- Very conservative approach
- Focuses on establishing account activity

### Phase 2: Gradual Increase (Days 4-7)
- Increases to 3-5 messages per day
- Maintains natural usage patterns
- Builds account reputation

### Phase 3: Normal Activity (Days 8+)
- Reaches target message frequency
- Simulates regular user behavior
- Account is considered "warmed up"

## Best Practices

### 1. Start Small
- Begin with 20-30 target messages
- Use longer intervals (10-15 minutes)
- Monitor account status carefully

### 2. Monitor Progress
- Check the **Accounts** tab regularly
- Look for any error messages
- Adjust settings if needed

### 3. Account Requirements
- Account must be **Online** and **Authorized**
- Account must have **Warmup Enabled**
- Account must not be in use by campaigns

### 4. Safety Guidelines
- Never warm up multiple accounts simultaneously
- Use different intervals for different accounts
- Monitor Telegram's rate limits

## Troubleshooting

### Common Issues

1. **"Account not online"**
   - Ensure the account is properly authorized
   - Check internet connection
   - Try re-authorizing the account

2. **"Warmup already in progress"**
   - Wait for current warmup to complete
   - Check if another process is using the account

3. **"No accounts eligible for warmup"**
   - Verify accounts have warmup enabled
   - Check account status
   - Ensure accounts are not in use

### Error Messages

- **"Telegram client not initialized"**: Account needs to be authorized first
- **"Rate limit exceeded"**: Wait before sending more messages
- **"Account banned"**: Account may be restricted by Telegram

## Advanced Configuration

### Custom Warmup Patterns

You can create custom warmup patterns by modifying the warmup settings:

```python
# Example: Custom warmup for high-volume accounts
warmup_messages = 200
warmup_interval = 3  # 3 minutes between messages
```

### Multiple Account Warmup

For multiple accounts:
1. Enable warmup for each account individually
2. Use different intervals to avoid conflicts
3. Monitor all accounts regularly

## Monitoring and Logs

### View Warmup Logs

1. Go to the **Logs** tab
2. Select **Send Logs**
3. Filter by **Campaign**: "Warmup"
4. Monitor message sending progress

### Warmup Status Indicators

- **🟢 Complete**: Warmup finished successfully
- **🟡 In Progress**: Currently warming up
- **🔴 Failed**: Warmup encountered errors
- **⚪ Not Started**: Warmup not yet begun

## Safety Features

### Rate Limiting
- Respects Telegram's rate limits
- Automatically adjusts sending frequency
- Prevents account suspension

### Error Handling
- Stops on critical errors
- Retries failed messages
- Logs all activities

### Account Protection
- Only sends to "Saved Messages"
- No external recipients
- Safe testing environment

## Tips for Success

1. **Patience**: Warmup takes time - don't rush it
2. **Consistency**: Keep accounts active regularly
3. **Monitoring**: Check progress daily
4. **Adjustment**: Modify settings based on results
5. **Documentation**: Keep track of what works

## Support

If you encounter issues with the warmup feature:

1. Check the **Logs** tab for error messages
2. Verify account settings and status
3. Ensure proper API credentials
4. Contact support if problems persist

Remember: The warmup feature is designed to help you use Telegram accounts safely and effectively. Always follow Telegram's Terms of Service and use the feature responsibly.
