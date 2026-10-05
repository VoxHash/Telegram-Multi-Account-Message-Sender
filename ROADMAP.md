# Telegram Multi-Account Message Sender Development Roadmap

> **Vision**: Keep a safety-first desktop Telegram campaign tool, then expand cloud sync, analytics, and hosting options without breaking the local workflow.

## Vision Statement

Deliver a reliable multi-account Telegram messaging desktop app (this repo) with a clear upgrade path to hosted SaaS ([SendGram](https://www.sendgram.pro)) for teams that outgrow single-machine installs.

## Current Status (v1.2.14)

### Completed
- Multi-account management (phone auth + session import)
- Proxy support with connection testing (HTTP/HTTPS/SOCKS4/SOCKS5)
- Campaigns, templates (spintax), recipients, message testing, logging
- 13 languages, themes (including Dracula), Windows startup option
- Rate limiting, warmup, dry-run, and compliance controls
- Plugin API + example filter/analytics plugins
- PyPI package, GitHub Releases / installers, GHCR container images with OCI description metadata
- Documentation kit (getting started, installation, usage, API, FAQ, troubleshooting)
- CI: compileall, GUI import smoke, pip-install smoke, unit tests

### In progress
- Performance and database/UI polishing based on real usage
- Contributor and sponsor community growth
- Cloud backup / sync (partial work exists on feature branches; not merged as a finished product)

### Latest release (v1.2.14 — 2026-10-05)
- Documentation kit completion (getting-started + installation; PyInstaller notes folded in)
- README SendGram upgrade path and shield badges
- Repository hygiene (stray markdown removed, `.gitignore` tightened)

### Previous highlights
- **v1.2.13**: GHCR OCI image description metadata
- **v1.2.12**: PyPI `pandas` dependency, frozen translation bundling, GHCR publish workflow
- **v1.2.10–v1.2.11**: Python 3.11 syntax fix, session import path, test-message logging crash, stricter release CI

---

## Near-term priorities (next 1–2 releases)

Realistic, shippable work — not a full platform rewrite.

| Priority | Item | Outcome |
| --- | --- | --- |
| High | Cloud backup MVP (encrypted export/restore) | Safe backup of app data to a user-owned cloud folder |
| High | Account health dashboard polish | Clear health scores and actionable warnings in the UI |
| Medium | Expand unit/integration tests | Cover campaign filter payloads, settings, and CLI entrypoints |
| Medium | Pydantic v2 field validators | Remove V1 `@validator` deprecation warnings |
| Medium | Circular-import hardening for `app.core` package exports | Safer `from app.core...` imports outside the GUI boot path |
| Low | Plugin marketplace / registry | Discover third-party plugins (after API stability) |

---

## Phase plan

### Phase 2 focus (active): Cloud + automation quality
- [ ] Encrypted cloud backup (Google Drive first; other providers later)
- [ ] Offline-friendly restore and conflict messaging
- [ ] Stronger campaign analytics export (CSV/JSON)
- [ ] AI-assisted copy tools only behind optional, user-supplied API keys (no hard dependency)

### Phase 3 (later): Platform expansion
- [ ] Enhanced macOS/Linux packaging and file associations
- [ ] Optional lightweight web companion (read-only monitoring first)
- [ ] Mobile companion deferred until web companion proves demand

### Phase 4 (later): Team / enterprise
- [ ] Multi-user roles belong primarily to SendGram (hosted)
- [ ] Desktop remains single-operator with export/import for handoff
- [ ] Developer SDK / plugin docs after marketplace demand appears

---

## Technical debt (tracked)

### Code quality
- [ ] Broader pytest coverage beyond spintax/throttler
- [ ] Coverage reporting in CI summary
- [ ] Type hints on remaining untyped modules
- [ ] Resolve known `app.core` ↔ `app.services` import cycle for package-level imports

### Documentation
- [x] API, FAQ, troubleshooting, installation, getting-started
- [ ] Short video walkthrough (external; link from README when published)

### Security
- [ ] Periodic dependency audit
- [ ] Session/credential storage review
- [ ] Document threat model for proxies and shared machines

---

## Community

- [x] GitHub Sponsors + issue/PR templates + CODE_OF_CONDUCT
- [ ] Discord or Discussions-first community channel
- [ ] Beta tester list for cloud-backup MVP

---

## Support

- GitHub Issues / Discussions
- Docs: `docs/index.md`
- Contact: contact@voxhash.dev
- Hosted product: https://www.sendgram.pro

---

**Made with ❤️ by VoxHash Technologies**
