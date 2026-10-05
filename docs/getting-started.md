# Getting Started

Welcome to Telegram Multi-Account Message Sender by VoxHash Technologies.

This guide orients new users before installation and first launch.

## Who this is for

Desktop operators and teams who need to manage multiple Telegram accounts, pace outbound campaigns, and keep sends within safety and rate limits — without building a custom Telethon stack.

## What you need

| Requirement | Details |
| --- | --- |
| Python | 3.10 or higher (3.11–3.12 recommended) |
| System packages | PyQt5 runtime deps (Qt libraries on Linux) |
| Telegram API | `TELEGRAM_API_ID` and `TELEGRAM_API_HASH` from [my.telegram.org/apps](https://my.telegram.org/apps) |
| Optional | Proxy credentials, Docker, Xvfb for headless GUI smoke tests |

## Path through the docs

1. [Installation](installation.md) — pip, source, Docker, installers, frozen builds
2. [Quick Start](quick-start.md) — configure `.env`, launch, add an account
3. [Configuration](configuration.md) — settings and environment variables
4. [Usage](usage.md) — campaigns, templates, recipients, testing
5. [Examples](examples/example-01.md) — practical walkthroughs

## Secrets you must supply

Copy `example_files/env_template.txt` to `.env` in the project root and set:

- `TELEGRAM_API_ID` — integer API ID from Telegram
- `TELEGRAM_API_HASH` — API hash string from Telegram

Without these values the app starts (database, UI, settings), but account authorization and live sends cannot complete. Never commit `.env`.

## Hosted alternative

For multi-tenant cloud delivery without a desktop install, see [SendGram](https://www.sendgram.pro).

## Support

- Docs index: [index.md](index.md)
- Issues: [GitHub Issues](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/issues)
- Security / direct contact: contact@voxhash.dev
