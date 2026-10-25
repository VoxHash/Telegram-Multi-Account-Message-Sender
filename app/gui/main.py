"""
Main window for the Telegram Multi-Account Message Sender.
"""

from pathlib import Path
from typing import List, Optional, Tuple

from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QStatusBar,
    QFrame,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QSizePolicy,
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QCloseEvent, QFont

from ..services import get_settings, get_logger
from ..services.translation import get_translation_manager, _
from .theme import ThemeManager

# Explicitly import telegram_selector to ensure PyInstaller includes it
from .widgets import (
    AccountWidget,
    CampaignWidget,
    LogWidget,
    RecipientWidget,
    SettingsWidget,
    DashboardWidget,
    PluginWidget,
)
from .widgets.about_widget import AboutWidget


class MainWindow(QMainWindow):
    """Main application window with media-style navigation rail."""

    def __init__(self, pending_backup_path: Optional[Path] = None):
        """Initialize main window."""
        super().__init__()

        self.settings = get_settings()
        self.logger = get_logger()
        self.theme_manager = ThemeManager()
        self.translation_manager = get_translation_manager()
        self._pending_backup_path = pending_backup_path

        # Nav key -> (title translation key, English subtitle for page header)
        self._nav_entries: List[Tuple[str, str, Optional[str]]] = [
            ("dashboard", "tabs.dashboard", "Campaign overview and account health"),
            ("accounts", "tabs.accounts", "Connect and manage Telegram sessions"),
            ("campaigns", "tabs.campaigns", "Schedule and control outbound campaigns"),
            ("templates", "tabs.templates", "Spintax templates and message variants"),
            ("recipients", "tabs.recipients", "Organize recipient lists and segments"),
            ("testing", "tabs.testing", "Preview and validate messages before send"),
            ("logs", "tabs.logs", "Delivery history and activity trail"),
            ("plugins", "tabs.plugins", "Extensions and registry installs"),
            ("settings", "tabs.settings", "Theme, language, safety, and cloud backup"),
            ("about", "tabs.about", "Version, license, and product info"),
        ]

        # Connect language change signal
        self.translation_manager.language_changed.connect(self.on_language_changed)

        self.setup_ui()
        self.setup_menu()
        self.setup_status_bar()

        # Setup timer for periodic updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(30000)  # Update every 30 seconds

        # Initial status update
        self.update_status()

        if self._pending_backup_path is not None:
            QTimer.singleShot(0, self._handle_pending_backup)

        # Optional web companion auto-start (background; no forced browser open)
        QTimer.singleShot(0, self._maybe_autostart_web_companion)

        self.logger.info("Main window initialized")

    def setup_ui(self) -> None:
        """Set up the user interface with sidebar navigation."""
        self.setWindowTitle(_("app.title"))
        self.setGeometry(100, 100, self.settings.window_width, self.settings.window_height)
        self.setMinimumSize(960, 640)

        # Central shell: nav rail | content
        central_widget = QWidget()
        central_widget.setObjectName("centralShell")
        self.setCentralWidget(central_widget)

        shell_layout = QHBoxLayout(central_widget)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)

        # ——— Navigation rail ———
        self.nav_rail = QFrame()
        self.nav_rail.setObjectName("navRail")
        self.nav_rail.setFixedWidth(220)
        nav_layout = QVBoxLayout(self.nav_rail)
        nav_layout.setContentsMargins(12, 16, 12, 16)
        nav_layout.setSpacing(4)

        self.brand_label = QLabel("TMMS")
        self.brand_label.setObjectName("navBrand")
        brand_font = QFont()
        brand_font.setPointSize(14)
        brand_font.setBold(True)
        self.brand_label.setFont(brand_font)
        nav_layout.addWidget(self.brand_label)

        self.brand_sub_label = QLabel("VoxHash · SendGram")
        self.brand_sub_label.setObjectName("navBrandSub")
        nav_layout.addWidget(self.brand_sub_label)

        self.nav_list = QListWidget()
        self.nav_list.setObjectName("navList")
        self.nav_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.nav_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.nav_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.nav_list.setSpacing(1)
        self.nav_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        nav_layout.addWidget(self.nav_list, 1)

        shell_layout.addWidget(self.nav_rail)

        # ——— Content area ———
        self.content_shell = QFrame()
        self.content_shell.setObjectName("contentShell")
        content_layout = QVBoxLayout(self.content_shell)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.content_header = QFrame()
        self.content_header.setObjectName("contentHeader")
        header_layout = QVBoxLayout(self.content_header)
        header_layout.setContentsMargins(24, 16, 24, 12)
        header_layout.setSpacing(2)

        self.page_title = QLabel("")
        self.page_title.setObjectName("pageTitle")
        header_layout.addWidget(self.page_title)

        self.page_subtitle = QLabel("")
        self.page_subtitle.setObjectName("pageSubtitle")
        header_layout.addWidget(self.page_subtitle)

        content_layout.addWidget(self.content_header)

        self.page_stack = QStackedWidget()
        self.page_stack.setObjectName("pageStack")
        content_layout.addWidget(self.page_stack, 1)

        shell_layout.addWidget(self.content_shell, 1)

        # Build pages + nav items (order matches _nav_entries)
        self.create_dashboard_tab()
        self.create_accounts_tab()
        self.create_campaigns_tab()
        self.create_templates_tab()
        self.create_recipients_tab()
        self.create_testing_tab()
        self.create_logs_tab()
        self.create_plugins_tab()
        self.create_settings_tab()
        self.create_about_tab()

        self._populate_nav()
        self.nav_list.currentRowChanged.connect(self._on_nav_changed)
        self.nav_list.setCurrentRow(0)
        self._on_nav_changed(0)

        # Compatibility alias: some helpers historically used tab_widget
        self.tab_widget = self.page_stack

    def _populate_nav(self) -> None:
        """Fill the navigation list from translation keys."""
        self.nav_list.blockSignals(True)
        self.nav_list.clear()
        for _key, title_key, _sub_key in self._nav_entries:
            item = QListWidgetItem(_(title_key))
            self.nav_list.addItem(item)
        self.nav_list.blockSignals(False)

    def _on_nav_changed(self, index: int) -> None:
        """Switch stacked page and update header when nav selection changes."""
        if index < 0 or index >= len(self._nav_entries):
            return
        self.page_stack.setCurrentIndex(index)
        _key, title_key, subtitle = self._nav_entries[index]
        self.page_title.setText(_(title_key))
        if subtitle:
            self.page_subtitle.setText(subtitle)
            self.page_subtitle.setVisible(True)
        else:
            self.page_subtitle.clear()
            self.page_subtitle.setVisible(False)

    def _add_page(self, widget: QWidget) -> None:
        """Add a page to the stacked content area."""
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(20, 16, 20, 16)
        page_layout.setSpacing(0)
        page_layout.addWidget(widget)
        self.page_stack.addWidget(page)

    def create_dashboard_tab(self) -> None:
        """Create dashboard page."""
        self.dashboard_widget = DashboardWidget()
        self._add_page(self.dashboard_widget)

    def create_accounts_tab(self) -> None:
        """Create accounts management page."""
        self.accounts_widget = AccountWidget()
        self._add_page(self.accounts_widget)

    def create_campaigns_tab(self) -> None:
        """Create campaigns management page."""
        self.campaigns_widget = CampaignWidget()
        self._add_page(self.campaigns_widget)

    def create_templates_tab(self) -> None:
        """Create templates management page."""
        from .widgets.template_widget import TemplateWidget

        self.templates_widget = TemplateWidget()
        self._add_page(self.templates_widget)

    def create_recipients_tab(self) -> None:
        """Create recipients management page."""
        self.recipients_widget = RecipientWidget()
        self._add_page(self.recipients_widget)

    def create_testing_tab(self) -> None:
        """Create testing page."""
        from .widgets.testing_widget import TestingWidget

        self.testing_widget = TestingWidget()
        self._add_page(self.testing_widget)

    def create_logs_tab(self) -> None:
        """Create logs viewer page."""
        self.logs_widget = LogWidget()
        self._add_page(self.logs_widget)

    def create_plugins_tab(self) -> None:
        """Create plugins management page."""
        self.plugins_widget = PluginWidget()
        self._add_page(self.plugins_widget)

    def create_settings_tab(self) -> None:
        """Create settings page."""
        self.settings_widget = SettingsWidget()
        # Connect settings update signal to update status bar
        self.settings_widget.settings_updated.connect(self.on_settings_updated)
        self._add_page(self.settings_widget)

    def create_about_tab(self) -> None:
        """Create about page."""
        self.about_widget = AboutWidget()
        self._add_page(self.about_widget)

    def _handle_pending_backup(self) -> None:
        """Open Settings → Cloud Backup for an OS file-association launch."""
        path = self._pending_backup_path
        self._pending_backup_path = None
        if path is None:
            return
        settings_index = self._nav_key_index("settings")
        if settings_index >= 0:
            self.nav_list.setCurrentRow(settings_index)
        cloud_index = self.settings_widget.tab_widget.indexOf(
            self.settings_widget.cloud_backup_widget
        )
        if cloud_index >= 0:
            self.settings_widget.tab_widget.setCurrentIndex(cloud_index)
        self.settings_widget.cloud_backup_widget.offer_associated_backup(path)

    def _nav_key_index(self, key: str) -> int:
        """Return nav index for a page key, or -1."""
        for i, (nav_key, _title, _sub) in enumerate(self._nav_entries):
            if nav_key == key:
                return i
        return -1

    def setup_menu(self) -> None:
        """Set up menu bar."""
        # Menu bar removed as requested

    def setup_status_bar(self) -> None:
        """Set up status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Status label
        self.status_label = QLabel(_("app.ready"))
        self.status_label.setStyleSheet("background-color: transparent;")
        self.status_bar.addWidget(self.status_label)

        # Language label
        current_language = self.translation_manager.get_language_display_name(
            self.translation_manager.current_language
        )
        self.language_label = QLabel(f"{_('app.language')}: {current_language}")
        self.language_label.setStyleSheet("background-color: transparent;")
        self.status_bar.addPermanentWidget(self.language_label)

        # Theme label
        initial_theme = self.theme_manager.get_current_theme()
        formatted_theme = self.format_theme_name(initial_theme)
        self.theme_label = QLabel(f"{_('app.theme')}: {formatted_theme}")
        self.theme_label.setStyleSheet("background-color: transparent;")
        self.status_bar.addPermanentWidget(self.theme_label)

    def toggle_theme(self) -> None:
        """Toggle between light and dark theme."""
        current = self.theme_manager.get_current_theme()
        if current == "light":
            self.set_theme("dark")
        else:
            self.set_theme("light")

    def set_theme(self, theme: str) -> None:
        """Set application theme."""
        self.theme_manager.apply_theme(theme)
        actual_theme = self.theme_manager.get_current_theme()
        formatted_theme = self.format_theme_name(actual_theme)
        self.theme_label.setText(f"{_('app.theme')}: {formatted_theme}")

    def on_settings_updated(self) -> None:
        """Handle settings update."""
        # Reload settings to get updated values
        from ..services import reload_settings

        reload_settings()
        self.settings = get_settings()

        # Update theme manager with new settings
        self.theme_manager.settings = self.settings

        # Convert enum to string value for theme application
        theme_value = (
            self.settings.theme.value
            if hasattr(self.settings.theme, "value")
            else str(self.settings.theme)
        )

        # Apply the current theme from settings
        self.theme_manager.apply_theme(theme_value)

        # Force refresh the status bar theme display
        self.refresh_status_bar_theme()

        self.logger.info(
            f"Settings updated, theme changed to: {self.theme_manager.get_current_theme()}"
        )

    def refresh_status_bar_theme(self) -> None:
        """Refresh the theme display in the status bar."""
        actual_theme = self.theme_manager.get_current_theme()
        formatted_theme = self.format_theme_name(actual_theme)
        self.theme_label.setText(f"{_('app.theme')}: {formatted_theme}")
        self.logger.debug(f"Status bar theme updated to: {formatted_theme}")

    def format_theme_name(self, theme: str) -> str:
        """Format theme name for display."""
        theme_formats = {
            "light": _("settings.light"),
            "dark": _("settings.dark"),
            "dracula": _("settings.dracula"),
            "auto": _("settings.auto"),
        }
        return theme_formats.get(theme, theme.title())

    def update_status(self) -> None:
        """Update status bar with current application status."""
        try:
            # Get current status information
            status_info = self.get_application_status()
            self.status_label.setText(status_info)
        except Exception as e:
            self.logger.error(f"Error updating status: {e}")
            self.status_label.setText(_("common.error"))

    def get_application_status(self) -> str:
        """Get current application status information."""
        try:
            from ..services import get_session
            from ..models import Account, Campaign, Recipient

            session = get_session()
            try:
                # Count accounts
                from sqlmodel import select, func

                account_count = (
                    session.exec(
                        select(func.count())
                        .select_from(Account)
                        .where(Account.is_deleted.is_(False))  # type: ignore[attr-defined]
                    ).first()
                    or 0
                )

                # Count campaigns
                campaign_count = (
                    session.exec(
                        select(func.count())
                        .select_from(Campaign)
                        .where(Campaign.is_deleted.is_(False))  # type: ignore[attr-defined]
                    ).first()
                    or 0
                )

                # Count recipients
                recipient_count = (
                    session.exec(
                        select(func.count())
                        .select_from(Recipient)
                        .where(Recipient.is_deleted.is_(False))  # type: ignore[attr-defined]
                    ).first()
                    or 0
                )

                # Get online accounts (only if we have accounts)
                online_accounts = 0
                if account_count > 0:
                    online_accounts = (
                        session.exec(
                            select(func.count())
                            .select_from(Account)
                            .where(Account.is_deleted.is_(False))  # type: ignore[attr-defined]
                            .where(Account.status == "ONLINE")
                        ).first()
                        or 0
                    )

                # Build status message
                status_parts = []
                if account_count > 0:
                    status_parts.append(_("app.accounts_count").format(count=account_count))
                    if online_accounts > 0:
                        status_parts.append(_("app.online_count").format(online=online_accounts))

                if campaign_count > 0:
                    status_parts.append(_("app.campaigns_count").format(count=campaign_count))

                if recipient_count > 0:
                    status_parts.append(_("app.recipients_count").format(count=recipient_count))

                if status_parts:
                    return " | ".join(status_parts)
                else:
                    return _("app.ready")

            finally:
                session.close()

        except Exception as e:
            self.logger.error(f"Error getting application status: {e}")
            return _("app.ready")

    def on_language_changed(self, language: str) -> None:
        """Handle language change."""
        self.logger.info(f"Language changed to: {language}")
        # Update UI text
        self.setWindowTitle(_("app.title"))
        self.status_label.setText(_("app.ready"))

        # Refresh nav labels and current page header
        current = self.nav_list.currentRow()
        self._populate_nav()
        if current >= 0:
            self.nav_list.setCurrentRow(current)
            self._on_nav_changed(current)

        # Update language label
        current_language = self.translation_manager.get_language_display_name(language)
        self.language_label.setText(f"{_('app.language')}: {current_language}")

        # Update theme label
        current_theme = self.theme_manager.get_current_theme()
        formatted_theme = self.format_theme_name(current_theme)
        self.theme_label.setText(f"{_('app.theme')}: {formatted_theme}")

        # Update status bar
        self.update_status()

        # Force refresh all widgets
        self.refresh_all_widgets()

    def refresh_all_widgets(self) -> None:
        """Refresh all widgets to apply language changes."""
        try:
            # Refresh each widget if it has a refresh method
            if hasattr(self, "accounts_widget") and hasattr(
                self.accounts_widget, "refresh_accounts"
            ):
                self.accounts_widget.refresh_accounts()
            if hasattr(self, "campaigns_widget") and hasattr(
                self.campaigns_widget, "refresh_campaigns"
            ):
                self.campaigns_widget.refresh_campaigns()
            if hasattr(self, "templates_widget") and hasattr(
                self.templates_widget, "refresh_templates"
            ):
                self.templates_widget.refresh_templates()
            if hasattr(self, "recipients_widget") and hasattr(
                self.recipients_widget, "refresh_recipients"
            ):
                self.recipients_widget.refresh_recipients()
            if hasattr(self, "logs_widget") and hasattr(self.logs_widget, "refresh_logs"):
                self.logs_widget.refresh_logs()
            if hasattr(self, "settings_widget") and hasattr(self.settings_widget, "load_settings"):
                self.settings_widget.load_settings()
            if hasattr(self, "about_widget") and hasattr(self.about_widget, "refresh_content"):
                self.about_widget.refresh_content()
        except Exception as e:
            self.logger.error(f"Error refreshing widgets: {e}")

    def _maybe_autostart_web_companion(self) -> None:
        """Start the read-only web companion in the background when Settings/env request it."""
        try:
            from ..services.web_companion import maybe_autostart_companion_from_settings

            server = maybe_autostart_companion_from_settings(self.settings)
            if server is not None and hasattr(self, "settings_widget"):
                refresh = getattr(self.settings_widget, "refresh_web_companion_status", None)
                if callable(refresh):
                    refresh()
        except Exception as e:
            self.logger.error(f"Web companion auto-start error: {e}")

    def closeEvent(self, event: Optional[QCloseEvent]) -> None:
        """Handle window close event."""
        self.logger.info("Application closing")
        try:
            from ..services.web_companion import stop_companion

            # Only stop if this GUI process started the companion (auto-start or Settings open).
            stop_companion(only_if_gui_owned=True)
        except Exception as e:
            self.logger.error(f"Error stopping web companion on exit: {e}")
        if event is not None:
            event.accept()
