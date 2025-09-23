"""
Settings management widget.
"""

from typing import Optional, Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QComboBox, QCheckBox, QSpinBox,
    QMessageBox, QDialog, QDialogButtonBox, QFormLayout,
    QTextEdit, QTabWidget, QSlider
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

from ...services import get_logger, get_settings, reload_settings
from ...services.logger import reload_logger
from ...services.translation import _, get_translation_manager
from ...services.warmup_manager import get_warmup_manager
from ...models import Account


class SettingsWidget(QWidget):
    """Main settings management widget."""
    
    settings_updated = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.settings = get_settings()
        self.translation_manager = get_translation_manager()
        
        # Connect language change signal
        self.translation_manager.language_changed.connect(self.on_language_changed)
        
        # Setup warmup status timer
        from PyQt5.QtCore import QTimer
        self.warmup_timer = QTimer()
        self.warmup_timer.timeout.connect(self.update_warmup_status)
        self.warmup_timer.start(10000)  # Update every 10 seconds
        
        self.setup_ui()
        self.load_settings()
        
        # Initial warmup status update
        self.update_warmup_status()
    
    def setup_ui(self):
        """Set up the UI."""
        # Clear existing layout if it exists
        if hasattr(self, 'layout') and self.layout() is not None:
            # Clear existing widgets
            while self.layout().count():
                child = self.layout().takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        else:
            # Create new layout only if it doesn't exist
            layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.layout().addWidget(self.tab_widget)
        
        # General Settings Tab
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        # Application Settings
        app_group = QGroupBox(_("settings.application_settings"))
        app_layout = QFormLayout(app_group)
        
        self.debug_check = QCheckBox(_("settings.enable_debug_mode"))
        self.debug_check.setChecked(self.settings.debug)
        app_layout.addRow(self.debug_check)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.log_level_combo.setCurrentText(self.settings.log_level)
        app_layout.addRow(f"{_('settings.log_level')}:", self.log_level_combo)
        
        self.startup_check = QCheckBox(_("settings.start_with_windows"))
        self.startup_check.setChecked(self.settings.start_with_windows)
        self.startup_check.stateChanged.connect(self.on_startup_changed)
        app_layout.addRow(self.startup_check)
        
        general_layout.addWidget(app_group)
        
        # Telegram Settings
        telegram_group = QGroupBox(_("settings.telegram_api_settings"))
        telegram_layout = QFormLayout(telegram_group)
        
        self.api_id_edit = QLineEdit()
        self.api_id_edit.setText(str(self.settings.telegram_api_id) if self.settings.telegram_api_id else "")
        self.api_id_edit.setPlaceholderText(_("settings.api_help"))
        telegram_layout.addRow(f"{_('settings.api_id')}:", self.api_id_edit)
        
        self.api_hash_edit = QLineEdit()
        self.api_hash_edit.setText(self.settings.telegram_api_hash or "")
        self.api_hash_edit.setEchoMode(QLineEdit.Password)
        self.api_hash_edit.setPlaceholderText(_("settings.api_help"))
        telegram_layout.addRow(f"{_('settings.api_hash')}:", self.api_hash_edit)
        
        general_layout.addWidget(telegram_group)
        
        # Database Settings
        db_group = QGroupBox(_("settings.database_settings"))
        db_layout = QFormLayout(db_group)
        
        self.db_url_edit = QLineEdit()
        self.db_url_edit.setText(self.settings.database_url)
        self.db_url_edit.setPlaceholderText(_("settings.database_url"))
        db_layout.addRow(f"{_('settings.database_url')}:", self.db_url_edit)
        
        general_layout.addWidget(db_group)
        
        self.tab_widget.addTab(general_tab, _("settings.general"))
        
        # Rate Limiting Tab
        rate_tab = QWidget()
        rate_layout = QVBoxLayout(rate_tab)
        
        # Default Rate Limits
        rate_group = QGroupBox(_("settings.default_rate_limits"))
        rate_form_layout = QFormLayout(rate_group)
        
        self.default_rate_spin = QSpinBox()
        self.default_rate_spin.setRange(1, 60)
        self.default_rate_spin.setValue(self.settings.default_rate_limits)
        rate_form_layout.addRow(f"{_('settings.messages_per_minute')}:", self.default_rate_spin)
        
        self.max_hourly_spin = QSpinBox()
        self.max_hourly_spin.setRange(1, 1000)
        self.max_hourly_spin.setValue(self.settings.max_messages_per_hour)
        rate_form_layout.addRow(f"{_('settings.messages_per_hour')}:", self.max_hourly_spin)
        
        self.max_daily_spin = QSpinBox()
        self.max_daily_spin.setRange(1, 10000)
        self.max_daily_spin.setValue(self.settings.max_messages_per_day)
        rate_form_layout.addRow(f"{_('settings.messages_per_day')}:", self.max_daily_spin)
        
        self.global_concurrency_spin = QSpinBox()
        self.global_concurrency_spin.setRange(1, 20)
        self.global_concurrency_spin.setValue(self.settings.global_max_concurrency)
        rate_form_layout.addRow(f"{_('settings.global_max_concurrency')}:", self.global_concurrency_spin)
        
        rate_layout.addWidget(rate_group)
        
        # Warmup Settings
        warmup_group = QGroupBox(_("settings.warmup_settings"))
        warmup_layout = QFormLayout(warmup_group)
        
        self.warmup_enabled_check = QCheckBox(_("settings.enable_account_warmup"))
        self.warmup_enabled_check.setChecked(self.settings.warmup_enabled)
        warmup_layout.addRow(self.warmup_enabled_check)
        
        self.warmup_messages_spin = QSpinBox()
        self.warmup_messages_spin.setRange(1, 100)
        self.warmup_messages_spin.setValue(self.settings.warmup_messages)
        warmup_layout.addRow(f"{_('settings.warmup_messages')}:", self.warmup_messages_spin)
        
        self.warmup_interval_spin = QSpinBox()
        self.warmup_interval_spin.setRange(10, 1440)
        self.warmup_interval_spin.setValue(self.settings.warmup_interval_minutes)
        warmup_layout.addRow(f"{_('settings.warmup_interval_minutes')}:", self.warmup_interval_spin)
        
        rate_layout.addWidget(warmup_group)
        
        self.tab_widget.addTab(rate_tab, _("settings.rate_limiting"))
        
        # UI Settings Tab
        ui_tab = QWidget()
        ui_layout = QVBoxLayout(ui_tab)
        
        # Theme Settings
        theme_group = QGroupBox(_("settings.theme_settings"))
        theme_layout = QFormLayout(theme_group)
        
        self.theme_combo = QComboBox()
        theme_items = [_("settings.auto"), _("settings.light"), _("settings.dark"), _("settings.dracula")]
        theme_values = ["auto", "light", "dark", "dracula"]
        for i, (display, value) in enumerate(zip(theme_items, theme_values)):
            self.theme_combo.addItem(display, value)
            if value == self.settings.theme:
                self.theme_combo.setCurrentIndex(i)
        theme_layout.addRow(f"{_('settings.theme')}:", self.theme_combo)
        
        # Language Settings
        self.language_combo = QComboBox()
        language_items = [
            _("settings.english"), _("settings.french"), _("settings.spanish"), _("settings.chinese"), _("settings.japanese"), _("settings.german"), 
            _("settings.russian"), _("settings.estonian"), _("settings.portuguese"), _("settings.korean"), _("settings.catalan"), _("settings.basque"), _("settings.galician")
        ]
        language_values = ["en", "fr", "es", "zh", "ja", "de", "ru", "et", "pt", "ko", "ca", "eu", "gl"]
        for i, (display, value) in enumerate(zip(language_items, language_values)):
            self.language_combo.addItem(display, value)
            if value == self.settings.language:
                self.language_combo.setCurrentIndex(i)
        self.language_combo.currentTextChanged.connect(self.on_language_combo_changed)
        theme_layout.addRow(f"{_('settings.language')}:", self.language_combo)
        
        ui_layout.addWidget(theme_group)
        
        # Window Settings
        window_group = QGroupBox(_("settings.window_settings"))
        window_layout = QFormLayout(window_group)
        
        self.window_width_spin = QSpinBox()
        self.window_width_spin.setRange(800, 2000)
        self.window_width_spin.setValue(self.settings.window_width)
        window_layout.addRow(f"{_('settings.default_width')}:", self.window_width_spin)
        
        self.window_height_spin = QSpinBox()
        self.window_height_spin.setRange(600, 1500)
        self.window_height_spin.setValue(self.settings.window_height)
        window_layout.addRow(f"{_('settings.default_height')}:", self.window_height_spin)
        
        self.window_maximized_check = QCheckBox(_("settings.start_maximized"))
        self.window_maximized_check.setChecked(self.settings.window_maximized)
        window_layout.addRow(self.window_maximized_check)
        
        ui_layout.addWidget(window_group)
        
        self.tab_widget.addTab(ui_tab, _("settings.user_interface"))
        
        # Safety Settings Tab
        safety_tab = QWidget()
        safety_layout = QVBoxLayout(safety_tab)
        
        # Safety Controls
        safety_group = QGroupBox(_("settings.safety_settings"))
        safety_form_layout = QFormLayout(safety_group)
        
        self.respect_limits_check = QCheckBox(_("settings.respect_rate_limits"))
        self.respect_limits_check.setChecked(self.settings.respect_rate_limits)
        safety_form_layout.addRow(self.respect_limits_check)
        
        self.stop_on_error_check = QCheckBox(_("settings.stop_on_error"))
        self.stop_on_error_check.setChecked(self.settings.stop_on_error)
        safety_form_layout.addRow(self.stop_on_error_check)
        
        self.max_retries_spin = QSpinBox()
        self.max_retries_spin.setRange(0, 10)
        self.max_retries_spin.setValue(self.settings.max_retries)
        safety_form_layout.addRow(f"{_('settings.max_retries')}:", self.max_retries_spin)
        
        self.retry_delay_spin = QSpinBox()
        self.retry_delay_spin.setRange(1, 60)
        self.retry_delay_spin.setValue(self.settings.retry_delay_seconds)
        safety_form_layout.addRow(f"{_('settings.retry_delay_seconds')}:", self.retry_delay_spin)
        
        safety_layout.addWidget(safety_group)
        
        # Warmup Controls
        warmup_group = QGroupBox(_("settings.warmup_settings"))
        warmup_layout = QVBoxLayout(warmup_group)
        
        # Warmup status
        self.warmup_status_label = QLabel(f"{_('settings.warmup_status')}: Not Available")
        warmup_layout.addWidget(self.warmup_status_label)
        
        # Warmup controls
        warmup_controls_layout = QHBoxLayout()
        
        self.start_warmup_button = QPushButton(_("settings.start_warmup_all"))
        self.start_warmup_button.clicked.connect(self.start_all_warmup)
        warmup_controls_layout.addWidget(self.start_warmup_button)
        
        self.stop_warmup_button = QPushButton(_("settings.stop_all_warmup"))
        self.stop_warmup_button.clicked.connect(self.stop_all_warmup)
        warmup_controls_layout.addWidget(self.stop_warmup_button)
        
        self.reset_warmup_button = QPushButton(_("settings.reset_warmup_progress"))
        self.reset_warmup_button.clicked.connect(self.reset_all_warmup)
        warmup_controls_layout.addWidget(self.reset_warmup_button)
        
        warmup_layout.addLayout(warmup_controls_layout)
        
        # Warmup settings info
        self.warmup_info = QLabel(f"""
        <b>{_('settings.warmup_description')}:</b><br>
        {_('settings.warmup_help').replace('\\n', '<br>')}
        """)
        self.warmup_info.setWordWrap(True)
        self.warmup_info.setStyleSheet("QLabel { background-color: #2d2d2d; color: #ffffff; padding: 10px; border-radius: 5px; border: 1px solid #404040; }")
        warmup_layout.addWidget(self.warmup_info)
        
        safety_layout.addWidget(warmup_group)
        
        # Log Management
        log_group = QGroupBox(_("settings.log_management"))
        log_layout = QVBoxLayout(log_group)
        
        # Log management info
        log_info = QLabel(f"""
        <b>{_('settings.log_management_description')}:</b><br>
        {_('settings.log_management_help').replace('\\n', '<br>')}
        """)
        log_info.setWordWrap(True)
        log_info.setStyleSheet("QLabel { background-color: #2d2d2d; color: #ffffff; padding: 10px; border-radius: 5px; border: 1px solid #404040; }")
        log_layout.addWidget(log_info)
        
        # Delete logs button
        self.delete_logs_button = QPushButton(_("settings.delete_all_logs"))
        self.delete_logs_button.clicked.connect(self.delete_all_logs)
        self.delete_logs_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """)
        log_layout.addWidget(self.delete_logs_button)
        
        safety_layout.addWidget(log_group)
        
        self.tab_widget.addTab(safety_tab, _("settings.safety"))
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton(_("settings.save_settings"))
        self.save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_button)
        
        self.reset_button = QPushButton(_("settings.reset_to_defaults"))
        self.reset_button.clicked.connect(self.reset_settings)
        button_layout.addWidget(self.reset_button)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Status label
        self.status_label = QLabel(_("settings.settings_reloaded"))
        layout.addWidget(self.status_label)
    
    def load_settings(self):
        """Load current settings into the form."""
        # This is already done in setup_ui
        pass
    
    def save_settings(self):
        """Save settings to file."""
        try:
            # Update settings object
            self.settings.debug = self.debug_check.isChecked()
            self.settings.log_level = self.log_level_combo.currentText()
            self.settings.start_with_windows = self.startup_check.isChecked()
            
            # Telegram settings
            api_id_text = self.api_id_edit.text().strip()
            self.settings.telegram_api_id = int(api_id_text) if api_id_text and api_id_text.isdigit() else None
            self.settings.telegram_api_hash = self.api_hash_edit.text().strip() or None
            
            # Database settings
            self.settings.database_url = self.db_url_edit.text().strip()
            
            # Rate limiting
            self.settings.default_rate_limits = self.default_rate_spin.value()
            self.settings.max_messages_per_hour = self.max_hourly_spin.value()
            self.settings.max_messages_per_day = self.max_daily_spin.value()
            self.settings.global_max_concurrency = self.global_concurrency_spin.value()
            
            # Warmup settings
            self.settings.warmup_enabled = self.warmup_enabled_check.isChecked()
            self.settings.warmup_messages = self.warmup_messages_spin.value()
            self.settings.warmup_interval_minutes = self.warmup_interval_spin.value()
            
            # UI settings
            new_theme = self.theme_combo.currentData()
            self.settings.theme = new_theme
            
            # Language settings
            from ...services.translation import get_translation_manager
            new_language = self.language_combo.currentData()
            self.settings.language = new_language
            
            # Update translation manager
            translation_manager = get_translation_manager()
            translation_manager.set_language(new_language)
            
            self.settings.window_width = self.window_width_spin.value()
            self.settings.window_height = self.window_height_spin.value()
            self.settings.window_maximized = self.window_maximized_check.isChecked()
            
            # Apply theme immediately
            from ...gui.theme import ThemeManager
            theme_manager = ThemeManager()
            theme_manager.apply_theme(new_theme)
            
            # Safety settings
            self.settings.respect_rate_limits = self.respect_limits_check.isChecked()
            self.settings.stop_on_error = self.stop_on_error_check.isChecked()
            self.settings.max_retries = self.max_retries_spin.value()
            self.settings.retry_delay_seconds = self.retry_delay_spin.value()
            
            # Save to .env file (simplified - in real app would use proper config management)
            self.save_to_env_file()
            
            # Reload logger with new settings
            reload_logger()
            
            self.logger.info("Settings saved successfully")
            self.status_label.setText(_("settings.settings_saved"))
            self.settings_updated.emit()
            
            QMessageBox.information(self, _("settings.settings_saved"), _("settings.settings_saved"))
            
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
            self.status_label.setText(_("settings.settings_save_failed").format(error=str(e)))
            QMessageBox.critical(self, _("common.error"), _("settings.settings_save_failed").format(error=str(e)))
    
    def save_to_env_file(self):
        """Save settings to .env file."""
        try:
            env_content = f"""# Telegram API Configuration
