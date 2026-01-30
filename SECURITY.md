# Security Policy

## Supported Versions

We provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.2.x   | :white_check_mark: |
| < 1.2   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability, please **do not** open a public issue. Instead, please report it via one of the following methods:

### Email (Preferred)
Send an email to **contact@voxhash.dev** with:
- A clear description of the vulnerability
- Steps to reproduce the issue
- Potential impact assessment
- Suggested fix (if available)
- Affected versions (if known)

### Vulnerability Report Template

```
Subject: Security Vulnerability Report - [Brief Description]

Vulnerability Type: [e.g., SQL Injection, XSS, Authentication Bypass]
Severity: [Critical/High/Medium/Low]
Affected Versions: [e.g., 1.2.0 - 1.2.8]

Description:
[Detailed description of the vulnerability]

Steps to Reproduce:
1. [Step 1]
2. [Step 2]
3. [Step 3]

Expected Behavior:
[What should happen]

Actual Behavior:
[What actually happens]

Impact:
[Potential impact if exploited]

Suggested Fix:
[If you have a fix or mitigation]

Additional Context:
[Any other relevant information]
```

### Response Time
- We will acknowledge receipt of your report within **48 hours**
- We will provide a detailed response within **7 days**
- We will keep you informed of the progress toward a fix
- Critical vulnerabilities will be addressed within **24 hours**

### Disclosure Policy
- We will work with you to understand and resolve the issue quickly
- We will credit you for the discovery (if desired)
- We will not disclose the vulnerability publicly until a fix is available
- We follow responsible disclosure practices

## Security Best Practices

### For Users
- Keep your application updated to the latest version
- Use strong, unique API credentials
- Never share your session files or API keys
- Regularly review your account activity
- Use rate limiting to prevent abuse

### For Developers
- Never commit sensitive data (API keys, credentials, session files)
- Use environment variables for configuration
- Keep dependencies updated
- Review code changes for security implications
- Follow secure coding practices

## Security Considerations

This application handles sensitive data including:
- Telegram API credentials
- Session files
- User account information
- Message content

All data is stored locally and encrypted where possible. We recommend:
- Using strong encryption for session files
- Regularly rotating API credentials
- Implementing proper access controls
- Monitoring for suspicious activity

## Contact

For security-related inquiries, contact: **contact@voxhash.dev**

