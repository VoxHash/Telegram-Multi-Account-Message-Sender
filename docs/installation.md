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

## Frozen builds (PyInstaller)

The repository includes `main.spec` and hooks under `hooks/` for one-file builds.

Recommended:

```bash
pip install pyinstaller
pyinstaller main.spec
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
