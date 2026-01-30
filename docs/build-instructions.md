# Build Instructions for PyInstaller

## Including telegram_selector Module

The `telegram_selector` module must be explicitly included when building with PyInstaller.

### Option 1: Use the Spec File (Recommended)

The project includes a `main.spec` file that explicitly includes all necessary modules.

Build with:
```bash
pyinstaller main.spec
```

For Windows (console version), edit `main.spec` and change `console=False` to `console=True`.

### Option 2: Use the Hook File

The project includes a PyInstaller hook file at `hooks/hook-app.gui.widgets.telegram_selector.py`.

When building with PyInstaller, use the `--additional-hooks-dir` flag:

```bash
pyinstaller --onefile --noconsole --additional-hooks-dir=hooks --hidden-import=app.gui.widgets.telegram_selector main.py
```

### Option 3: Use Hidden Imports Only

```bash
pyinstaller --onefile --noconsole --hidden-import=app.gui.widgets.telegram_selector main.py
```

## Complete Build Command Example (Windows)

```bash
pyinstaller \
    --name=telegram-multi-account-sender \
    --onefile \
    --noconsole \
    --icon=assets/icons/favicon.ico \
    --additional-hooks-dir=hooks \
    --hidden-import=app.gui.widgets.telegram_selector \
    --hidden-import=PyQt5 \
    --hidden-import=PyQt5.QtCore \
    --hidden-import=PyQt5.QtGui \
    --hidden-import=PyQt5.QtWidgets \
    --add-data "app/translations;app/translations" \
    --add-data "assets;assets" \
    main.py
```

## Troubleshooting

If you still get the "No module named 'app.gui.widgets.telegram_selector'" error:

1. **Use the spec file**: `pyinstaller main.spec` (most reliable)
2. **Check the hooks directory**: Ensure `hooks/hook-app.gui.widgets.telegram_selector.py` exists
3. **Verify the file exists**: Check that `app/gui/widgets/telegram_selector.py` exists
4. **Clean build**: Delete `build/` and `dist/` directories, then rebuild
5. **Check PyInstaller version**: Ensure you're using a recent version of PyInstaller
