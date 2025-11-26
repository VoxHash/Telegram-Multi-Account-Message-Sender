# Example 2: Advanced Campaign with Spintax

This example demonstrates creating an advanced campaign with spintax variations and scheduling.

## Scenario

Send personalized messages to multiple recipients using spintax and schedule the campaign.

## Steps

1. **Create a Spintax Template**:
   - Go to Templates tab
   - Click "Add Template"
   - Name: `Personalized Welcome`
   - Content: `Hello {John|Jane|Alex}, welcome to {our|my} {amazing|fantastic} service!`

2. **Import Recipients**:
   - Go to Recipients tab
   - Click "Import CSV"
   - Select `example_files/recipients_example.csv`

3. **Create a Scheduled Campaign**:
   - Go to Campaigns tab
   - Click "Create Campaign"
   - Name: `Scheduled Welcome Campaign`
   - Type: `SCHEDULED`
   - Select the spintax template
   - Select all imported recipients
   - Set start time: Tomorrow at 9:00 AM
   - Rate limit: 5 messages per minute
   - Click "Create Campaign"

4. **Monitor the Campaign**:
   - View campaign status in Campaigns tab
   - Check logs in Logs tab
   - Monitor send progress

## Result

The campaign will start at the scheduled time and send personalized messages to all recipients, with each message using a different variation from the spintax template.

## Features Demonstrated

- Spintax message variations
- CSV recipient import
- Scheduled campaigns
- Rate limiting
- Campaign monitoring

## Next Steps

- See [Example 1](example-01.md) for basic usage
- Read [Usage Guide](../usage.md) for more details
- Check [API Documentation](../api.md) for programmatic access

