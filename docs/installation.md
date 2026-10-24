# Installation

Install Telegram Multi-Account Message Sender on Windows, macOS, or Linux.

## Prerequisites

- Python 3.10+
- `pip`
- Internet access to install dependencies and reach Telegram
- Telegram API credentials (required for live account use; see [Configuration](configuration.md))

### Linux GUI dependencies

Headless or minimal Linux images need Qt/X11 libraries for PyQt5 (exact package names vary by distro). For CI-style smoke tests without a display, use `xvfb-run`.

## Option 1: pip (recommended)

Install from [PyPI](https://pypi.org/project/telegram-multi-account-sender/):

```bash
pip install telegram-multi-account-sender
```

Launch:

```bash
telegram-sender
# or
python -m app.cli
```

## Option 2: From source

```bash
git clone https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender.git
cd Telegram-Multi-Account-Message-Sender
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt   # optional: tests and tooling
python main.py
```

Editable install:

```bash
pip install -e .
```

## Option 3: Docker

```bash
docker build -t telegram-sender .
docker run -it --rm \
  -v "$(pwd)/app_data:/app/app_data" \
  -v "$(pwd)/.env:/app/.env" \
  telegram-sender
```

Published images (on release tags):

```text
ghcr.io/voxhash/telegram-multi-account-message-sender
```

## Option 4: Release installers

Download platform installers or executables from the [GitHub Releases](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/releases) page.

### Linux release tarball (desktop + MIME)

The Linux asset is a directory archive (`telegram-multi-account-sender-v*-linux.tar.gz`) that includes the binary, icons, FreeDesktop `.desktop` entry, `application/x-tmas-backup` MIME XML for `*.tmas-backup.zip`, and `install.sh`:

```bash
tar -xzf telegram-multi-account-sender-v*-linux.tar.gz
cd telegram-multi-account-sender-v*-linux
./install.sh
```

That installs into `~/.local` (no root). Uninstall with `./install.sh --uninstall`. After install, opening a `.tmas-backup.zip` from the file manager launches a local restore prompt.

### macOS DMG

The macOS asset is a `.dmg` built on GitHub Actions `macos-latest` runners. The `.app` ships `Info.plist` document types / UTI `dev.voxhash.tmas-backup` for `*.tmas-backup.zip`. **Code signing and notarization are not included** in this repo’s workflow — Gatekeeper may require right-click → Open on unsigned builds. Local ICNS generation uses `packaging/macos/build-icns.sh` (`iconutil`; macOS only).

## Frozen builds (PyInstaller)

The repository includes `main.spec` and hooks under `hooks/`. On Linux/Windows the spec produces a one-file binary; on macOS it builds an `.app` bundle with backup file associations.

Recommended:

```bash
pip install pyinstaller
pyinstaller main.spec
```

Linux release layout (after building the binary):

```bash
./packaging/linux/assemble-dist.sh dist/telegram-multi-account-sender ./tmms-linux v1.2.23
```

Alternative (hook directory):

```bash
pyinstaller --onefile --noconsole \
  --additional-hooks-dir=hooks \
  --hidden-import=app.gui.widgets.telegram_selector \
  main.py
```

For a Windows console build, set `console=True` in `main.spec`.

If `app.gui.widgets.telegram_selector` is missing from the bundle:

1. Prefer `pyinstaller main.spec`
2. Confirm `hooks/hook-app.gui.widgets.telegram_selector.py` exists
3. Delete `build/` and `dist/`, then rebuild

## Optional: Rust native accelerator

For lower memory use and faster parallel spintax / pacing on large campaigns, use the optional Rust sidecar.

### Prebuilt binary (Linux x86_64)

From the [GitHub Releases](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/releases) page, download `tmms_native-linux-x86_64`, then:

```bash
mkdir -p bin
install -m 755 tmms_native-linux-x86_64 bin/tmms_native
```

Or set `TMMS_NATIVE_BIN` to the downloaded file path. Other platforms: build from source (below). Release assets currently include Linux x86_64; macOS/Windows binaries may be added later.

### Build from source

Requires [Rust](https://rustup.rs/) / `cargo`:

```bash
./native/build.sh
# installs bin/tmms_native and prints a ping JSON response
```

The Python app auto-detects `bin/tmms_native` (or `TMMS_NATIVE_BIN`). If the binary is missing, it falls back to pure Python with the same behavior. Disable with `TMMS_NATIVE_ACCEL=0`. Details: [Architecture](architecture.md#native-accelerator-rust).

## Verify the install

```bash
python -m compileall -q app main.py
pytest tests/ -q --override-ini='addopts='
```

GUI smoke (with display or Xvfb):

```bash
xvfb-run -a python -c "from app.gui.main import MainWindow; print('ok')"
```

## Next steps

- [Getting Started](getting-started.md)
- [Quick Start](quick-start.md)
- [Configuration](configuration.md)