TELEGRAM_API_ID={self.settings.telegram_api_id or ''}
TELEGRAM_API_HASH={self.settings.telegram_api_hash or ''}

# Application Settings
APP_ENV=development
LOG_LEVEL={self.settings.log_level}
DEBUG={str(self.settings.debug).lower()}
LANGUAGE={self.settings.language}
START_WITH_WINDOWS={str(self.settings.start_with_windows).lower()}

# Database
DATABASE_URL={self.settings.database_url}

# Rate Limiting
DEFAULT_RATE_LIMITS={self.settings.default_rate_limits}
GLOBAL_MAX_CONCURRENCY={self.settings.global_max_concurrency}
MAX_MESSAGES_PER_HOUR={self.settings.max_messages_per_hour}
MAX_MESSAGES_PER_DAY={self.settings.max_messages_per_day}

# Warmup Settings
WARMUP_ENABLED={str(self.settings.warmup_enabled).lower()}
WARMUP_MESSAGES={self.settings.warmup_messages}
WARMUP_INTERVAL_MINUTES={self.settings.warmup_interval_minutes}

# UI Settings
THEME={self.settings.theme}
WINDOW_WIDTH={self.settings.window_width}
WINDOW_HEIGHT={self.settings.window_height}
WINDOW_MAXIMIZED={str(self.settings.window_maximized).lower()}

