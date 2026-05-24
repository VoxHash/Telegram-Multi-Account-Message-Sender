"""
Cloud backup settings widget (Google Drive).
"""

from pathlib import Path
from typing import List, Optional

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
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
from ...services.translation import _


class CloudBackupWorker(QThread):
    """Run cloud backup operations off the UI thread."""

    finished = pyqtSignal(bool, str, object)

    def __init__(self, operation: str, **kwargs):
        super().__init__()
        self.operation = operation
        self.kwargs = kwargs

    def run(self):
        service = CloudBackupService()
        try:
            if self.operation == "connect":
                service.connect_google_drive()
                self.finished.emit(True, _("settings.cloud_connect_success"), None)
            elif self.operation == "disconnect":
                service.disconnect_google_drive()
                self.finished.emit(True, _("settings.cloud_disconnect_success"), None)
            elif self.operation == "backup":
                remote_id = service.backup_to_google_drive(
                    password=self.kwargs.get("password") or None
                )
                self.finished.emit(True, _("settings.cloud_backup_success"), remote_id)
            elif self.operation == "list":
                backups = service.list_google_drive_backups()
                self.finished.emit(True, _("settings.cloud_list_success"), backups)
            elif self.operation == "restore":
                pre_restore = service.restore_from_google_drive(
                    self.kwargs["remote_id"],
                    password=self.kwargs.get("password") or None,
                )
                self.finished.emit(
                    True,
                    _("settings.cloud_restore_success").format(path=str(pre_restore)),
                    pre_restore,
                )
            else:
                self.finished.emit(False, _("settings.cloud_unknown_operation"), None)
        except CloudBackupServiceError as exc:
            self.finished.emit(False, str(exc), None)
        except Exception as exc:
            self.finished.emit(False, _("settings.cloud_error").format(error=str(exc)), None)


class CloudBackupWidget(QWidget):
    """Settings tab for Google Drive cloud backup and restore."""

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
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label)

        connect_layout = QHBoxLayout()
        self.connect_button = QPushButton(_("settings.cloud_connect_drive"))
        self.connect_button.clicked.connect(self.connect_google_drive)
        connect_layout.addWidget(self.connect_button)

        self.disconnect_button = QPushButton(_("settings.cloud_disconnect"))
        self.disconnect_button.clicked.connect(self.disconnect_google_drive)
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

        self.restore_button = QPushButton(_("settings.cloud_restore_selected"))
        self.restore_button.clicked.connect(self.restore_selected)
        list_layout.addWidget(self.restore_button)
        layout.addWidget(list_group)

        help_label = QLabel(_("settings.cloud_help"))
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #888888; font-style: italic;")
        layout.addWidget(help_label)

        layout.addStretch()

    def refresh_connection_status(self):
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

        self._set_busy(True)
        self._worker = CloudBackupWorker(operation, **kwargs)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

    def _set_busy(self, busy: bool):
        for widget in (
            self.connect_button,
            self.disconnect_button,
            self.backup_button,
            self.refresh_button,
            self.restore_button,
        ):
            widget.setEnabled(not busy)

    def _on_worker_finished(self, success: bool, message: str, result):
        self._set_busy(False)
        self.refresh_connection_status()

        if self._worker and self._worker.operation == "list" and success:
            self._populate_backup_list(result or [])

        if success:
            QMessageBox.information(self, _("common.success"), message)
            if self._worker and self._worker.operation in ("connect", "backup", "restore"):
                if self._worker.operation == "connect":
                    self.refresh_backup_list()
        else:
            QMessageBox.critical(self, _("common.error"), message)

    def connect_google_drive(self):
        self._start_worker("connect")

    def disconnect_google_drive(self):
        self._start_worker("disconnect")

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

        self._start_worker("restore", remote_id=remote_id, password=self._password())
