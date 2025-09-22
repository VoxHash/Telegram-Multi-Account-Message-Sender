# Configuration Examples

This document provides example configurations for different use cases of the Telegram Multi-Account Message Sender.

## 🏢 Business Use Cases

### Small Business (1-3 Accounts)
```env
# Conservative settings for small businesses
GLOBAL_MESSAGES_PER_MINUTE=2
GLOBAL_MESSAGES_PER_HOUR=20
GLOBAL_MESSAGES_PER_DAY=200
MAX_CONCURRENT_ACCOUNTS=2
WARMUP_ENABLED=true
WARMUP_TARGET_MESSAGES=5
WARMUP_INTERVAL_MINUTES=120
```

### Marketing Agency (5-10 Accounts)
```env
# Moderate settings for marketing agencies
GLOBAL_MESSAGES_PER_MINUTE=5
GLOBAL_MESSAGES_PER_HOUR=50
GLOBAL_MESSAGES_PER_DAY=500
MAX_CONCURRENT_ACCOUNTS=5
WARMUP_ENABLED=true
WARMUP_TARGET_MESSAGES=10
WARMUP_INTERVAL_MINUTES=60
```

### Enterprise (10+ Accounts)
```env
# Higher volume settings for enterprises
GLOBAL_MESSAGES_PER_MINUTE=10
GLOBAL_MESSAGES_PER_HOUR=100
GLOBAL_MESSAGES_PER_DAY=1000
MAX_CONCURRENT_ACCOUNTS=10
WARMUP_ENABLED=true
WARMUP_TARGET_MESSAGES=20
WARMUP_INTERVAL_MINUTES=30
```

## 🔧 Technical Configurations

### Development/Testing
```env
# Settings for development and testing
DEBUG=true
LOG_LEVEL=DEBUG
GLOBAL_MESSAGES_PER_MINUTE=1
GLOBAL_MESSAGES_PER_HOUR=10
GLOBAL_MESSAGES_PER_DAY=100
DRY_RUN=true
```

### Production
```env
# Settings for production use
DEBUG=false
LOG_LEVEL=INFO
GLOBAL_MESSAGES_PER_MINUTE=5
GLOBAL_MESSAGES_PER_HOUR=50
GLOBAL_MESSAGES_PER_DAY=500
DRY_RUN=false
```

### High-Security Environment
```env
# Settings for high-security environments
DEBUG=false
LOG_LEVEL=WARNING
SESSION_ENCRYPTION_KEY=your_32_character_encryption_key_here
AUTO_BACKUP=true
BACKUP_INTERVAL_HOURS=6
MAX_BACKUP_FILES=30
```

## 🌍 Regional Configurations

### North America
```env
# Optimized for North American time zones
TIMEZONE=America/New_York
WINDOW_WIDTH=1200
WINDOW_HEIGHT=800
```

### Europe
```env
# Optimized for European time zones
TIMEZONE=Europe/London
WINDOW_WIDTH=1200
WINDOW_HEIGHT=800
```

### Asia
```env
# Optimized for Asian time zones
TIMEZONE=Asia/Tokyo
WINDOW_WIDTH=1200
WINDOW_HEIGHT=800
```

## 📱 Account-Specific Settings

### New Account (Warmup Phase)
```csv
name,rate_limit_per_minute,rate_limit_per_hour,rate_limit_per_day,warmup_enabled,warmup_target_messages,warmup_interval_minutes
New Account,1,10,50,true,20,60
```

### Established Account (Normal Phase)
```csv
name,rate_limit_per_minute,rate_limit_per_hour,rate_limit_per_day,warmup_enabled,warmup_target_messages,warmup_interval_minutes
Established Account,5,50,500,false,0,0
```

### High-Volume Account
```csv
name,rate_limit_per_minute,rate_limit_per_hour,rate_limit_per_day,warmup_enabled,warmup_target_messages,warmup_interval_minutes
High Volume Account,10,100,1000,false,0,0
```

## 🔒 Proxy Configurations

### No Proxy
```env
PROXY_TYPE=none
```

### HTTP Proxy
```env
PROXY_TYPE=http
PROXY_HOST=proxy.example.com
PROXY_PORT=8080
PROXY_USERNAME=your_username
PROXY_PASSWORD=your_password
```

### SOCKS5 Proxy
```env
PROXY_TYPE=socks5
PROXY_HOST=proxy.example.com
PROXY_PORT=1080
PROXY_USERNAME=your_username
PROXY_PASSWORD=your_password
```

## 📊 Campaign Configurations

### Conservative Campaign
```csv
name,messages_per_minute,messages_per_hour,messages_per_day,random_jitter_seconds,respect_rate_limits,stop_on_error,max_retries
Conservative Campaign,1,10,100,30,true,true,5
```

### Moderate Campaign
```csv
name,messages_per_minute,messages_per_hour,messages_per_day,random_jitter_seconds,respect_rate_limits,stop_on_error,max_retries
Moderate Campaign,3,30,300,15,true,true,3
```

### Aggressive Campaign
```csv
name,messages_per_minute,messages_per_hour,messages_per_day,random_jitter_seconds,respect_rate_limits,stop_on_error,max_retries
Aggressive Campaign,10,100,1000,5,false,false,1
```

## 🎯 Template Configurations

### Simple Text Messages
```csv
name,message_type,use_spintax,use_ab_testing
Simple Text,TEXT,false,false
```

### Spintax Messages
```csv
name,message_type,use_spintax,use_ab_testing
Spintax Message,TEXT,true,false
```

### A/B Test Messages
```csv
name,message_type,use_spintax,use_ab_testing
AB Test Message,TEXT,false,true
```

### Media Messages
```csv
name,message_type,use_spintax,use_ab_testing
Media Message,PHOTO,false,false
```

## ⚠️ Safety Guidelines

### Rate Limiting Best Practices
- Start with conservative limits
- Monitor account health
- Gradually increase if needed
- Always respect Telegram's limits

### Account Management
- Use different accounts for different purposes
- Implement proper warmup for new accounts
- Monitor error rates and adjust accordingly
- Keep session files secure

### Content Guidelines
- Follow Telegram's Terms of Service
- Respect recipient preferences
- Use appropriate content
- Implement opt-out mechanisms

## 🔍 Monitoring and Alerts

### Log Levels
- **DEBUG**: Detailed information for debugging
- **INFO**: General information about operations
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for failed operations
- **CRITICAL**: Critical errors that stop the application

### Backup Settings
```env
AUTO_BACKUP=true
BACKUP_INTERVAL_HOURS=24
MAX_BACKUP_FILES=7
```

### Notification Settings
```env
ENABLE_NOTIFICATIONS=true
```

## 📝 Customization Tips

### Environment Variables
- All settings can be overridden per account
- Use environment variables for global defaults
- Test changes in development first

### CSV Imports
- Use the example files as templates
- Validate data before importing
- Start with small datasets

### Campaign Management
- Use dry-run mode for testing
- Monitor performance metrics
- Adjust settings based on results
