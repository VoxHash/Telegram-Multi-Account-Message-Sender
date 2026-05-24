"""
Runtime hook to ensure telegram_selector module is available.
This is executed before the main script runs.
"""

import sys
import os

# Add the app directory to path if not already there
if hasattr(sys, '_MEIPASS'):
    # We're running from a PyInstaller bundle
    app_path = os.path.join(sys._MEIPASS, 'app')
    if app_path not in sys.path:
        sys.path.insert(0, app_path)

    translations_path = os.path.join(sys._MEIPASS, 'app', 'translations')
    if not os.path.isdir(translations_path):
        raise RuntimeError(
            f"Translation files missing from application bundle: {translations_path}"
        )
    
    # Try to import the module explicitly
    try:
        import app.gui.widgets.telegram_selector
    except ImportError:
        # If import fails, try to add the widgets directory
        widgets_path = os.path.join(sys._MEIPASS, 'app', 'gui', 'widgets')
        if widgets_path not in sys.path:
            sys.path.insert(0, widgets_path)
        try:
            import telegram_selector
            # Make it available as app.gui.widgets.telegram_selector
            import app.gui.widgets as widgets_module
            widgets_module.telegram_selector = telegram_selector
        except ImportError:
            pass  # Will fail at runtime if really needed

