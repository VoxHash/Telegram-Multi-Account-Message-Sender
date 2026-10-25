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

## Threat model (proxies and shared machines)

This desktop app is a **single-operator** tool. Trust boundary is the local OS user account that runs the GUI/CLI. Hosted multi-user roles belong to [SendGram](https://www.sendgram.pro).

### Assets

| Asset | Where it lives | Why it matters |
| --- | --- | --- |
| Telethon `.session` files | `app_data/sessions/` (configurable) | Bearer credentials — reading them lets an attacker impersonate the Telegram account |
| Telegram `API_ID` / `API_HASH` | `.env` / Settings | Required to create clients; treat as secrets |
| Proxy username/password | SQLite `accounts` table (`app_data/app.db`) | Can expose upstream proxy access and traffic metadata |
| Cloud / AI tokens | `.env`, encrypted Drive tokens under `app_data/cloud/` | Access to backups or paid AI APIs |
| Message content & recipients | SQLite + logs | Privacy / compliance exposure |
| Web companion token | Settings / env | Protects read-only monitor when bound beyond localhost |

### Adversaries and assumptions

| Scenario | Assumption | Guidance |
| --- | --- | --- |
| Dedicated personal machine | Only you use the OS account | Default layout is acceptable; still run `security-check` after install |
| Shared / lab / family PC | Other local users or admins may read your home directory | Use a dedicated OS user; run `security-harden`; encrypt the disk; lock the screen |
| Untrusted HTTP/SOCKS proxy | Proxy operator can see destinations and (for non-TLS or misconfigured TLS) content | Prefer trusted proxies; SOCKS5 over a network you control; never point campaigns through a random public proxy |
| Compromised backup package | `.tmas-backup.zip` without a password is readable offline | Always password-encrypt handoff/cloud packages that include sessions |
| Non-localhost web companion | LAN peers can hit the monitor | Require `WEB_COMPANION_TOKEN`; bind `127.0.0.1` behind a TLS reverse proxy |

### Out of scope (for this desktop threat model)

- Multi-tenant RBAC, SSO, or remote admin (use SendGram)
- Protecting secrets from a malware process running as the same OS user
- Telegram server-side account takeover unrelated to local session theft

## Session / credential storage review

Findings from the v1.2.45 storage review:

1. **Sessions are not encrypted at rest by Telethon.** File-system permissions are the primary control. On POSIX, prefer `0700` for the sessions directory and `0600` for `.session` files.
2. **`.env` is plaintext.** API hashes, AI keys, and cloud tokens are written by Settings. Keep the file owner-only (`0600`) and never commit it (see `.gitignore`).
3. **SQLite may hold proxy credentials** (`proxy_username` / `proxy_password`) and account metadata. Protect `app_data/app.db` the same way as sessions.
4. **Cloud backup packages** can encrypt payloads with a password (Fernet via `app.utils.crypto`). Google Drive OAuth tokens under `app_data/cloud/` should stay owner-only. Settings export for backups intentionally **omits** `telegram_api_id` / `telegram_api_hash` and proxy env keys.
5. **Handoff packages that include sessions are as sensitive as the sessions directory.** Use `--password` and treat the zip as secret.

### Operator commands

```bash
telegram-sender security-check
telegram-sender security-harden
```

- `security-check` — report path kinds and permission posture (never prints secret values)
- `security-harden` — on POSIX, `chmod` sessions / `.env` / `app.db` / `app_data/cloud/` to owner-only; on Windows, reports guidance only (use NTFS ACLs)

Exit code `1` means one or more `warn`/`critical` findings.

## Periodic dependency audit

| Mechanism | Detail |
| --- | --- |
| CI workflow | `.github/workflows/dependency-audit.yml` runs `pip-audit -r requirements.txt` weekly (Monday), on `workflow_dispatch`, and when dependency manifests change |
| Local | `pip install pip-audit && pip-audit -r requirements.txt` (or `uvx pip-audit -r requirements.txt`) |
| Baseline (v1.2.45) | Runtime `requirements.txt` audit: **no known vulnerabilities** |

When audit finds a CVE: pin or upgrade the dependency, note the change in `CHANGELOG.md`, and cut a patch release if the issue is exploitable in our usage.

## Security Best Practices

### For Users
- Keep your application updated to the latest version
- Use strong, unique API credentials from https://my.telegram.org
- Never share session files, handoff zips, or API keys
- Run `security-check` on shared machines; prefer a dedicated OS user
- Use rate limiting and dry-run before large campaigns
- Prefer trusted proxies only; assume proxy operators can log destinations

### For Developers
- Never commit sensitive data (API keys, credentials, session files, `*.priv`)
- Use environment variables / `.env` (gitignored) for configuration
- Keep dependencies updated; watch the dependency-audit workflow
- Review code changes for security implications
- Follow secure coding practices

## Security Considerations

This application handles sensitive data including:
- Telegram API credentials
- Session files
- Proxy credentials
- User account information
- Message content

All operational data is stored locally. Encryption is used for password-protected backup/handoff packages and Drive token blobs where implemented. We recommend:
- Owner-only permissions via `security-harden` (POSIX)
- Regularly rotating API credentials and cloud tokens
- Full-disk encryption on laptops
- Monitoring Telegram account activity for unexpected sessions

## Contact

For security-related inquiries, contact: **contact@voxhash.dev**
