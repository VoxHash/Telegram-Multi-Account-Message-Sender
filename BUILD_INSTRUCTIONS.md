# Build Instructions for PyInstaller

## Including telegram_selector Module

The `telegram_selector` module must be explicitly included when building with PyInstaller.

### Option 1: Use the Hook File (Recommended)

The project includes a PyInstaller hook file at `hooks/hook-app.gui.widgets.telegram_selector.py`.

When building with PyInstaller, use the `--additional-hooks-dir` flag:

```bash
pyinstaller --additional-hooks-dir=hooks main.py
```

### Option 2: Use Hidden Imports

Alternatively, you can use the `--hidden-import` flag:

```bash
pyinstaller --hidden-import=app.gui.widgets.telegram_selector main.py
```

### Option 3: Create a Spec File

Create a `main.spec` file with hidden imports:

```python
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['app.gui.widgets.telegram_selector'],
    hookspath=['hooks'],
    ...
)
```

Then build with:
```bash
pyinstaller main.spec
```

## Complete Build Command Example

```bash
pyinstaller \
    --name=telegram-multi-account-sender \
    --onefile \
    --windowed \
    --icon=assets/icons/favicon.ico \
    --additional-hooks-dir=hooks \
    --hidden-import=app.gui.widgets.telegram_selector \
    --add-data "app/translations;app/translations" \
    --add-data "assets;assets" \
    main.py
```

