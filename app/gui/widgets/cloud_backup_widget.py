"""
Cloud backup settings widget (Google Drive + S3-compatible).
"""

from pathlib import Path
from typing import List, Optional

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...services import get_logger
from ...services.cloud import CloudBackupService, RemoteBackupItem
from ...services.cloud.cloud_backup_service import CloudBackupServiceError
from ...services.cloud.network import is_offline_error_message
from ...services.translation import _

PROVIDER_GOOGLE_DRIVE = "google_drive"
PROVIDER_S3 = "s3"


class CloudBackupWorker(QThread):
    """Run cloud backup operations off the UI thread."""

    finished = pyqtSignal(bool, str, object)

    def __init__(self, operation: str, **kwargs):
        super().__init__()
        self.operation = operation
        self.kwargs = kwargs

    def run(self):
        service = CloudBackupService()
        provider = self.kwargs.get("provider") or PROVIDER_GOOGLE_DRIVE
        try:
            if self.operation == "connect":
                if provider == PROVIDER_S3:
                    service.connect_s3()
                    self.finished.emit(True, _("settings.cloud_s3_connect_success"), None)
                else:
                    service.connect_google_drive()
                    self.finished.emit(True, _("settings.cloud_connect_success"), None)
            elif self.operation == "disconnect":
                if provider == PROVIDER_S3:
                    service.disconnect_s3()
                    self.finished.emit(
                        True, _("settings.cloud_s3_disconnect_success"), None
                    )
                else:
                    service.disconnect_google_drive()
                    self.finished.emit(True, _("settings.cloud_disconnect_success"), None)
            elif self.operation == "backup":
                if provider == PROVIDER_S3:
                    remote_id = service.backup_to_s3(
                        password=self.kwargs.get("password") or None
                    )
                    self.finished.emit(
                        True, _("settings.cloud_s3_backup_success"), remote_id
                    )
                else:
                    remote_id = service.backup_to_google_drive(
                        password=self.kwargs.get("password") or None
                    )
                    self.finished.emit(True, _("settings.cloud_backup_success"), remote_id)
            elif self.operation == "list":
                if provider == PROVIDER_S3:
                    backups = service.list_s3_backups()
                else:
                    backups = service.list_google_drive_backups()
                self.finished.emit(True, _("settings.cloud_list_success"), backups)
            elif self.operation == "restore":
                if provider == PROVIDER_S3:
                    pre_restore = service.restore_from_s3(
                        self.kwargs["remote_id"],
                        password=self.kwargs.get("password") or None,
                    )
                else:
                    pre_restore = service.restore_from_google_drive(
                        self.kwargs["remote_id"],
                        password=self.kwargs.get("password") or None,
                    )
                self.finished.emit(
                    True,
                    _("settings.cloud_restore_success").format(path=str(pre_restore)),
                    pre_restore,
                )
            elif self.operation == "restore_local":
                pre_restore = service.restore_from_local_package(
                    Path(self.kwargs["package_path"]),
                    password=self.kwargs.get("password") or None,
                    mode=str(self.kwargs.get("mode") or "replace"),
                )
                self.finished.emit(
                    True,
                    _("settings.cloud_restore_success").format(path=str(pre_restore)),
                    pre_restore,
                )
            elif self.operation == "export_handoff":
                built = service.export_local_package(
                    Path(self.kwargs["package_path"]),
                    password=self.kwargs.get("password") or None,
                    include_sessions=bool(self.kwargs.get("include_sessions", True)),
                    entity_kinds=self.kwargs.get("entity_kinds"),
                )
                success_key = (
                    "settings.cloud_export_entities_success"
                    if self.kwargs.get("entity_kinds")
                    else "settings.cloud_export_handoff_success"
                )
                self.finished.emit(
                    True,
                    _(success_key).format(path=str(built)),
                    built,
                )
            else:
                self.finished.emit(False, _("settings.cloud_unknown_operation"), None)
        except CloudBackupServiceError as exc:
            self.finished.emit(False, str(exc), None)
        except Exception as exc:
            self.finished.emit(False, _("settings.cloud_error").format(error=str(exc)), None)


