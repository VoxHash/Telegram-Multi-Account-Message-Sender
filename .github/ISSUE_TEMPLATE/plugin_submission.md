---
name: Plugin registry submission
about: Propose a community plugin for the curated marketplace catalog
title: "[plugin] "
labels: enhancement
assignees: ""
---

## Plugin summary

- **Proposed catalog id** (e.g. `community.my-filter`):
- **Plugin type** (`filter` / `analytics` / other):
- **License**:
- **Min app version**:

## What it does

Brief description of behavior and default config.

## Submission checklist

- [ ] Started from `registry/templates/sample_filter_plugin.py` or `sample_analytics_plugin.py`
- [ ] Absolute imports only (`from app.core.plugin import …`)
- [ ] Installable `.py` lives under `registry/plugins/` (or linked in the PR)
- [ ] Generated catalog entry with `telegram-sender plugin-catalog-entry path/to/plugin.py`
- [ ] Validated with `telegram-sender plugin-validate path/to/plugin.py`
- [ ] Validated catalog SHA-256 with `telegram-sender plugin-validate registry/catalog.json --plugins-dir registry/plugins`
- [ ] Install never auto-enables the plugin

## Links

- PR (preferred) or gist / raw HTTPS URL:
- Homepage / repository:

Maintainers will review, merge the catalog entry, and re-sign the official catalog (Ed25519). Do not commit private keys.
