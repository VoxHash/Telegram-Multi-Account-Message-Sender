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


class SettingsWidget(QWidget):
    """Main settings management widget."""
    
    settings_updated = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.settings = get_settings()
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # General Settings Tab
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        # Application Settings
        app_group = QGroupBox("Application Settings")
        app_layout = QFormLayout(app_group)
        
        self.app_name_edit = QLineEdit()
        self.app_name_edit.setText(self.settings.app_name)
        app_layout.addRow("Application Name:", self.app_name_edit)
        
        self.debug_check = QCheckBox("Enable Debug Mode")
        self.debug_check.setChecked(self.settings.debug)
        app_layout.addRow(self.debug_check)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.log_level_combo.setCurrentText(self.settings.log_level)
        app_layout.addRow("Log Level:", self.log_level_combo)
        
        general_layout.addWidget(app_group)
        
        # Telegram Settings
        telegram_group = QGroupBox("Telegram API Settings")
        telegram_layout = QFormLayout(telegram_group)
        
        self.api_id_edit = QLineEdit()
        self.api_id_edit.setText(str(self.settings.telegram_api_id) if self.settings.telegram_api_id else "")
        self.api_id_edit.setPlaceholderText("Your Telegram API ID")
        telegram_layout.addRow("API ID:", self.api_id_edit)
        
        self.api_hash_edit = QLineEdit()
        self.api_hash_edit.setText(self.settings.telegram_api_hash or "")
        self.api_hash_edit.setEchoMode(QLineEdit.Password)
        self.api_hash_edit.setPlaceholderText("Your Telegram API Hash")
        telegram_layout.addRow("API Hash:", self.api_hash_edit)
        
        general_layout.addWidget(telegram_group)
        
        # Database Settings
        db_group = QGroupBox("Database Settings")
        db_layout = QFormLayout(db_group)
        
        self.db_url_edit = QLineEdit()
        self.db_url_edit.setText(self.settings.database_url)
        self.db_url_edit.setPlaceholderText("Database connection URL")
        db_layout.addRow("Database URL:", self.db_url_edit)
        
        general_layout.addWidget(db_group)
        
        tab_widget.addTab(general_tab, "General")
        
        # Rate Limiting Tab
        rate_tab = QWidget()
        rate_layout = QVBoxLayout(rate_tab)
        
        # Default Rate Limits
        rate_group = QGroupBox("Default Rate Limits")
        rate_form_layout = QFormLayout(rate_group)
        
        self.default_rate_spin = QSpinBox()
        self.default_rate_spin.setRange(1, 60)
        self.default_rate_spin.setValue(self.settings.default_rate_limits)
        rate_form_layout.addRow("Messages per Minute:", self.default_rate_spin)
        
        self.max_hourly_spin = QSpinBox()
        self.max_hourly_spin.setRange(1, 1000)
        self.max_hourly_spin.setValue(self.settings.max_messages_per_hour)
        rate_form_layout.addRow("Max Messages per Hour:", self.max_hourly_spin)
        
        self.max_daily_spin = QSpinBox()
        self.max_daily_spin.setRange(1, 10000)
        self.max_daily_spin.setValue(self.settings.max_messages_per_day)
        rate_form_layout.addRow("Max Messages per Day:", self.max_daily_spin)
        
        self.global_concurrency_spin = QSpinBox()
        self.global_concurrency_spin.setRange(1, 20)
        self.global_concurrency_spin.setValue(self.settings.global_max_concurrency)
        rate_form_layout.addRow("Global Max Concurrency:", self.global_concurrency_spin)
        
        rate_layout.addWidget(rate_group)
        
        # Warmup Settings
        warmup_group = QGroupBox("Account Warmup Settings")
        warmup_layout = QFormLayout(warmup_group)
        
        self.warmup_enabled_check = QCheckBox("Enable Account Warmup")
        self.warmup_enabled_check.setChecked(self.settings.warmup_enabled)
        warmup_layout.addRow(self.warmup_enabled_check)
        
        self.warmup_messages_spin = QSpinBox()
        self.warmup_messages_spin.setRange(1, 100)
        self.warmup_messages_spin.setValue(self.settings.warmup_messages)
        warmup_layout.addRow("Warmup Messages:", self.warmup_messages_spin)
        
        self.warmup_interval_spin = QSpinBox()
        self.warmup_interval_spin.setRange(10, 1440)
        self.warmup_interval_spin.setValue(self.settings.warmup_interval_minutes)
        warmup_layout.addRow("Warmup Interval (minutes):", self.warmup_interval_spin)
        
        rate_layout.addWidget(warmup_group)
        
        tab_widget.addTab(rate_tab, "Rate Limiting")
        
        # UI Settings Tab
        ui_tab = QWidget()
        ui_layout = QVBoxLayout(ui_tab)
        
        # Theme Settings
        theme_group = QGroupBox("Theme Settings")
        theme_layout = QFormLayout(theme_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["auto", "light", "dark"])
        self.theme_combo.setCurrentText(self.settings.theme)
        theme_layout.addRow("Theme:", self.theme_combo)
        
        ui_layout.addWidget(theme_group)
        
        # Window Settings
        window_group = QGroupBox("Window Settings")
        window_layout = QFormLayout(window_group)
        
        self.window_width_spin = QSpinBox()
        self.window_width_spin.setRange(800, 2000)
        self.window_width_spin.setValue(self.settings.window_width)
        window_layout.addRow("Default Width:", self.window_width_spin)
        
        self.window_height_spin = QSpinBox()
        self.window_height_spin.setRange(600, 1500)
        self.window_height_spin.setValue(self.settings.window_height)
        window_layout.addRow("Default Height:", self.window_height_spin)
        
        self.window_maximized_check = QCheckBox("Start Maximized")
        self.window_maximized_check.setChecked(self.settings.window_maximized)
        window_layout.addRow(self.window_maximized_check)
        
        ui_layout.addWidget(window_group)
        
        tab_widget.addTab(ui_tab, "User Interface")
        
        # Safety Settings Tab
        safety_tab = QWidget()
        safety_layout = QVBoxLayout(safety_tab)
        
        # Safety Controls
        safety_group = QGroupBox("Safety Controls")
        safety_form_layout = QFormLayout(safety_group)
        
        self.respect_limits_check = QCheckBox("Respect Rate Limits")
        self.respect_limits_check.setChecked(self.settings.respect_rate_limits)
        safety_form_layout.addRow(self.respect_limits_check)
        
        self.stop_on_error_check = QCheckBox("Stop on Error")
        self.stop_on_error_check.setChecked(self.settings.stop_on_error)
        safety_form_layout.addRow(self.stop_on_error_check)
        
        self.max_retries_spin = QSpinBox()
        self.max_retries_spin.setRange(0, 10)
        self.max_retries_spin.setValue(self.settings.max_retries)
        safety_form_layout.addRow("Max Retries:", self.max_retries_spin)
        
        self.retry_delay_spin = QSpinBox()
        self.retry_delay_spin.setRange(1, 60)
        self.retry_delay_spin.setValue(self.settings.retry_delay_seconds)
        safety_form_layout.addRow("Retry Delay (seconds):", self.retry_delay_spin)
        
        safety_layout.addWidget(safety_group)
        
        tab_widget.addTab(safety_tab, "Safety")
        
        # About Tab
        about_tab = QWidget()
        about_layout = QVBoxLayout(about_tab)
        
        # About Information
        about_group = QGroupBox("About Telegram Multi-Account Message Sender")
        about_form_layout = QFormLayout(about_group)
        
        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setMaximumHeight(300)
        about_text.setHtml("""
        <h2>🚀 Telegram Multi-Account Message Sender v1.0.0</h2>
        
        <p><b>Professional-grade desktop application for managing and sending messages across multiple Telegram accounts safely with advanced features like scheduling, spintax, media support, and compliance controls.</b></p>
        
        <h3>✨ Key Features:</h3>
        <ul>
        <li><b>🏦 Account Management:</b> Multi-account support with proxy configuration</li>
        <li><b>📢 Campaign System:</b> Advanced campaign builder with A/B testing</li>
        <li><b>👥 Recipient Management:</b> Individual management and CSV import</li>
        <li><b>📊 Analytics & Logging:</b> Real-time logs and performance metrics</li>
        <li><b>🔒 Safety & Compliance:</b> Rate limiting and safety controls</li>
        <li><b>🎨 Modern UI:</b> Professional PyQt5 interface with theme support</li>
        </ul>
        
        <h3>🛠️ Technical Stack:</h3>
        <ul>
        <li><b>Python:</b> 3.10+ with type hints</li>
        <li><b>GUI:</b> PyQt5 framework</li>
        <li><b>Database:</b> SQLModel ORM with SQLite</li>
        <li><b>API:</b> Telethon for Telegram integration</li>
        <li><b>Settings:</b> Pydantic configuration management</li>
        </ul>
        
        <h3>📄 License:</h3>
        <p>BSD 3-Clause License - See LICENSE file for details</p>
        
        <h3>👨‍💻 Developer:</h3>
        <p><b>VoxHash</b> - contact@voxhash.dev</p>
        
        <h3>⚠️ Disclaimer:</h3>
        <p>This application is for educational and legitimate business purposes only. Users are responsible for complying with Telegram's Terms of Service and applicable laws.</p>
        
        <p><i>Made with ❤️ by VoxHash</i></p>
        <p><i>Professional Telegram automation made simple! 🚀</i></p>
        """)
        about_form_layout.addRow(about_text)
        
        about_layout.addWidget(about_group)
        
        tab_widget.addTab(about_tab, "About")
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_button)
        
        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.clicked.connect(self.reset_settings)
        button_layout.addWidget(self.reset_button)
        
        self.reload_button = QPushButton("Reload Settings")
        self.reload_button.clicked.connect(self.reload_settings)
        button_layout.addWidget(self.reload_button)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Status label
        self.status_label = QLabel("Settings loaded")
        layout.addWidget(self.status_label)
    
    def load_settings(self):
        """Load current settings into the form."""
        # This is already done in setup_ui
        pass
    
    def save_settings(self):
        """Save settings to file."""
        try:
            # Update settings object
            self.settings.app_name = self.app_name_edit.text()
            self.settings.debug = self.debug_check.isChecked()
            self.settings.log_level = self.log_level_combo.currentText()
            
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
            self.settings.theme = self.theme_combo.currentText()
            self.settings.window_width = self.window_width_spin.value()
            self.settings.window_height = self.window_height_spin.value()
            self.settings.window_maximized = self.window_maximized_check.isChecked()
            
            # Safety settings
            self.settings.respect_rate_limits = self.respect_limits_check.isChecked()
            self.settings.stop_on_error = self.stop_on_error_check.isChecked()
            self.settings.max_retries = self.max_retries_spin.value()
            self.settings.retry_delay_seconds = self.retry_delay_spin.value()
            
            # Save to .env file (simplified - in real app would use proper config management)
            self.save_to_env_file()
            
            self.logger.info("Settings saved successfully")
            self.status_label.setText("Settings saved successfully")
            self.settings_updated.emit()
            
            QMessageBox.information(self, "Settings Saved", "Settings have been saved successfully!")
            
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
            self.status_label.setText(f"Error saving settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")
    
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
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Reload settings from defaults
            from ...services import Settings
            self.settings = Settings()
            self.load_settings()
            self.status_label.setText("Settings reset to defaults")
            QMessageBox.information(self, "Settings Reset", "Settings have been reset to defaults!")
    
    def reload_settings(self):
        """Reload settings from file."""
        try:
            from ...services import Settings
            self.settings = Settings()
            self.load_settings()
            self.status_label.setText("Settings reloaded from file")
            QMessageBox.information(self, "Settings Reloaded", "Settings have been reloaded from file!")
        except Exception as e:
            self.logger.error(f"Error reloading settings: {e}")
            self.status_label.setText(f"Error reloading settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to reload settings: {e}")
