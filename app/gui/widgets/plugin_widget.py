"""
Plugin management widget for the Telegram Multi-Account Message Sender.
"""

from typing import Dict, Any, List
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QCheckBox,
    QSpinBox,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFileDialog,
    QComboBox,
)
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFont, QColor

from pathlib import Path
from ...services import get_logger
from ...services.translation import _
from ...services.plugin_manager import get_plugin_manager
from ...services.plugin_registry import (
    PluginRegistryError,
    PluginRegistryInstallError,
    PluginRegistryOfflineError,
    RegistryPluginEntry,
    get_plugin_registry_service,
)
from ...core.plugin import PluginStatus


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

        self.browse_registry_button = QPushButton(_("plugins.browse_registry"))
        self.browse_registry_button.clicked.connect(self.browse_registry)
        toolbar.addWidget(self.browse_registry_button)

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
        self.plugins_table.setHorizontalHeaderLabels(
            [
                _("plugins.name"),
                _("plugins.version"),
                _("plugins.type"),
                _("plugins.status"),
                _("plugins.author"),
                _("common.actions"),
            ]
        )
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
            self.plugins_table.setItem(
                row, 2, QTableWidgetItem(plugin_info.metadata.plugin_type.value.title())
            )

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

            info_btn = QPushButton(_("common.information"))
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
        <p><b>{_('plugins.description_label')}:</b> {metadata.description}</p>
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
        file_path, _selected_filter = QFileDialog.getOpenFileName(
            self, _("plugins.select_plugin_file"), "", "Python Files (*.py);;All Files (*)"
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
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.plugin_manager.reload_all_plugins()
            self.refresh_plugins()
            QMessageBox.information(self, _("common.success"), _("plugins.reloaded_successfully"))

    def browse_registry(self):
        """Open the plugin marketplace / registry browser."""
        dialog = PluginRegistryDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_plugins()


class PluginRegistryDialog(QDialog):
    """Browse and install plugins from the official curated registry."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.registry = get_plugin_registry_service()
        self.plugin_manager = get_plugin_manager()
        self._entries: List[RegistryPluginEntry] = []
        self.setup_ui()
        self.refresh_catalog()

    def setup_ui(self):
        self.setWindowTitle(_("plugins.registry_title"))
        self.resize(820, 480)
        layout = QVBoxLayout(self)

        help_label = QLabel(_("plugins.registry_help"))
        help_label.setWordWrap(True)
        layout.addWidget(help_label)

        filters = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(_("plugins.registry_search_placeholder"))
        self.search_edit.returnPressed.connect(self.refresh_catalog)
        filters.addWidget(self.search_edit)

        self.type_combo = QComboBox()
        self.type_combo.addItem(_("plugins.registry_all_types"), "")
        for value, label in (
            ("filter", "Filter"),
            ("analytics", "Analytics"),
            ("notification", "Notification"),
            ("integration", "Integration"),
            ("transformer", "Transformer"),
            ("ui_extension", "UI Extension"),
            ("custom", "Custom"),
        ):
            self.type_combo.addItem(label, value)
        filters.addWidget(self.type_combo)

        search_btn = QPushButton(_("plugins.registry_search"))
        search_btn.clicked.connect(self.refresh_catalog)
        filters.addWidget(search_btn)

        refresh_btn = QPushButton(_("common.refresh"))
        refresh_btn.clicked.connect(self.refresh_catalog)
        filters.addWidget(refresh_btn)
        layout.addLayout(filters)

        self.source_label = QLabel("")
        self.source_label.setStyleSheet("color: #888888;")
        layout.addWidget(self.source_label)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            [
                _("plugins.name"),
                _("plugins.version"),
                _("plugins.type"),
                _("plugins.author"),
                _("plugins.registry_availability"),
                _("common.actions"),
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        close_btn = buttons.button(QDialogButtonBox.Close)
        if close_btn:
            close_btn.clicked.connect(self.accept)
        layout.addWidget(buttons)

    def refresh_catalog(self):
        try:
            catalog = self.registry.fetch_catalog(prefer_remote=True)
            query = self.search_edit.text().strip()
            plugin_type = self.type_combo.currentData() or None
            from ...services.plugin_registry import search_catalog

            self._entries = search_catalog(
                catalog, query=query, plugin_type=plugin_type or None
            )
            source = catalog.source
            self.source_label.setText(
                _("plugins.registry_source").format(
                    source=source, name=catalog.name, updated=catalog.updated_at or "—"
                )
            )
            self._populate_table()
        except PluginRegistryOfflineError as exc:
            QMessageBox.warning(
                self,
                _("plugins.registry_offline_title"),
                _("plugins.registry_offline_message").format(error=str(exc)),
            )
        except PluginRegistryError as exc:
            QMessageBox.warning(self, _("common.error"), str(exc))

    def _availability_label(self, entry: RegistryPluginEntry) -> str:
        if entry.local_only or entry.bundled:
            return _("plugins.registry_bundled")
        if self.registry.is_installed(entry):
            return _("plugins.registry_installed")
        return _("plugins.registry_available")

    def _populate_table(self):
        self.table.setRowCount(len(self._entries))
        for row, entry in enumerate(self._entries):
            self.table.setItem(row, 0, QTableWidgetItem(entry.name))
            self.table.setItem(row, 1, QTableWidgetItem(entry.version))
            self.table.setItem(row, 2, QTableWidgetItem(entry.plugin_type.title()))
            self.table.setItem(row, 3, QTableWidgetItem(entry.author))
            self.table.setItem(row, 4, QTableWidgetItem(self._availability_label(entry)))

            actions = QWidget()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(2, 2, 2, 2)

            info_btn = QPushButton(_("common.information"))
            info_btn.clicked.connect(lambda _, e=entry: self.show_entry_info(e))
            actions_layout.addWidget(info_btn)

            if entry.is_installable and not self.registry.is_installed(entry):
                install_btn = QPushButton(_("plugins.registry_install"))
                install_btn.clicked.connect(lambda _, e=entry: self.install_entry(e))
                actions_layout.addWidget(install_btn)
            elif entry.is_installable and self.registry.is_installed(entry):
                reinstall_btn = QPushButton(_("plugins.registry_reinstall"))
                reinstall_btn.clicked.connect(
                    lambda _, e=entry: self.install_entry(e, overwrite=True)
                )
                actions_layout.addWidget(reinstall_btn)

            self.table.setCellWidget(row, 5, actions)

    def show_entry_info(self, entry: RegistryPluginEntry):
        text = f"""
        <h2>{entry.name}</h2>
        <p><b>ID:</b> {entry.id}</p>
        <p><b>{_('plugins.version')}:</b> {entry.version}</p>
        <p><b>{_('plugins.type')}:</b> {entry.plugin_type.title()}</p>
        <p><b>{_('plugins.author')}:</b> {entry.author}</p>
        <p><b>{_('plugins.description_label')}:</b> {entry.description}</p>
        """
        if entry.homepage:
            text += f"<p><b>{_('plugins.homepage')}:</b> {entry.homepage}</p>"
        if entry.repository:
            text += f"<p><b>{_('plugins.repository')}:</b> {entry.repository}</p>"
        if entry.tags:
            text += f"<p><b>Tags:</b> {', '.join(entry.tags)}</p>"
        QMessageBox.information(self, _("plugins.plugin_info"), text)

    def install_entry(self, entry: RegistryPluginEntry, overwrite: bool = False):
        reply = QMessageBox.question(
            self,
            _("common.confirm"),
            _("plugins.registry_install_confirm").format(name=entry.name, version=entry.version),
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        try:
            path = self.registry.install(entry.id, overwrite=overwrite)
            plugin_info = self.plugin_manager.load_plugin(path)
            if plugin_info:
                QMessageBox.information(
                    self,
                    _("common.success"),
                    _("plugins.registry_install_success").format(path=str(path)),
                )
            else:
                QMessageBox.warning(
                    self,
                    _("common.error"),
                    _("plugins.registry_install_load_failed").format(path=str(path)),
                )
            self.refresh_catalog()
        except PluginRegistryOfflineError as exc:
            QMessageBox.warning(
                self,
                _("plugins.registry_offline_title"),
                _("plugins.registry_offline_message").format(error=str(exc)),
            )
        except (PluginRegistryInstallError, PluginRegistryError) as exc:
            QMessageBox.warning(self, _("common.error"), str(exc))


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
