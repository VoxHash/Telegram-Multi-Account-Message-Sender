# Telegram Multi-Account Message Sender Development Roadmap

> **Vision**: Keep a safety-first desktop Telegram campaign tool, then expand cloud sync, analytics, and hosting options without breaking the local workflow.

## Vision Statement

Deliver a reliable multi-account Telegram messaging desktop app (this repo) with a clear upgrade path to hosted SaaS ([SendGram](https://www.sendgram.pro)) for teams that outgrow single-machine installs.

## Current Status (v1.2.49)

### Completed
- Multi-account management (phone auth + session import)
- Proxy support with connection testing (HTTP/HTTPS/SOCKS4/SOCKS5)
- Campaigns, templates (spintax), recipients, message testing, logging
- 13 languages, modern dense themes (including Dracula) with navigation rail shell, Windows startup option
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
- **Blocking mypy** for `app/core`, `app/services`, `app/models`, `app/plugins`, `app/utils`, `app/cli.py`, and expanded GUI subset (`main`, `theme`, `about`, `account_widget`, `campaign_widget`, `cloud_backup_widget`, `dashboard_widget`, `log_widget`, `plugin_widget`, `recipient_widget`, `settings_widget`, `template_widget`, `testing_widget`, `telegram_selector`, package inits) (strict flags; CI fails on errors)
- **Optional AI copy tools** (user-supplied API key; provider presets: OpenAI-compatible, Azure OpenAI, Anthropic Messages API; stdlib HTTP; Templates rewrite / spintax / variations; AI UI strings in all 13 locales)
- **Plugin marketplace / registry** (curated JSON catalog, offline bundled fallback, SHA-256 install into `app_data/plugins/`)
- **Enhanced macOS/Linux packaging and file associations** (Linux desktop/MIME/`install.sh`; macOS `.app` Info.plist UTI; local `.tmas-backup.zip` restore)
- **Windows file-association installer polish** (`install.ps1` + release zip; HKCU ProgID `dev.voxhash.tmas-backup`) — v1.2.49
- **Optional lightweight web companion (read-only monitoring)** (stdlib `http.server`; CLI `web-monitor` + Settings open; localhost by default; Bearer token auth + reverse-proxy guidance; live SVG charts; optional GUI auto-start)
- **Single-operator handoff export/import** (local `.tmas-backup.zip` with sessions; CLI `handoff-export` / `handoff-import`; Settings Export for Handoff)
- **Selective entity export + merge-on-import** (templates/campaigns `entities.json`; CLI `--entities` / `--mode merge|replace`; Settings Export Templates/Campaigns)
- **Developer SDK polish for registry submissions** (`plugin-validate` CLI; catalog schema/SHA-256 helpers; sample filter template)
- **S3-compatible cloud backup** (AWS S3 / MinIO / R2 / Wasabi / B2 via boto3; Settings provider selector)
- **Dropbox cloud backup** (Bearer access token + folder; stdlib HTTP; Settings provider selector)
- **OneDrive cloud backup** (Microsoft Graph Bearer token + folder; stdlib HTTP; Settings provider selector)
- **Proton Drive cloud backup** (official `proton-drive` CLI + OS keyring session; Settings provider selector) — v1.2.48
- **Signed plugin catalogs** (Ed25519 + `json-sorted-compact`; official `trusted_keys.json`; `plugin-catalog-sign` CLI)
- **Richer community registry submissions** (Whitespace Normalize + Failure Counter installables; analytics sample template; `plugin-catalog-entry` CLI; plugin submission issue template)
- **Further third-party registry volume** (Emoji Strip Filter + Success Counter Analytics; six downloadable catalog plugins)
- **Security posture** (threat model for proxies/shared machines; session/credential storage review + `security-check`/`security-harden`; periodic `pip-audit` CI)
- **Discussions-first community channel** (GitHub Discussions enabled; SUPPORT / README / CONTRIBUTING routing; welcome + Q&A + beta threads; Discord deferred until a real invite exists)
- **Beta tester interest path** (Discussions #2 + `beta_tester` issue template / label)

### In progress
- Performance and database/UI polishing based on real usage
- Contributor and sponsor community growth
- Ongoing community registry PRs beyond the curated seed set

### Latest release (v1.2.49 — 2026-10-25)
- Phase 3 leftover: Windows file-association installer polish (`install.ps1` + `*-windows.zip`)

### Previous highlights
- **v1.2.48**: Phase 2: Proton Drive cloud backup via official `proton-drive` CLI (out-of-process; OS keyring auth)
- **v1.2.47**: UI: modern desktop-client shell (navigation rail, dense dark theme, VoxHash teal accent)
- **v1.2.46**: Community: Discussions-first channel + beta tester interest path (no Discord invent)
- **v1.2.45**: Security: threat model, credential storage review/harden CLI, periodic dependency audit
- **v1.2.44**: Technical debt: type `app/utils` / `app/cli.py` under the same blocking mypy gate
- **v1.2.43**: Technical debt: expand blocking mypy GUI subset (`settings_widget` / `account_widget` / `campaign_widget`)
- **v1.2.42**: Technical debt: expand blocking mypy GUI subset (`log_widget` / `template_widget` / `recipient_widget`)
- **v1.2.41**: Technical debt: expand blocking mypy GUI subset (`main` / `cloud_backup_widget` / `dashboard_widget`)
- **v1.2.40**: Technical debt: expand blocking mypy GUI subset (`plugin_widget` / `testing_widget` / `telegram_selector`)
- **v1.2.39**: Technical debt: expand blocking mypy to `app/plugins` + practical GUI subset (`theme` / `about` / inits)
- **v1.2.38**: Phase 2 leftover: AI provider presets (Azure OpenAI path/api-version + Anthropic Messages API)
- **v1.2.37**: Phase 2 leftover: AI non-English locale strings for AI UI keys (all 13 languages)
- **v1.2.36**: Phase 2/4 leftover: further third-party registry volume (Emoji Strip + Success Counter)
- **v1.2.35**: Phase 2/4 leftover: richer community registry submissions (seed plugins + catalog-entry tooling)
- **v1.2.34**: Phase 4 leftover: signed plugin catalogs (Ed25519)
- **v1.2.33**: Phase 2 leftover: OneDrive cloud backup provider (Microsoft Graph)
- **v1.2.32**: Phase 2 leftover: Dropbox cloud backup provider (beyond Google Drive + S3)
- **v1.2.31**: Phase 2: S3-compatible cloud backup provider (beyond Google Drive)
- **v1.2.30**: Phase 4: broader developer SDK polish as registry submissions grow
- **v1.2.29**: Phase 4 leftover: selective template/campaign export and merge-on-import vs replace
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
| Done (v1.2.49) | Windows file-association polish | Release zip + `install.ps1` registers HKCU `*.tmas-backup.zip` → local restore; bare EXE still published |
| Done (v1.2.48) | Proton Drive cloud backup | Official `proton-drive` CLI provider; Settings selector; `PROTON_DRIVE_CLI` / `PROTON_DRIVE_FOLDER` |
| Done (v1.2.47) | Modern desktop UI shell | Navigation rail + page headers; dense dark/light/Dracula/high-contrast themes with VoxHash teal accent |
| Done (v1.2.46) | Discussions-first community + beta testers | GitHub Discussions enabled; SUPPORT/README/CONTRIBUTING routing; beta discussion + issue template; Discord deferred |
| Done (v1.2.22) | Plugin marketplace / registry | Discover/install curated plugins via JSON catalog (remote + bundled offline); SHA-256 verify; Plugins → Browse Registry |
| Done (v1.2.21) | AI-assisted copy tools (optional keys) | Templates rewrite / spintax / variations via OpenAI-compatible Chat Completions; user-supplied `AI_API_KEY`; no SDK hard dependency |
| Done (v1.2.20 / v1.2.39–v1.2.44) | Stricter mypy (blocking) | Strict flags + CI fail for core/services/models; v1.2.39–v1.2.43 plugins + expanded GUI; v1.2.44 `app/utils` + `app/cli.py` |
| Done (v1.2.45) | Security posture | Threat model (proxies/shared machines); session/credential review + harden CLI; periodic `pip-audit` CI |
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
- [x] S3-compatible cloud backup (AWS / MinIO / R2 / Wasabi / B2) — v1.2.31
- [x] Dropbox cloud backup (access token + folder; stdlib HTTP) — v1.2.32
- [x] OneDrive cloud backup (Microsoft Graph access token + folder; stdlib HTTP) — v1.2.33
- [x] **Proton Drive cloud backup** (official `proton-drive` CLI + OS keyring session; Settings provider) — v1.2.48
  - Leftover: in-process SDK/REST provider if/when Proton ships third-party GA with documented auth (CLI path remains the supported integration)
  - Leftover: other niche non-S3 providers only if demand appears
- [x] Offline-friendly restore and conflict messaging
- [x] Stronger campaign analytics export (CSV/JSON)
- [x] AI-assisted copy tools only behind optional, user-supplied API keys (no hard dependency)
  - [x] Non-English locale strings for AI UI keys (all 13 languages) — v1.2.37
  - [x] Provider presets beyond generic OpenAI-compatible base URL (Azure path/api-version + Anthropic Messages API) — v1.2.38
- [x] Plugin marketplace / registry (curated catalog discover + verified install)
  - [x] Community seed submissions beyond the original two official plugins (Whitespace Normalize Filter + Failure Counter Analytics; analytics sample template; `plugin-catalog-entry` CLI) — v1.2.35
  - [x] Further third-party registry volume (Emoji Strip Filter + Success Counter Analytics; six downloadable plugins) — v1.2.36
  - Leftover: ongoing community PRs / external third-party authors beyond the curated seed set

### Proton Drive cloud backup — shipped path (v1.2.48)

**Status:** Done as a CLI-backed Settings provider (`ProtonDriveProvider`). No third-party REST/OAuth API exists; TMAS does **not** embed reverse-engineered clients or rclone.

| Option | Reality | TMAS choice |
| --- | --- | --- |
| Official public REST / OAuth API | Still absent for third-party apps | N/A |
| [Proton Drive SDK](https://github.com/ProtonDriveApps/sdk) | Preview; auth not third-party-ready | Deferred leftover for a future in-process provider |
| [Proton Drive CLI](https://proton.me/support/drive-cli) | Official; `proton-drive auth login` + `filesystem` upload/list/download | **Shipped** — subprocess wrapper; session in OS keyring |
| rclone / unofficial bridges | Fragile / unsupported by Proton | Not embedded |

**Setup:** install CLI → `proton-drive auth login` → optional `PROTON_DRIVE_CLI` / `PROTON_DRIVE_FOLDER` → Settings → Cloud Backup → **Proton Drive (CLI)** → Verify session.

**Leftover:** replace/augment with an in-process SDK provider only after Proton ships third-party GA + documented auth.

### Phase 3 (later): Platform expansion
- [x] Enhanced macOS/Linux packaging and file associations
- [x] Windows file-association installer polish (`packaging/windows/install.ps1` + release zip) — v1.2.49
  - Leftover: Apple code signing / notarization (requires Apple Developer ID; not shippable from CI secrets in this repo alone)
- [x] Optional lightweight web companion (read-only monitoring first)
  - [x] Auth token / reverse-proxy guidance for non-localhost (v1.2.25)
  - [x] Richer live charts (v1.2.26)
  - [x] Optional auto-start with GUI (v1.2.27)
- [ ] Mobile companion deferred until web companion proves demand

### Phase 4 (later): Team / enterprise
- [x] Multi-user roles belong primarily to SendGram (hosted) — documented; no desktop RBAC
- [x] Desktop remains single-operator with export/import for handoff (v1.2.28)
- [x] Selective entity export (templates/campaigns only) + merge-on-import vs replace (v1.2.29)
- [x] Broader developer SDK polish as registry submissions grow (v1.2.30)
- [x] Signed plugin catalogs (Ed25519; `plugin-catalog-sign`; optional require-signature) — v1.2.34
- [x] Richer community registry submissions (seed installables + catalog-entry tooling + submission issue template) — v1.2.35
- [x] Further third-party registry volume (Emoji Strip + Success Counter; six downloadable plugins) — v1.2.36
  - Leftover: ongoing community PRs / external third-party authors beyond the curated seed set

---

## Technical debt (tracked)

### Code quality
- [x] Broader pytest coverage beyond spintax/throttler (campaign filters, settings, CLI, import smoke; more integration coverage still welcome)
- [x] Coverage reporting in CI summary (Actions job summary + fail-under 20% baseline; Codecov upload remains optional)
- [x] Type hints on remaining high-value untyped modules (incremental)
- [x] Stricter mypy for `app/core`, `app/services`, `app/models` (blocking in CI)
- [x] Extend blocking mypy to `app/plugins` + practical GUI subset (`theme`, `about`, package inits) — v1.2.39
- [x] Expand blocking mypy GUI subset (`plugin_widget`, `testing_widget`, `telegram_selector`) — v1.2.40
- [x] Expand blocking mypy GUI subset (`main`, `cloud_backup_widget`, `dashboard_widget`) — v1.2.41
- [x] Expand blocking mypy GUI subset (`log_widget`, `template_widget`, `recipient_widget`) — v1.2.42
- [x] Expand blocking mypy GUI subset (`settings_widget`, `account_widget`, `campaign_widget`) — v1.2.43
- [x] Type `app/utils` / `app/cli.py` under the same blocking gate — v1.2.44
- [x] Resolve known `app.core` ↔ `app.services` import cycle for package-level imports

### Documentation
- [x] API, FAQ, troubleshooting, installation, getting-started
- [ ] Short video walkthrough (external; link from README when published)

### Security
- [x] Periodic dependency audit (`pip-audit` workflow + SECURITY.md process) — v1.2.45
- [x] Session/credential storage review (`security-check` / `security-harden`) — v1.2.45
- [x] Document threat model for proxies and shared machines — v1.2.45

---

## Community

- [x] GitHub Sponsors + issue/PR templates + CODE_OF_CONDUCT
- [x] Discussions-first community channel (Discussions enabled + linked in SUPPORT/README/CONTRIBUTING; Discord still open when a real invite exists) — v1.2.46
- [x] Beta tester list for cloud-backup MVP (Discussions #2 + `beta_tester` issue template) — v1.2.46

---

## Support

- GitHub Issues / Discussions
- Docs: `docs/index.md`
- Contact: contact@voxhash.dev
- Hosted product: https://www.sendgram.pro

---

**Made with ❤️ by VoxHash Technologies**
