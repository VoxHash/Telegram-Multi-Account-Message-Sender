# Telegram Multi-Account Message Sender Development Roadmap

> **Vision**: Keep a safety-first desktop Telegram campaign tool, then expand cloud sync, analytics, and hosting options without breaking the local workflow.

## Vision Statement

Deliver a reliable multi-account Telegram messaging desktop app (this repo) with a clear upgrade path to hosted SaaS ([SendGram](https://www.sendgram.pro)) for teams that outgrow single-machine installs.

## Current Status (v1.2.18)

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
- Optional Rust native accelerator (`tmms_native`) with prebuilt `tmms_native-linux-x86_64` on Releases
- Encrypted Google Drive cloud backup / restore MVP (Settings → Cloud Backup)
- Account health dashboard polish (scores, summary cards, actionable warnings)
- Broader unit coverage (campaign filters, settings validators, CLI, import smoke)
- Pydantic v2 field validators on Settings
- Circular-import hardening for `app.core` / `app.services` lazy exports

### In progress
- Performance and database/UI polishing based on real usage
- Contributor and sponsor community growth
- Offline-friendly restore messaging and additional cloud providers

### Latest release (v1.2.18 — 2026-10-24)
- Quality milestone: expanded unit tests, Pydantic v2 Settings validators, and core/services circular-import hardening

### Previous highlights
- **v1.2.17**: Account health dashboard polish (scores, summary cards, actionable warnings)
- **v1.2.16**: Cloud backup MVP (Google Drive encrypted export/restore)
- **v1.2.15**: Rust native accelerator + prebuilt Linux x86_64 binary on Releases
- **v1.2.14**: Documentation kit completion, SendGram upgrade path, repo hygiene
- **v1.2.13**: GHCR OCI image description metadata
- **v1.2.12**: PyPI `pandas` dependency, frozen translation bundling, GHCR publish workflow
- **v1.2.10–v1.2.11**: Python 3.11 syntax fix, session import path, test-message logging crash, stricter release CI

---

## Near-term priorities (next 1–2 releases)

Realistic, shippable work — not a full platform rewrite.

| Priority | Item | Outcome |
| --- | --- | --- |
| Done (v1.2.18) | Expand unit/integration tests | Cover campaign filter payloads, settings validators, CLI entrypoints, import smoke |
| Done (v1.2.18) | Pydantic v2 field validators | Remove V1 `@validator` deprecation warnings |
| Done (v1.2.18) | Circular-import hardening for `app.core` package exports | Safer `from app.core...` imports outside the GUI boot path |
| Low | Plugin marketplace / registry | Discover third-party plugins (after API stability) |
| Done (v1.2.17) | Account health dashboard polish | Clear health scores, summary cards, and actionable warnings in the UI |
| Done (v1.2.16) | Cloud backup MVP (encrypted export/restore) | Safe backup of app data to a user-owned Google Drive folder |
| Done (v1.2.15) | Ship prebuilt `tmms_native` in releases | Users get Rust accel without a local Rust toolchain |

---

## Phase plan

### Phase 2 focus (active): Cloud + automation quality
- [x] Encrypted cloud backup (Google Drive first; other providers later)
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
- [x] Broader pytest coverage beyond spintax/throttler (campaign filters, settings, CLI, import smoke; more integration coverage still welcome)
- [ ] Coverage reporting in CI summary
- [ ] Type hints on remaining untyped modules
- [x] Resolve known `app.core` ↔ `app.services` import cycle for package-level imports

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
