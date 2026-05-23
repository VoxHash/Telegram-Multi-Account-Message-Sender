"""
Telegram channel/group selector widget for browsing and selecting chats.
"""

import asyncio
from typing import Optional, List, Dict, Any
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QGroupBox,
    QFormLayout,
    QMessageBox,
    QProgressDialog,
    QTreeWidget,
    QTreeWidgetItem,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from ...models import Account, AccountStatus
from ...services import get_logger, get_session
from ...services.translation import _
from sqlmodel import select
from telethon import TelegramClient
from telethon.tl.types import (
    Channel,
    Chat,
    User,
)


class TelegramChatFetcher(QThread):
    """Worker thread to fetch Telegram chats."""

    chats_fetched = pyqtSignal(list)  # List of chat dictionaries
    error_occurred = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(
        self,
        account_id: int,
        api_id: int,
        api_hash: str,
        session_path: str,
        proxy: Optional[Dict[str, Any]] = None,
    ):
        super().__init__()
        self.account_id = account_id
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_path = session_path
        self.proxy = proxy
        self.logger = get_logger()
        self._should_stop = False

    def stop(self):
        """Stop the fetching process."""
        self._should_stop = True

    def run(self):
        """Fetch chats from Telegram."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                loop.run_until_complete(self._fetch_chats())
            finally:
                loop.close()
        except Exception as e:
            self.logger.error(f"Error fetching chats: {e}")
            self.error_occurred.emit(str(e))

    async def _fetch_chats(self):
        """Async method to fetch chats."""
        client = None
        try:
            self.progress.emit("Connecting to Telegram...")

            client = TelegramClient(self.session_path, self.api_id, self.api_hash, proxy=self.proxy)

            if self.proxy:
                self.logger.info(
                    f"Using proxy for chat fetching: {self.proxy['proxy_type']}://{self.proxy['addr']}:{self.proxy['port']}"
                )

            await client.connect()

            if not await client.is_user_authorized():
                self.error_occurred.emit(
                    "Account is not authorized. Please authorize the account first."
                )
                return

            self.progress.emit("Fetching chats and channels...")

            chats = []
            async for dialog in client.iter_dialogs():
                if self._should_stop:
                    break

                entity = dialog.entity
                chat_info = {
                    "id": entity.id,
                    "title": getattr(entity, "title", None)
                    or getattr(entity, "first_name", "") + " " + getattr(entity, "last_name", ""),
                    "username": getattr(entity, "username", None),
                    "type": self._get_entity_type(entity),
                    "unread_count": dialog.unread_count,
                    "is_pinned": dialog.pinned,
                    "is_verified": getattr(entity, "verified", False),
                    "member_count": getattr(entity, "participants_count", None),
                }

                # Get threads for groups/channels
                if isinstance(entity, Channel) and entity.megagroup:
                    chat_info["has_threads"] = True
                    # Fetch threads
                    try:
                        threads = []
                        async for message in client.iter_messages(entity, limit=100):
                            if hasattr(message, "reply_to") and message.reply_to:
                                thread_id = message.reply_to.reply_to_msg_id
                                if thread_id and thread_id not in [t["id"] for t in threads]:
                                    threads.append(
                                        {
                                            "id": thread_id,
                                            "title": f"Thread {thread_id}",
                                            "message_count": 1,
                                        }
                                    )
                        chat_info["threads"] = threads[:10]  # Limit to 10 threads
                    except Exception as e:
                        self.logger.warning(
                            f"Could not fetch threads for {chat_info['title']}: {e}"
                        )
                        chat_info["threads"] = []
                else:
                    chat_info["has_threads"] = False
                    chat_info["threads"] = []

                chats.append(chat_info)

            await client.disconnect()
            self.chats_fetched.emit(chats)

        except Exception as e:
            self.logger.error(f"Error in _fetch_chats: {e}")
            if client:
                try:
                    await client.disconnect()
                except Exception:
                    pass
            self.error_occurred.emit(str(e))

    def _get_entity_type(self, entity) -> str:
        """Get entity type string."""
        if isinstance(entity, Channel):
            if entity.broadcast:
                return "channel"
            else:
                return "supergroup"
        elif isinstance(entity, Chat):
            return "group"
        elif isinstance(entity, User):
            return "user"
        else:
            return "unknown"


class TelegramSelectorDialog(QDialog):
    """Dialog for selecting Telegram chats/channels/groups."""

    chat_selected = pyqtSignal(dict)  # Emits selected chat info

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.selected_chat = None
        self.selected_thread_id = None
        self.fetcher = None

        self.setup_ui()
        self.load_accounts()

    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle(_("recipients.select_from_telegram"))
        self.setModal(True)
        self.resize(800, 600)

        layout = QVBoxLayout(self)

        # Account selection
        account_group = QGroupBox(_("common.account"))
        account_layout = QFormLayout(account_group)

        self.account_combo = QComboBox()
        self.account_combo.currentIndexChanged.connect(self.on_account_changed)
        account_layout.addRow(_("common.account") + ":", self.account_combo)

        self.refresh_button = QPushButton(_("common.refresh"))
        self.refresh_button.clicked.connect(self.fetch_chats)
        account_layout.addRow("", self.refresh_button)

        layout.addWidget(account_group)

        # Search
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel(_("common.search") + ":"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(_("recipients.search_chats"))
        self.search_edit.textChanged.connect(self.filter_chats)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        # Chats list
        chats_group = QGroupBox(_("recipients.telegram_chats"))
        chats_layout = QVBoxLayout(chats_group)

        self.chats_tree = QTreeWidget()
        self.chats_tree.setHeaderLabels(
            [_("common.name"), _("common.type"), _("recipients.members"), _("recipients.username")]
        )
        self.chats_tree.setAlternatingRowColors(True)
        self.chats_tree.setSelectionMode(QTreeWidget.SingleSelection)
        self.chats_tree.itemDoubleClicked.connect(self.on_chat_double_clicked)
        self.chats_tree.itemSelectionChanged.connect(self.on_chat_selected)
        chats_layout.addWidget(self.chats_tree)

        layout.addWidget(chats_group)

        # Thread selection (for groups with threads)
        self.thread_group = QGroupBox(_("recipients.select_thread"))
        thread_layout = QVBoxLayout(self.thread_group)

        self.thread_combo = QComboBox()
        self.thread_combo.addItem(_("recipients.no_thread"), None)
        thread_layout.addWidget(self.thread_combo)

        layout.addWidget(self.thread_group)
        self.thread_group.setVisible(False)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept_selection)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def load_accounts(self):
        """Load available accounts."""
        try:
            with get_session() as session:
                query = select(Account).where(
                    Account.is_deleted.is_(False), Account.status == AccountStatus.ONLINE
                )
                accounts = session.exec(query).all()

                self.account_combo.clear()
                for account in accounts:
                    self.account_combo.addItem(
                        f"{account.name} ({account.phone_number})", account.id
                    )

                if accounts:
                    self.fetch_chats()
                else:
                    QMessageBox.warning(
                        self, _("common.warning"), _("recipients.no_online_accounts")
                    )
        except Exception as e:
            self.logger.error(f"Error loading accounts: {e}")
            QMessageBox.critical(self, _("common.error"), str(e))

    def on_account_changed(self):
        """Handle account selection change."""
        self.fetch_chats()

    def fetch_chats(self):
        """Fetch chats from selected account."""
        account_id = self.account_combo.currentData()
        if not account_id:
            return

        try:
            with get_session() as session:
                account = session.get(Account, account_id)
                if not account:
                    return

                from ...services import get_settings

                settings = get_settings()

                if not settings.telegram_api_id or not settings.telegram_api_hash:
                    QMessageBox.warning(
                        self, _("common.warning"), _("recipients.api_credentials_required")
                    )
                    return

                # Stop previous fetcher if running
                if self.fetcher and self.fetcher.isRunning():
                    self.fetcher.stop()
                    self.fetcher.wait()

                # Create progress dialog
                progress = QProgressDialog(
                    _("recipients.fetching_chats"), _("common.cancel"), 0, 0, self
                )
                progress.setWindowModality(Qt.WindowModal)
                progress.setCancelButton(None)
                progress.show()

                # Get proxy configuration from account
                proxy = account.get_telethon_proxy()

                # Create fetcher
                self.fetcher = TelegramChatFetcher(
                    account.id,
                    settings.telegram_api_id,
                    settings.telegram_api_hash,
                    account.session_path,
                    proxy=proxy,
                )

                self.fetcher.chats_fetched.connect(
                    lambda chats: (progress.close(), self.populate_chats(chats))
                )
                self.fetcher.error_occurred.connect(
                    lambda error: (
                        progress.close(),
                        QMessageBox.critical(self, _("common.error"), error),
                    )
                )
                self.fetcher.progress.connect(progress.setLabelText)

                self.fetcher.start()

        except Exception as e:
            self.logger.error(f"Error fetching chats: {e}")
            QMessageBox.critical(self, _("common.error"), str(e))

    def populate_chats(self, chats: List[Dict[str, Any]]):
        """Populate the chats tree with fetched chats."""
        self.chats_tree.clear()
        self.all_chats = chats

        for chat in chats:
            item = QTreeWidgetItem(
                [
                    chat.get("title", "Unknown"),
                    chat.get("type", "unknown").title(),
                    str(chat.get("member_count", "")) if chat.get("member_count") else "",
                    f"@{chat.get('username', '')}" if chat.get("username") else "",
                ]
            )
            item.setData(0, Qt.UserRole, chat)

            # Add thread items if available
            if chat.get("has_threads") and chat.get("threads"):
                for thread in chat.get("threads", []):
                    thread_id = thread.get("id")
                    thread_title = thread.get("title") or f"Thread {thread_id}"
                    thread_item = QTreeWidgetItem(
                        [
                            f"  └─ {thread_title}",
                            _("recipients.thread"),
                            "",
                            "",
                        ]
                    )
                    thread_item.setData(0, Qt.UserRole, {**chat, "thread_id": thread.get("id")})
                    item.addChild(thread_item)

            self.chats_tree.addTopLevelItem(item)

        self.chats_tree.expandAll()
        self.chats_tree.resizeColumnToContents(0)

    def filter_chats(self, text: str):
        """Filter chats by search text."""
        text_lower = text.lower()

        for i in range(self.chats_tree.topLevelItemCount()):
            item = self.chats_tree.topLevelItem(i)
            chat = item.data(0, Qt.UserRole)

            if (
                not text
                or text_lower in chat.get("title", "").lower()
                or text_lower in (chat.get("username", "") or "").lower()
            ):
                item.setHidden(False)
                # Show/hide children
                for j in range(item.childCount()):
                    child = item.child(j)
                    child.setHidden(False)
            else:
                item.setHidden(True)

    def on_chat_selected(self):
        """Handle chat selection."""
        selected_items = self.chats_tree.selectedItems()
        if not selected_items:
            return

        item = selected_items[0]
        chat_data = item.data(0, Qt.UserRole)

        if chat_data:
            self.selected_chat = chat_data
            self.selected_thread_id = chat_data.get("thread_id")

            # Update thread combo if it's a group with threads
            if chat_data.get("has_threads"):
                self.thread_group.setVisible(True)
                self.thread_combo.clear()
                self.thread_combo.addItem(_("recipients.no_thread"), None)

                for thread in chat_data.get("threads", []):
                    self.thread_combo.addItem(
                        thread.get("title", f"Thread {thread.get('id')}"), thread.get("id")
                    )
            else:
                self.thread_group.setVisible(False)

    def on_chat_double_clicked(self, item, column):
        """Handle chat double-click."""
        self.accept_selection()

    def accept_selection(self):
        """Accept the selected chat."""
        selected_items = self.chats_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, _("common.warning"), _("recipients.select_chat_first"))
            return

        item = selected_items[0]
        chat_data = item.data(0, Qt.UserRole)

        if not chat_data:
            return

        # Get thread ID if selected
        thread_id = None
        if self.thread_group.isVisible() and self.thread_combo.currentIndex() > 0:
            thread_id = self.thread_combo.currentData()
        elif chat_data.get("thread_id"):
            thread_id = chat_data.get("thread_id")

        # Prepare result
        result = {
            "id": chat_data.get("id"),
            "title": chat_data.get("title"),
            "username": chat_data.get("username"),
            "type": chat_data.get("type"),
            "thread_id": thread_id,
        }

        self.selected_chat = result
        self.chat_selected.emit(result)
        self.accept()
