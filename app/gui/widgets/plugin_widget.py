"""
Plugin management widget for the Telegram Multi-Account Message Sender.
"""

from typing import Optional, List, Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QComboBox, QCheckBox, QSpinBox,
    QMessageBox, QDialog, QDialogButtonBox, QFormLayout,
    QTextEdit, QDateTimeEdit, QProgressBar, QTabWidget, QFrame,
    QFileDialog, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QDateTime
from PyQt5.QtGui import QFont, QIcon, QColor

from pathlib import Path
from ...models import Account, AccountStatus, Campaign, CampaignStatus
from ...services import get_logger, get_session
from ...services.translation import _, get_translation_manager
from ...services.plugin_manager import get_plugin_manager
from ...core.plugin import PluginInfo, PluginStatus, PluginType
from sqlmodel import select, func


class PluginListWidget(QWidget):
    """Widget displaying list of plugins with management options."""

    plugin_selected = pyqtSignal(str)  # Emits plugin_id
    plugin_enabled = pyqtSignal(str)
    plugin_disabled = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.plugin_manager = get_plugin_manager()
        self.setup_ui()
        self.refresh_plugins()

    def setup_ui(self):
        """Set up the plugin list UI."""
        layout = QVBoxLayout(self)

        # Toolbar
        toolbar = QHBoxLayout()
        
        self.refresh_button = QPushButton(_("common.refresh"))
        self.refresh_button.clicked.connect(self.refresh_plugins)
        toolbar.addWidget(self.refresh_button)

        self.load_button = QPushButton(_("plugins.load_plugin"))
        self.load_button.clicked.connect(self.load_plugin_file)
        toolbar.addWidget(self.load_button)

        self.reload_all_button = QPushButton(_("plugins.reload_all"))
        self.reload_all_button.clicked.connect(self.reload_all_plugins)
        toolbar.addWidget(self.reload_all_button)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Plugins table
        self.plugins_table = QTableWidget()
        self.plugins_table.setColumnCount(6)
        self.plugins_table.setHorizontalHeaderLabels([
            _("plugins.name"),
            _("plugins.version"),
            _("plugins.type"),
            _("plugins.status"),
            _("plugins.author"),
            _("common.actions")
        ])
        self.plugins_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.plugins_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.plugins_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.plugins_table.itemSelectionChanged.connect(self.on_plugin_selected)
        layout.addWidget(self.plugins_table)

    def refresh_plugins(self):
        """Refresh the plugins list."""
        self.plugins_table.setRowCount(0)
        plugins = self.plugin_manager.list_plugins()

        self.plugins_table.setRowCount(len(plugins))
        for row, plugin_info in enumerate(plugins):
            metadata = plugin_info.metadata

            # Name
            self.plugins_table.setItem(row, 0, QTableWidgetItem(metadata.name))

            # Version
            self.plugins_table.setItem(row, 1, QTableWidgetItem(metadata.version))

            # Type
            self.plugins_table.setItem(row, 2, QTableWidgetItem(plugin_info.metadata.plugin_type.value.title()))

            # Status
            status_item = QTableWidgetItem(plugin_info.status.value.title())
            if plugin_info.status == PluginStatus.ENABLED:
                status_item.setForeground(QColor("#28a745"))  # Green
            elif plugin_info.status == PluginStatus.DISABLED:
                status_item.setForeground(QColor("#6c757d"))  # Gray
            elif plugin_info.status == PluginStatus.ERROR:
                status_item.setForeground(QColor("#dc3545"))  # Red
            self.plugins_table.setItem(row, 3, status_item)

            # Author
            self.plugins_table.setItem(row, 4, QTableWidgetItem(metadata.author))

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)

            plugin_id = f"{metadata.name}@{metadata.version}"

            if plugin_info.status == PluginStatus.ENABLED:
                disable_btn = QPushButton(_("plugins.disable"))
                disable_btn.clicked.connect(lambda _, pid=plugin_id: self.disable_plugin(pid))
                actions_layout.addWidget(disable_btn)
            else:
                enable_btn = QPushButton(_("plugins.enable"))
                enable_btn.clicked.connect(lambda _, pid=plugin_id: self.enable_plugin(pid))
                actions_layout.addWidget(enable_btn)

            config_btn = QPushButton(_("plugins.configure"))
            config_btn.clicked.connect(lambda _, pid=plugin_id: self.configure_plugin(pid))
            actions_layout.addWidget(config_btn)

            info_btn = QPushButton(_("common.info"))
            info_btn.clicked.connect(lambda _, pid=plugin_id: self.show_plugin_info(pid))
            actions_layout.addWidget(info_btn)

            self.plugins_table.setCellWidget(row, 5, actions_widget)

    def on_plugin_selected(self):
        """Handle plugin selection."""
        selected_items = self.plugins_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            name_item = self.plugins_table.item(row, 0)
            version_item = self.plugins_table.item(row, 1)
            if name_item and version_item:
                plugin_id = f"{name_item.text()}@{version_item.text()}"
                self.plugin_selected.emit(plugin_id)

    def enable_plugin(self, plugin_id: str):
        """Enable a plugin."""
        if self.plugin_manager.enable_plugin(plugin_id):
            QMessageBox.information(self, _("common.success"), _("plugins.enabled_successfully"))
            self.refresh_plugins()
            self.plugin_enabled.emit(plugin_id)
        else:
            QMessageBox.warning(self, _("common.error"), _("plugins.enable_failed"))

    def disable_plugin(self, plugin_id: str):
        """Disable a plugin."""
        if self.plugin_manager.disable_plugin(plugin_id):
            QMessageBox.information(self, _("common.success"), _("plugins.disabled_successfully"))
            self.refresh_plugins()
            self.plugin_disabled.emit(plugin_id)
        else:
            QMessageBox.warning(self, _("common.error"), _("plugins.disable_failed"))

    def configure_plugin(self, plugin_id: str):
        """Configure a plugin."""
        plugin = self.plugin_manager.get_plugin(plugin_id)
        if not plugin:
            QMessageBox.warning(self, _("common.error"), _("plugins.plugin_not_found"))
            return

        # Get current config
        current_config = plugin.config or plugin.get_default_config()

        # Create config dialog
        dialog = PluginConfigDialog(plugin, current_config, self)
        if dialog.exec_() == QDialog.Accepted:
            new_config = dialog.get_config()
            if self.plugin_manager.set_plugin_config(plugin_id, new_config):
                QMessageBox.information(self, _("common.success"), _("plugins.config_saved"))
            else:
                QMessageBox.warning(self, _("common.error"), _("plugins.config_save_failed"))

    def show_plugin_info(self, plugin_id: str):
        """Show detailed plugin information."""
        plugin_info = self.plugin_manager.get_plugin_info(plugin_id)
        if not plugin_info:
            QMessageBox.warning(self, _("common.error"), _("plugins.plugin_not_found"))
            return

        metadata = plugin_info.metadata

        info_text = f"""
        <h2>{metadata.name}</h2>
        <p><b>{_('plugins.version')}:</b> {metadata.version}</p>
        <p><b>{_('plugins.type')}:</b> {metadata.plugin_type.value.title()}</p>
        <p><b>{_('plugins.author')}:</b> {metadata.author}</p>
        <p><b>{_('plugins.status')}:</b> {plugin_info.status.value.title()}</p>
        <p><b>{_('plugins.description')}:</b> {metadata.description}</p>
        """
        
        if metadata.homepage:
            info_text += f"<p><b>{_('plugins.homepage')}:</b> <a href='{metadata.homepage}'>{metadata.homepage}</a></p>"
        
        if metadata.repository:
            info_text += f"<p><b>{_('plugins.repository')}:</b> <a href='{metadata.repository}'>{metadata.repository}</a></p>"
        
        if plugin_info.error_message:
            info_text += f"<p><b>{_('common.error')}:</b> {plugin_info.error_message}</p>"

        QMessageBox.information(self, _("plugins.plugin_info"), info_text)

    def load_plugin_file(self):
        """Load a plugin from a file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            _("plugins.select_plugin_file"),
            "",
            "Python Files (*.py);;All Files (*)"
        )

        if file_path:
            plugin_info = self.plugin_manager.load_plugin(Path(file_path))
            if plugin_info:
                QMessageBox.information(self, _("common.success"), _("plugins.loaded_successfully"))
                self.refresh_plugins()
            else:
                QMessageBox.warning(self, _("common.error"), _("plugins.load_failed"))

    def reload_all_plugins(self):
        """Reload all plugins."""
        reply = QMessageBox.question(
            self,
            _("common.confirm"),
            _("plugins.reload_all_confirm"),
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.plugin_manager.reload_all_plugins()
            self.refresh_plugins()
            QMessageBox.information(self, _("common.success"), _("plugins.reloaded_successfully"))


class PluginConfigDialog(QDialog):
    """Dialog for configuring a plugin."""

    def __init__(self, plugin, config: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.config = config.copy()
        self.setup_ui()

    def setup_ui(self):
        """Set up the configuration dialog UI."""
        self.setWindowTitle(_("plugins.configure_plugin").format(name=self.plugin.metadata.name))
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        # Create input fields for each config key
        self.config_widgets = {}
        default_config = self.plugin.get_default_config()

        for key, value in default_config.items():
            if isinstance(value, bool):
                widget = QCheckBox()
                widget.setChecked(self.config.get(key, value))
                self.config_widgets[key] = widget
            elif isinstance(value, int):
                widget = QSpinBox()
                widget.setValue(self.config.get(key, value))
                self.config_widgets[key] = widget
            elif isinstance(value, str):
                widget = QLineEdit()
                widget.setText(self.config.get(key, value))
                self.config_widgets[key] = widget
            else:
                widget = QLineEdit()
                widget.setText(str(self.config.get(key, value)))
                self.config_widgets[key] = widget

            form_layout.addRow(key + ":", widget)

        layout.addLayout(form_layout)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_config(self) -> Dict[str, Any]:
        """Get configuration from widgets."""
        config = {}
        for key, widget in self.config_widgets.items():
            if isinstance(widget, QCheckBox):
                config[key] = widget.isChecked()
            elif isinstance(widget, QSpinBox):
                config[key] = widget.value()
            elif isinstance(widget, QLineEdit):
                config[key] = widget.text()
        return config


class PluginWidget(QWidget):
    """Main plugin management widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.setup_ui()

    def setup_ui(self):
        """Set up the plugin management UI."""
        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel(_("plugins.title"))
        title_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        layout.addWidget(title_label)

        # Description
        desc_label = QLabel(_("plugins.description"))
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # Plugin list
        self.plugin_list = PluginListWidget()
        layout.addWidget(self.plugin_list)

        layout.addStretch()

