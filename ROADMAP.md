# Telegram Multi-Account Message Sender Development Roadmap

> **Vision**: Keep a safety-first desktop Telegram campaign tool, then expand cloud sync, analytics, and hosting options without breaking the local workflow.

## Vision Statement

Deliver a reliable multi-account Telegram messaging desktop app (this repo) with a clear upgrade path to hosted SaaS ([SendGram](https://www.sendgram.pro)) for teams that outgrow single-machine installs.

## Current Status (v1.2.29)

### Completed
- Multi-account management (phone auth + session import)
- Proxy support with connection testing (HTTP/HTTPS/SOCKS4/SOCKS5)
- Campaigns, templates (spintax), recipients, message testing, logging
- 13 languages, themes (including Dracula), Windows startup option
- Rate limiting, warmup, dry-run, and compliance controls
- Plugin API + example filter/analytics plugins
- PyPI package, GitHub Releases / installers, GHCR container images with OCI description metadata
- Documentation kit (getting started, installation, usage, API, FAQ, troubleshooting)
- CI: compileall, GUI import smoke, pip-install smoke, unit tests, coverage job summary (fail-under 20%)
- Optional Rust native accelerator (`tmms_native`) with prebuilt `tmms_native-linux-x86_64` on Releases
- Encrypted Google Drive cloud backup / restore MVP (Settings → Cloud Backup)
- Offline-friendly restore messaging when network / Drive is unavailable
- Account health dashboard polish (scores, summary cards, actionable warnings)
- Campaign analytics CSV/JSON export from the Dashboard
- Broader unit coverage (campaign filters, settings validators, CLI, import smoke, analytics export, offline cloud)
- Pydantic v2 field validators on Settings
- Circular-import hardening for `app.core` / `app.services` lazy exports
- Incremental type hints on high-value core/services modules
- **Blocking mypy** for `app/core`, `app/services`, `app/models` (strict flags; CI fails on errors)
- **Optional AI copy tools** (user-supplied OpenAI-compatible API key; stdlib HTTP; Templates rewrite / spintax / variations)
- **Plugin marketplace / registry** (curated JSON catalog, offline bundled fallback, SHA-256 install into `app_data/plugins/`)
- **Enhanced macOS/Linux packaging and file associations** (Linux desktop/MIME/`install.sh`; macOS `.app` Info.plist UTI; local `.tmas-backup.zip` restore)
- **Optional lightweight web companion (read-only monitoring)** (stdlib `http.server`; CLI `web-monitor` + Settings open; localhost by default; Bearer token auth + reverse-proxy guidance; live SVG charts; optional GUI auto-start)
- **Single-operator handoff export/import** (local `.tmas-backup.zip` with sessions; CLI `handoff-export` / `handoff-import`; Settings Export for Handoff)
- **Selective entity export + merge-on-import** (templates/campaigns `entities.json`; CLI `--entities` / `--mode merge|replace`; Settings Export Templates/Campaigns)

### In progress
- Performance and database/UI polishing based on real usage
- Contributor and sponsor community growth
- Additional cloud providers beyond Google Drive

### Latest release (v1.2.29 — 2026-10-24)
- Phase 4 leftover: selective template/campaign export and merge-on-import vs replace

### Previous highlights
- **v1.2.28**: Phase 4 slice: desktop single-operator export/import for handoff (local package + sessions; multi-user roles remain SendGram)
- **v1.2.27**: Phase 3 leftover: optional web companion auto-start with GUI (`WEB_COMPANION_AUTO_START`)
- **v1.2.26**: Phase 3 leftover: web companion richer live charts (`/api/charts` + SVG dashboard)
- **v1.2.25**: Phase 3 leftover: web companion Bearer token auth + reverse-proxy guidance for non-localhost
- **v1.2.24**: Phase 3: optional read-only web companion for local monitoring (accounts / campaigns / activity)
- **v1.2.23**: Phase 3 packaging: Linux desktop + MIME install; macOS `.app` document types; local backup file association restore
- **v1.2.22**: Plugin marketplace / registry: browse curated catalog, install verified plugins, offline bundled fallback
- **v1.2.21**: Optional AI-assisted copy tools behind user-supplied API keys (no AI SDK dependency)
- **v1.2.20**: Stricter mypy: blocking CI for core/services/models; typed JSON columns; remaining type gaps documented below
- **v1.2.19**: Quality + cloud UX: CI coverage summary, type-hint pass, offline restore messaging, analytics CSV/JSON export
- **v1.2.18**: Expanded unit tests, Pydantic v2 Settings validators, core/services circular-import hardening
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
| Done (v1.2.22) | Plugin marketplace / registry | Discover/install curated plugins via JSON catalog (remote + bundled offline); SHA-256 verify; Plugins → Browse Registry |
| Done (v1.2.21) | AI-assisted copy tools (optional keys) | Templates rewrite / spintax / variations via OpenAI-compatible Chat Completions; user-supplied `AI_API_KEY`; no SDK hard dependency |
| Done (v1.2.20) | Stricter mypy (blocking) | Strict flags + CI fail for `app/core`, `app/services`, `app/models`; GUI/plugins excluded |
| Done (v1.2.19) | Coverage reporting in CI summary | pytest-cov + GitHub Actions job summary; fail-under **20%** baseline on ubuntu/3.11 |
| Done (v1.2.19) | Type hints on remaining high-value modules | Incremental annotations on core/services (compliance, analytics, engine, campaign/warmup managers) |
| Done (v1.2.19) | Offline-friendly restore messaging | Clear UX when cloud restore/list/backup attempted offline or Drive unreachable |
| Done (v1.2.19) | Stronger campaign analytics export (CSV/JSON) | Real Dashboard export of campaign analytics |
| Done (v1.2.18) | Expand unit/integration tests | Cover campaign filter payloads, settings validators, CLI entrypoints, import smoke |
| Done (v1.2.18) | Pydantic v2 field validators | Remove V1 `@validator` deprecation warnings |
| Done (v1.2.18) | Circular-import hardening for `app.core` package exports | Safer `from app.core...` imports outside the GUI boot path |
| Done (v1.2.17) | Account health dashboard polish | Clear health scores, summary cards, and actionable warnings in the UI |
| Done (v1.2.16) | Cloud backup MVP (encrypted export/restore) | Safe backup of app data to a user-owned Google Drive folder |
| Done (v1.2.15) | Ship prebuilt `tmms_native` in releases | Users get Rust accel without a local Rust toolchain |

---

## Phase plan

### Phase 2 focus (active): Cloud + automation quality
- [x] Encrypted cloud backup (Google Drive first; other providers later)
- [x] Offline-friendly restore and conflict messaging
- [x] Stronger campaign analytics export (CSV/JSON)
- [x] AI-assisted copy tools only behind optional, user-supplied API keys (no hard dependency)
  - Leftover: non-English locale strings for AI UI keys (English kit shipped; other locales fall back to key path until translated)
  - Leftover: provider presets beyond generic OpenAI-compatible base URL (Azure path quirks, Anthropic native API)
- [x] Plugin marketplace / registry (curated catalog discover + verified install)
  - Leftover: community submissions beyond the two official registry plugins; signed catalogs

### Phase 3 (later): Platform expansion
- [x] Enhanced macOS/Linux packaging and file associations
  - Leftover: Apple code signing / notarization; Windows file-association installer polish
- [x] Optional lightweight web companion (read-only monitoring first)
  - [x] Auth token / reverse-proxy guidance for non-localhost (v1.2.25)
  - [x] Richer live charts (v1.2.26)
  - [x] Optional auto-start with GUI (v1.2.27)
- [ ] Mobile companion deferred until web companion proves demand

### Phase 4 (later): Team / enterprise
- [x] Multi-user roles belong primarily to SendGram (hosted) — documented; no desktop RBAC
- [x] Desktop remains single-operator with export/import for handoff (v1.2.28)
- [x] Selective entity export (templates/campaigns only) + merge-on-import vs replace (v1.2.29)
- [ ] Broader developer SDK polish as registry submissions grow

---

## Technical debt (tracked)

### Code quality
- [x] Broader pytest coverage beyond spintax/throttler (campaign filters, settings, CLI, import smoke; more integration coverage still welcome)
- [x] Coverage reporting in CI summary (Actions job summary + fail-under 20% baseline; Codecov upload remains optional)
- [x] Type hints on remaining high-value untyped modules (incremental)
- [x] Stricter mypy for `app/core`, `app/services`, `app/models` (blocking in CI)
- [ ] Extend blocking mypy to `app/gui` and `app/plugins` (large PyQt annotation surface; deferred)
- [ ] Optional: type `app/utils` / `app/cli.py` under the same blocking gate
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