class CloudBackupWidget(QWidget):
    """Settings tab for Google Drive / S3 cloud backup and restore."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.service = CloudBackupService()
        self._worker: Optional[CloudBackupWorker] = None
        self._remote_backups: List[RemoteBackupItem] = []
        self.setup_ui()
        self.refresh_connection_status()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        status_group = QGroupBox(_("settings.cloud_backup"))
        status_layout = QVBoxLayout(status_group)

        provider_row = QHBoxLayout()
        provider_row.addWidget(QLabel(_("settings.cloud_provider")))
        self.provider_combo = QComboBox()
        self.provider_combo.addItem(
            _("settings.cloud_provider_google_drive"), PROVIDER_GOOGLE_DRIVE
        )
        self.provider_combo.addItem(_("settings.cloud_provider_s3"), PROVIDER_S3)
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        provider_row.addWidget(self.provider_combo)
        status_layout.addLayout(provider_row)

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label)

        connect_layout = QHBoxLayout()
        self.connect_button = QPushButton(_("settings.cloud_connect_drive"))
        self.connect_button.clicked.connect(self.connect_provider)
        connect_layout.addWidget(self.connect_button)

        self.disconnect_button = QPushButton(_("settings.cloud_disconnect"))
        self.disconnect_button.clicked.connect(self.disconnect_provider)
        connect_layout.addWidget(self.disconnect_button)
        status_layout.addLayout(connect_layout)
        layout.addWidget(status_group)

        backup_group = QGroupBox(_("settings.cloud_backup_actions"))
        backup_layout = QVBoxLayout(backup_group)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText(_("settings.cloud_encryption_optional"))
        backup_layout.addWidget(QLabel(_("settings.cloud_encryption_password")))
        backup_layout.addWidget(self.password_edit)

        action_layout = QHBoxLayout()
        self.backup_button = QPushButton(_("settings.cloud_backup_now"))
        self.backup_button.clicked.connect(self.backup_now)
        action_layout.addWidget(self.backup_button)

        self.refresh_button = QPushButton(_("settings.cloud_refresh_list"))
        self.refresh_button.clicked.connect(self.refresh_backup_list)
        action_layout.addWidget(self.refresh_button)
        backup_layout.addLayout(action_layout)
        layout.addWidget(backup_group)

        list_group = QGroupBox(_("settings.cloud_backups_list"))
        list_layout = QVBoxLayout(list_group)
        self.backups_list = QListWidget()
        self.backups_list.setSelectionMode(QListWidget.SingleSelection)
        list_layout.addWidget(self.backups_list)

        restore_row = QHBoxLayout()
        self.restore_button = QPushButton(_("settings.cloud_restore_selected"))
        self.restore_button.clicked.connect(self.restore_selected)
        restore_row.addWidget(self.restore_button)
        self.restore_local_button = QPushButton(_("settings.cloud_restore_local"))
        self.restore_local_button.clicked.connect(self.restore_local_file)
        restore_row.addWidget(self.restore_local_button)
        list_layout.addLayout(restore_row)

        handoff_row = QHBoxLayout()
        self.export_handoff_button = QPushButton(_("settings.cloud_export_handoff"))
        self.export_handoff_button.clicked.connect(self.export_handoff_package)
        handoff_row.addWidget(self.export_handoff_button)
        self.export_entities_button = QPushButton(_("settings.cloud_export_entities"))
        self.export_entities_button.clicked.connect(self.export_entities_package)
        handoff_row.addWidget(self.export_entities_button)
        list_layout.addLayout(handoff_row)
        layout.addWidget(list_group)

        help_label = QLabel(_("settings.cloud_help"))
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #888888; font-style: italic;")
        layout.addWidget(help_label)

        layout.addStretch()

    def _selected_provider(self) -> str:
        data = self.provider_combo.currentData()
        return str(data) if data else PROVIDER_GOOGLE_DRIVE

    def _on_provider_changed(self, _index: int = 0) -> None:
        self.backups_list.clear()
        self._remote_backups = []
        self.refresh_connection_status()

    def refresh_connection_status(self):
        provider = self._selected_provider()
        if provider == PROVIDER_S3:
            self.connect_button.setText(_("settings.cloud_connect_s3"))
            connected = self.service.is_s3_connected()
            if connected:
                self.status_label.setText(_("settings.cloud_s3_status_connected"))
            elif self.service.is_s3_configured():
                self.status_label.setText(_("settings.cloud_s3_status_configured"))
            else:
                self.status_label.setText(_("settings.cloud_s3_status_disconnected"))
        else:
            self.connect_button.setText(_("settings.cloud_connect_drive"))
            connected = self.service.is_google_drive_connected()
            if connected:
                self.status_label.setText(_("settings.cloud_status_connected"))
            else:
                self.status_label.setText(_("settings.cloud_status_disconnected"))
        self._set_actions_enabled(connected)

    def _set_actions_enabled(self, connected: bool):
        self.disconnect_button.setEnabled(connected)
        self.backup_button.setEnabled(connected)
        self.refresh_button.setEnabled(connected)
        self.restore_button.setEnabled(connected)
        self.backups_list.setEnabled(connected)
        # Local package restore / handoff export work offline without cloud.
        self.restore_local_button.setEnabled(True)
        self.export_handoff_button.setEnabled(True)
        self.export_entities_button.setEnabled(True)

    def _password(self) -> Optional[str]:
        value = self.password_edit.text().strip()
        return value or None

    def _start_worker(self, operation: str, **kwargs):
        if self._worker and self._worker.isRunning():
            QMessageBox.warning(
                self,
                _("common.warning"),
                _("settings.cloud_operation_in_progress"),
            )
            return

        kwargs.setdefault("provider", self._selected_provider())
        self._set_busy(True)
        self._worker = CloudBackupWorker(operation, **kwargs)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

    def _set_busy(self, busy: bool):
        for widget in (
            self.provider_combo,
            self.connect_button,
            self.disconnect_button,
            self.backup_button,
            self.refresh_button,
            self.restore_button,
            self.restore_local_button,
            self.export_handoff_button,
            self.export_entities_button,
        ):
            widget.setEnabled(not busy)

    def _on_worker_finished(self, success: bool, message: str, result):
        self._set_busy(False)
        self.refresh_connection_status()

        if self._worker and self._worker.operation == "list" and success:
            self._populate_backup_list(result or [])

        if success:
            QMessageBox.information(self, _("common.success"), message)
            if self._worker and self._worker.operation in (
                "connect",
                "backup",
                "restore",
                "restore_local",
            ):
                if self._worker.operation == "connect":
                    self.refresh_backup_list()
        else:
            self._show_cloud_error(message)

    def _show_cloud_error(self, message: str) -> None:
        """Show offline-aware restore/list/backup errors with actionable guidance."""
        operation = self._worker.operation if self._worker else ""
        if is_offline_error_message(message):
            if operation == "restore":
                title = _("settings.cloud_offline_restore_title")
                body = _("settings.cloud_offline_restore_message")
            else:
                title = _("settings.cloud_offline_title")
                body = _("settings.cloud_offline_message")
            detail = message.strip()
            if detail:
                body = f"{body}\n\n{detail}"
            QMessageBox.warning(self, title, body)
            return
        QMessageBox.critical(self, _("common.error"), message)

    def connect_provider(self):
        self._start_worker("connect")

    def disconnect_provider(self):
        self._start_worker("disconnect")

    # Backwards-compatible aliases used by older call sites / tests
    def connect_google_drive(self):
        self.provider_combo.setCurrentIndex(
            self.provider_combo.findData(PROVIDER_GOOGLE_DRIVE)
        )
        self._start_worker("connect", provider=PROVIDER_GOOGLE_DRIVE)

    def disconnect_google_drive(self):
        self._start_worker("disconnect", provider=PROVIDER_GOOGLE_DRIVE)

    def backup_now(self):
        self._start_worker("backup", password=self._password())

    def refresh_backup_list(self):
        self._start_worker("list")

    def _populate_backup_list(self, backups: List[RemoteBackupItem]):
        self._remote_backups = backups
        self.backups_list.clear()
        for item in backups:
            created = item.created_at.strftime("%Y-%m-%d %H:%M UTC")
            size_kb = max(1, item.size_bytes // 1024)
            label = f"{item.name} — {size_kb} KB — {created}"
            list_item = QListWidgetItem(label)
            list_item.setData(Qt.UserRole, item.remote_id)
            self.backups_list.addItem(list_item)

    def restore_selected(self):
        selected = self.backups_list.currentItem()
        if not selected:
            QMessageBox.warning(
                self,
                _("common.warning"),
                _("settings.cloud_select_backup"),
            )
            return

        remote_id = selected.data(Qt.UserRole)
        confirm = QMessageBox.warning(
            self,
            _("settings.cloud_restore_confirm_title"),
            _("settings.cloud_restore_confirm_message"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        provider = self._selected_provider()
        if provider == PROVIDER_S3:
            connected = self.service.is_s3_connected()
            disconnected_msg = _("settings.cloud_s3_status_disconnected")
        else:
            connected = self.service.is_google_drive_connected()
            disconnected_msg = _("settings.cloud_status_disconnected")
        if not connected:
            QMessageBox.warning(
                self,
                _("common.warning"),
                disconnected_msg,
            )
            return

        self._start_worker("restore", remote_id=remote_id, password=self._password())

    def restore_local_file(self, package_path: Optional[Path] = None):
        """Restore from a local ``.tmas-backup.zip`` (picker or file association)."""
        from PyQt5.QtWidgets import QFileDialog

        path = Path(package_path) if package_path else None
        if path is None or not path.is_file():
            chosen, _ = QFileDialog.getOpenFileName(
                self,
                _("settings.cloud_restore_local_title"),
                "",
                _("settings.cloud_restore_local_filter"),
            )
            if not chosen:
                return
            path = Path(chosen)

        mode = "replace"
        try:
            info = self.service.inspect_local_package(path, password=self._password())
        except CloudBackupServiceError as exc:
            QMessageBox.critical(self, _("common.error"), str(exc))
            return

        if info.get("has_entities") and not info.get("has_database"):
            choice = QMessageBox.question(
                self,
                _("settings.cloud_import_mode_title"),
                _("settings.cloud_import_mode_message").format(path=str(path)),
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Yes,
            )
            if choice == QMessageBox.Cancel:
                return
            # Yes = merge, No = replace entity kinds
            mode = "merge" if choice == QMessageBox.Yes else "replace"
        else:
            confirm = QMessageBox.warning(
                self,
                _("settings.cloud_restore_local_confirm_title"),
                _("settings.cloud_restore_local_confirm_message").format(path=str(path)),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if confirm != QMessageBox.Yes:
                return

        self._start_worker(
            "restore_local",
            package_path=str(path),
            password=self._password(),
            mode=mode,
        )

    def export_handoff_package(self):
        """Export a local handoff package (DB + sessions) without cloud upload."""
        from PyQt5.QtWidgets import QFileDialog

        from ...services.cloud import BackupPackageBuilder

        default_name = BackupPackageBuilder.generate_handoff_filename()
        chosen, _ = QFileDialog.getSaveFileName(
            self,
            _("settings.cloud_export_handoff_title"),
            default_name,
            _("settings.cloud_restore_local_filter"),
        )
        if not chosen:
            return

        path = Path(chosen)
        confirm = QMessageBox.information(
            self,
            _("settings.cloud_export_handoff_confirm_title"),
            _("settings.cloud_export_handoff_confirm_message").format(path=str(path)),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if confirm != QMessageBox.Yes:
            return

        self._start_worker(
            "export_handoff",
            package_path=str(path),
            password=self._password(),
            include_sessions=True,
        )

    def export_entities_package(self):
        """Export templates and/or campaigns only (merge-friendly entities.json)."""
        from PyQt5.QtWidgets import QFileDialog

        from ...services.cloud import BackupPackageBuilder

        dialog = QDialog(self)
        dialog.setWindowTitle(_("settings.cloud_export_entities_title"))
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(_("settings.cloud_export_entities_prompt")))
        templates_cb = QCheckBox(_("settings.cloud_export_entities_templates"))
        templates_cb.setChecked(True)
        campaigns_cb = QCheckBox(_("settings.cloud_export_entities_campaigns"))
        campaigns_cb.setChecked(True)
        layout.addWidget(templates_cb)
        layout.addWidget(campaigns_cb)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec_() != QDialog.Accepted:
            return

        kinds = []
        if templates_cb.isChecked():
            kinds.append("templates")
        if campaigns_cb.isChecked():
            kinds.append("campaigns")
        if not kinds:
            QMessageBox.warning(
                self,
                _("common.warning"),
                _("settings.cloud_export_entities_none"),
            )
            return

        default_name = BackupPackageBuilder.generate_entities_filename()
        chosen, _ = QFileDialog.getSaveFileName(
            self,
            _("settings.cloud_export_entities_save_title"),
            default_name,
            _("settings.cloud_restore_local_filter"),
        )
        if not chosen:
            return

        self._start_worker(
            "export_handoff",
            package_path=str(Path(chosen)),
            password=self._password(),
            include_sessions=False,
            entity_kinds=kinds,
        )

    def offer_associated_backup(self, package_path: Path):
        """Prompt restore when the OS opened a ``.tmas-backup.zip`` via file association."""
        self.restore_local_file(package_path=package_path)