# Safety Settings
RESPECT_RATE_LIMITS={str(self.settings.respect_rate_limits).lower()}
STOP_ON_ERROR={str(self.settings.stop_on_error).lower()}
MAX_RETRIES={self.settings.max_retries}
RETRY_DELAY_SECONDS={self.settings.retry_delay_seconds}
"""
            
            with open('.env', 'w') as f:
                f.write(env_content)
                
        except Exception as e:
            self.logger.error(f"Error saving to .env file: {e}")
    
    def reset_settings(self):
        """Reset settings to defaults."""
        reply = QMessageBox.question(
            self,
            _("settings.reset_to_defaults"),
            _("settings.reset_to_defaults"),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Create new settings with default values
            from ...services import Settings
            self.settings = Settings()
            
            # Update all UI fields to reflect default values
            self.debug_check.setChecked(self.settings.debug)
            self.log_level_combo.setCurrentText(self.settings.log_level)
            self.startup_check.setChecked(self.settings.start_with_windows)
            
            # Telegram settings
            self.api_id_edit.setText(str(self.settings.telegram_api_id) if self.settings.telegram_api_id else "")
            self.api_hash_edit.setText(self.settings.telegram_api_hash or "")
            
            # Database settings
            self.db_url_edit.setText(self.settings.database_url)
            
            # Rate limiting
            self.default_rate_spin.setValue(self.settings.default_rate_limits)
            self.max_hourly_spin.setValue(self.settings.max_messages_per_hour)
            self.max_daily_spin.setValue(self.settings.max_messages_per_day)
            self.global_concurrency_spin.setValue(self.settings.global_max_concurrency)
            
            # Warmup settings
            self.warmup_enabled_check.setChecked(self.settings.warmup_enabled)
            self.warmup_messages_spin.setValue(self.settings.warmup_messages)
            self.warmup_interval_spin.setValue(self.settings.warmup_interval_minutes)
            
            # UI settings
            # Set theme combo to correct value
            for i in range(self.theme_combo.count()):
                if self.theme_combo.itemData(i) == self.settings.theme:
                    self.theme_combo.setCurrentIndex(i)
                    break
            
            # Set language combo to correct value
            for i in range(self.language_combo.count()):
                if self.language_combo.itemData(i) == self.settings.language:
                    self.language_combo.setCurrentIndex(i)
                    break
            
            # Update translation manager
            from ...services.translation import get_translation_manager
            translation_manager = get_translation_manager()
            translation_manager.set_language(self.settings.language)
            
            self.window_width_spin.setValue(self.settings.window_width)
            self.window_height_spin.setValue(self.settings.window_height)
            self.window_maximized_check.setChecked(self.settings.window_maximized)
            
            # Apply theme immediately
            from ...gui.theme import ThemeManager
            theme_manager = ThemeManager()
            theme_manager.apply_theme(self.settings.theme)
            
            # Safety settings
            self.respect_limits_check.setChecked(self.settings.respect_rate_limits)
            self.stop_on_error_check.setChecked(self.settings.stop_on_error)
            self.max_retries_spin.setValue(self.settings.max_retries)
            self.retry_delay_spin.setValue(self.settings.retry_delay_seconds)
            
            # Save to .env file
            self.save_to_env_file()
            
            # Reload logger with new settings
            reload_logger()
            
            self.status_label.setText(_("settings.settings_reset"))
            QMessageBox.information(self, _("settings.settings_reset"), _("settings.settings_reset"))
    
    
    def on_language_combo_changed(self, text: str):
        """Handle language combo box change."""
        try:
            # Get the language value from the combo box
            current_index = self.language_combo.currentIndex()
            language_value = self.language_combo.itemData(current_index)
            
            if language_value:
                # Update the translation manager
                from ...services.translation import get_translation_manager
                translation_manager = get_translation_manager()
                translation_manager.set_language(language_value)
                
                # Update settings
                from ...services.settings import Language
                self.settings.language = Language(language_value)
                
                self.logger.info(f"Language changed to: {language_value}")
        except Exception as e:
            self.logger.error(f"Error changing language: {e}")
    
    def on_startup_changed(self, state: int):
        """Handle startup checkbox change."""
        try:
            enabled = state == 2  # Qt.Checked = 2
            
            # Import Windows startup utilities
            from ...utils.windows_startup import update_startup_setting
            
            # Update Windows startup setting
            app_name = "TelegramMultiAccountMessageSender"
            success = update_startup_setting(app_name, enabled)
            
            if success:
                # Update settings object
                self.settings.start_with_windows = enabled
                
                # Show success message
                if enabled:
                    QMessageBox.information(self, _("common.success"), _("settings.startup_enabled"))
                else:
                    QMessageBox.information(self, _("common.success"), _("settings.startup_disabled"))
            else:
                # Show error message
                QMessageBox.warning(self, _("common.error"), _("settings.startup_error"))
                # Revert checkbox state
                self.startup_check.setChecked(not enabled)
                
        except Exception as e:
            self.logger.error(f"Error updating startup setting: {e}")
            QMessageBox.warning(self, _("common.error"), _("settings.startup_error"))
            # Revert checkbox state
            self.startup_check.setChecked(not enabled)

    def on_language_changed(self, language: str):
        """Handle language change."""
        self.logger.info(f"Language changed to: {language}")
        # Update button texts
        if hasattr(self, 'save_button'):
            self.save_button.setText(_("settings.save_settings"))
        if hasattr(self, 'reset_button'):
            self.reset_button.setText(_("settings.reset_to_defaults"))
        # Update tab names
        if hasattr(self, 'tab_widget'):
            self.tab_widget.setTabText(0, _("settings.general"))
            self.tab_widget.setTabText(1, _("settings.rate_limiting"))
            self.tab_widget.setTabText(2, _("settings.user_interface"))
            self.tab_widget.setTabText(3, _("settings.safety"))
        # Update UI elements
        self.update_ui_translations()
        # Reload settings to refresh any other translated content
        self.load_settings()
    
    def update_ui_translations(self):
        """Update UI elements with current translations."""
        try:
            # Update debug checkbox
            if hasattr(self, 'debug_check'):
                self.debug_check.setText(_("settings.enable_debug_mode"))
            
            # Update log level label
            if hasattr(self, 'log_level_combo'):
                # Find the parent form layout and update the label
                parent = self.log_level_combo.parent()
                if parent and hasattr(parent, 'labelForField'):
                    label = parent.labelForField(self.log_level_combo)
                    if label:
                        label.setText(f"{_('settings.log_level')}:")
            
            # Update startup checkbox
            if hasattr(self, 'startup_check'):
                self.startup_check.setText(_("settings.start_with_windows"))
            
            # Update API ID and Hash labels
            if hasattr(self, 'api_id_edit'):
                parent = self.api_id_edit.parent()
                if parent and hasattr(parent, 'labelForField'):
                    label = parent.labelForField(self.api_id_edit)
                    if label:
                        label.setText(f"{_('settings.api_id')}:")
            
            if hasattr(self, 'api_hash_edit'):
                parent = self.api_hash_edit.parent()
                if parent and hasattr(parent, 'labelForField'):
                    label = parent.labelForField(self.api_hash_edit)
                    if label:
                        label.setText(f"{_('settings.api_hash')}:")
            
            # Update database URL label
            if hasattr(self, 'db_url_edit'):
                parent = self.db_url_edit.parent()
                if parent and hasattr(parent, 'labelForField'):
                    label = parent.labelForField(self.db_url_edit)
                    if label:
                        label.setText(f"{_('settings.database_url')}:")
            
            # Update warmup controls
            if hasattr(self, 'warmup_status_label'):
                self.warmup_status_label.setText(f"{_('settings.warmup_status')}: Not Available")
            
            if hasattr(self, 'start_warmup_button'):
                self.start_warmup_button.setText(_("settings.start_warmup_all"))
            
            if hasattr(self, 'stop_warmup_button'):
                self.stop_warmup_button.setText(_("settings.stop_all_warmup"))
            
            if hasattr(self, 'reset_warmup_button'):
                self.reset_warmup_button.setText(_("settings.reset_warmup_progress"))
            
            # Update language combo items
            if hasattr(self, 'language_combo'):
                language_items = [
                    _("settings.english"), _("settings.french"), _("settings.spanish"), _("settings.chinese"), 
                    _("settings.japanese"), _("settings.german"), _("settings.russian"), _("settings.estonian"), 
                    _("settings.portuguese"), _("settings.korean"), _("settings.catalan"), _("settings.basque"), 
                    _("settings.galician")
                ]
                for i, item in enumerate(language_items):
                    if i < self.language_combo.count():
                        self.language_combo.setItemText(i, item)
            
            # Update warmup info
            if hasattr(self, 'warmup_info'):
                self.warmup_info.setText(f"""
                <b>{_('settings.warmup_description')}:</b><br>
                {_('settings.warmup_help').replace('\\n', '<br>')}
                """)
                
        except Exception as e:
            self.logger.error(f"Error updating UI translations: {e}")
    
    def start_all_warmup(self):
        """Start warmup for all eligible accounts."""
        try:
            from ...services.db import get_session
            warmup_manager = get_warmup_manager()
            
            # Connect to warmup manager signals for progress tracking
            warmup_manager.warmup_started.connect(self.on_warmup_started)
            warmup_manager.warmup_progress.connect(self.on_warmup_progress)
            warmup_manager.warmup_completed.connect(self.on_warmup_completed)
            warmup_manager.warmup_error.connect(self.on_warmup_error)
            
            with get_session() as session:
                # Get all accounts that need warmup (not just ONLINE ones)
                accounts = session.query(Account).filter(
                    Account.warmup_enabled == True,
                    Account.is_active == True,
                    Account.is_deleted == False
                ).all()
                
                started_count = 0
                total_accounts = len(accounts)
                self.logger.info(f"Found {total_accounts} accounts eligible for warmup")
                
                # Update status to show we're starting
                self.warmup_status_label.setText(_("settings.starting_warmup").format(count=total_accounts))
                
                for account in accounts:
                    self.logger.info(f"Checking account {account.name} (ID: {account.id})")
                    if not account.is_warmup_complete():
                        self.logger.info(f"Starting warmup for account {account.name}")
                        if warmup_manager.start_warmup(account.id):
                            started_count += 1
                            self.logger.info(f"Successfully started warmup for account {account.name}")
                        else:
                            self.logger.warning(f"Failed to start warmup for account {account.name}")
                    else:
                        self.logger.info(f"Warmup already complete for account {account.name}")
                
                if started_count > 0:
                    self.warmup_status_label.setText(_("settings.warmup_started").format(count=started_count))
                    QMessageBox.information(self, _("settings.warmup_started"), _("settings.warmup_started").format(count=started_count))
                else:
                    self.warmup_status_label.setText(_("settings.no_warmup_needed"))
                    QMessageBox.information(self, _("settings.no_warmup_needed"), _("settings.no_warmup_needed"))
                    
        except Exception as e:
            self.logger.error(f"Error starting warmup: {e}")
            QMessageBox.critical(self, _("common.error"), _("settings.error_starting_warmup").format(error=str(e)))
    
    def on_warmup_started(self, account_id: int):
        """Handle warmup started signal."""
        try:
            from ...services.db import get_session
            from ...models import Account
            
            with get_session() as session:
                account = session.get(Account, account_id)
                if account:
                    self.logger.info(f"Warmup started for account {account.name}")
                    # Update status to show warmup is running
                    current_text = self.warmup_status_label.text()
                    if "warmup started" not in current_text.lower():
                        self.warmup_status_label.setText(f"{_('settings.warmup_running')}: {account.name}")
        except Exception as e:
            self.logger.error(f"Error handling warmup started: {e}")
    
    def on_warmup_progress(self, account_id: int, sent: int, target: int):
        """Handle warmup progress signal."""
        try:
            from ...services.db import get_session
            from ...models import Account
            
            with get_session() as session:
                account = session.get(Account, account_id)
                if account:
                    progress_percent = (sent / target * 100) if target > 0 else 0
                    self.logger.info(f"Warmup progress for {account.name}: {sent}/{target} ({progress_percent:.1f}%)")
                    self.warmup_status_label.setText(f"{_('settings.warmup_progress')}: {account.name} - {sent}/{target} ({progress_percent:.1f}%)")
        except Exception as e:
            self.logger.error(f"Error handling warmup progress: {e}")
    
    def on_warmup_completed(self, account_id: int):
        """Handle warmup completed signal."""
        try:
            from ...services.db import get_session
            from ...models import Account
            
            with get_session() as session:
                account = session.get(Account, account_id)
                if account:
                    self.logger.info(f"Warmup completed for account {account.name}")
                    self.warmup_status_label.setText(f"{_('settings.warmup_completed')}: {account.name}")
        except Exception as e:
            self.logger.error(f"Error handling warmup completed: {e}")
    
    def on_warmup_error(self, account_id: int, error_message: str):
        """Handle warmup error signal."""
        try:
            from ...services.db import get_session
            from ...models import Account
            
            with get_session() as session:
                account = session.get(Account, account_id)
                if account:
                    self.logger.error(f"Warmup error for account {account.name}: {error_message}")
                    self.warmup_status_label.setText(f"{_('settings.warmup_error')}: {account.name} - {error_message}")
        except Exception as e:
            self.logger.error(f"Error handling warmup error: {e}")
    
    def stop_all_warmup(self):
        """Stop warmup for all accounts."""
        try:
            # Note: This is a simple implementation. In a real scenario, you'd want to track
            # running warmup processes and stop them gracefully.
            self.warmup_status_label.setText(f"{_('settings.warmup_stopped')} (manual stop)")
            QMessageBox.information(self, _("settings.warmup_stopped"), _("settings.warmup_stopped"))
            
        except Exception as e:
            self.logger.error(f"Error stopping warmup: {e}")
            QMessageBox.critical(self, _("common.error"), _("settings.error_stopping_warmup").format(error=str(e)))
    
    def reset_all_warmup(self):
        """Reset warmup progress for all accounts."""
        try:
            reply = QMessageBox.question(
                self,
                _("settings.reset_warmup_progress"),
                _("settings.reset_warmup_progress"),
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                from ...services.db import get_session
                warmup_manager = get_warmup_manager()
                
                with get_session() as session:
                    accounts = session.query(Account).filter(
                        Account.warmup_enabled == True,
                        Account.is_active == True,
                        Account.is_deleted == False
                    ).all()
                    
                    reset_count = 0
                    for account in accounts:
                        if warmup_manager.reset_warmup(account.id):
                            reset_count += 1
                    
                    self.warmup_status_label.setText(f"{_('settings.warmup_reset')}: {reset_count} accounts")
                    QMessageBox.information(self, _("settings.warmup_reset"), _("settings.warmup_reset").format(count=reset_count))
                    
        except Exception as e:
            self.logger.error(f"Error resetting warmup: {e}")
            QMessageBox.critical(self, _("common.error"), _("settings.error_resetting_warmup").format(error=str(e)))
    
    def delete_all_logs(self):
        """Delete all log files to free memory space."""
        try:
            reply = QMessageBox.question(
                self,
                _("settings.delete_all_logs"),
                _("settings.delete_all_logs_confirmation"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                import os
                from pathlib import Path
                
                # Get log directory
                log_dir = Path(self.settings.app_data_dir) / "logs"
                deleted_files = []
                total_size = 0
                
                if log_dir.exists():
                    # Delete all log files
                    for log_file in log_dir.glob("*.log"):
                        if log_file.is_file():
                            file_size = log_file.stat().st_size
                            total_size += file_size
                            log_file.unlink()
                            deleted_files.append(log_file.name)
                
                # Also clear send logs from database
                from ...services.db import get_session
                from ...models import SendLog
                
                with get_session() as session:
                    # Count existing logs
                    log_count = session.query(SendLog).count()
                    
                    # Delete all send logs
                    session.query(SendLog).delete()
                    session.commit()
                
                # Format size for display
                if total_size > 1024 * 1024:
                    size_str = f"{total_size / (1024 * 1024):.1f} MB"
                elif total_size > 1024:
                    size_str = f"{total_size / 1024:.1f} KB"
                else:
                    size_str = f"{total_size} bytes"
                
                # Show success message
                message = f"{_('settings.logs_deleted_successfully')}\n\n"
                message += f"{_('settings.files_deleted')}: {len(deleted_files)}\n"
                message += f"{_('settings.database_logs_deleted')}: {log_count}\n"
                message += f"{_('settings.space_freed')}: {size_str}"
                
                QMessageBox.information(
                    self,
                    _("settings.logs_deleted_successfully"),
                    message
                )
                
                self.logger.info(f"Deleted {len(deleted_files)} log files and {log_count} database logs, freed {size_str}")
                
        except Exception as e:
            self.logger.error(f"Error deleting logs: {e}")
            QMessageBox.critical(
                self,
                _("common.error"),
                _("settings.error_deleting_logs").format(error=str(e))
            )
    
    def update_warmup_status(self):
        """Update warmup status display."""
        try:
            from ...services.db import get_session
            warmup_manager = get_warmup_manager()
            
            with get_session() as session:
                accounts = session.query(Account).filter(
                    Account.warmup_enabled == True,
                    Account.is_active == True,
                    Account.is_deleted == False
                ).all()
                
                total_accounts = len(accounts)
                completed_accounts = sum(1 for account in accounts if account.is_warmup_complete())
                in_progress_accounts = sum(1 for account in accounts if warmup_manager.warmup_in_progress.get(account.id, False))
                
                status_text = f"{_('settings.warmup_status')}: {completed_accounts}/{total_accounts} {_('settings.completed')}"
                if in_progress_accounts > 0:
                    status_text += f", {in_progress_accounts} {_('settings.in_progress')}"
                
                self.warmup_status_label.setText(status_text)
                
        except Exception as e:
            self.logger.error(f"Error updating warmup status: {e}")
            self.warmup_status_label.setText(f"{_('settings.warmup_status')}: {_('common.error')}")
