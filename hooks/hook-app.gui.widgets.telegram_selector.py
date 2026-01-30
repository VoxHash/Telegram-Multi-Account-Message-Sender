"""
PyInstaller hook for app.gui.widgets.telegram_selector module.

This ensures the telegram_selector module is included in PyInstaller builds.
"""

from PyInstaller.utils.hooks import collect_all, collect_submodules

# Collect all dependencies for the telegram_selector module
datas, binaries, hiddenimports = collect_all('app.gui.widgets.telegram_selector')

# Explicitly add the module to hidden imports
hiddenimports += [
    'app.gui.widgets.telegram_selector',
    'app.gui.widgets.telegram_selector.TelegramSelectorDialog',
    'telegram_selector',  # Also try without full path
]

# Collect any submodules
hiddenimports += collect_submodules('app.gui.widgets.telegram_selector')


