"""
Template management widgets.
"""

from typing import Optional, List, Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QComboBox, QCheckBox, QSpinBox,
    QMessageBox, QDialog, QDialogButtonBox, QFormLayout,
    QTextEdit, QFileDialog, QAbstractItemView
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QColor

from ...models import MessageTemplate
from ...services import get_logger, get_session
from ...core import SpintaxProcessor


class TemplateDialog(QDialog):
    """Dialog for creating/editing templates."""
    
    template_saved = pyqtSignal(int)
    
    def __init__(self, parent=None, template: Optional[MessageTemplate] = None):
        super().__init__(parent)
        self.template = template
        self.logger = get_logger()
        self.spintax_processor = SpintaxProcessor()
        self.setup_ui()
        
        if template:
            self.load_template_data()
    
    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Create Template" if not self.template else "Edit Template")
        self.setModal(True)
        self.resize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Basic Information
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Template name (e.g., 'Welcome Message')")
        basic_layout.addRow("Name:", self.name_edit)
        
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Brief description of this template")
        basic_layout.addRow("Description:", self.description_edit)
        
        layout.addWidget(basic_group)
        
        # Message Content
        message_group = QGroupBox("Message Content")
        message_layout = QVBoxLayout(message_group)
        
        # Message text
        message_layout.addWidget(QLabel("Message Text:"))
        self.message_edit = QTextEdit()
        self.message_edit.setPlaceholderText("Enter your message template here...\n\nYou can use variables like {name}, {email}, etc.")
        self.message_edit.setMinimumHeight(150)
        message_layout.addWidget(self.message_edit)
        
        # Variables help
        variables_help = QLabel("Available variables: {name}, {email}, {phone}, {company}, {date}, {time}")
        variables_help.setStyleSheet("color: #888888; font-style: italic;")
        message_layout.addWidget(variables_help)
        
        layout.addWidget(message_group)
        
        # Spintax Settings
        spintax_group = QGroupBox("Spintax Settings")
        spintax_layout = QFormLayout(spintax_group)
        
        self.use_spintax_check = QCheckBox("Enable Spintax")
        self.use_spintax_check.toggled.connect(self.toggle_spintax_settings)
        spintax_layout.addRow(self.use_spintax_check)
        
        self.spintax_example_edit = QLineEdit()
        self.spintax_example_edit.setPlaceholderText("Example: Hello {name|friend|buddy}, welcome to {our company|our service}!")
        spintax_layout.addRow("Spintax Example:", self.spintax_example_edit)
        
        layout.addWidget(spintax_group)
        
        # Tags
        tags_group = QGroupBox("Tags")
        tags_layout = QFormLayout(tags_group)
        
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("welcome, onboarding, marketing (comma-separated)")
        tags_layout.addRow("Tags:", self.tags_edit)
        
        layout.addWidget(tags_group)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.save_template)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Initialize spintax settings as disabled
        self.toggle_spintax_settings(False)
    
    def toggle_spintax_settings(self, enabled: bool):
        """Toggle spintax settings visibility."""
        self.spintax_example_edit.setEnabled(enabled)
    
    def load_template_data(self):
        """Load template data into the form."""
        if not self.template:
            return
        
        self.name_edit.setText(self.template.name)
        self.description_edit.setText(self.template.description or "")
        self.message_edit.setText(self.template.body)
        self.use_spintax_check.setChecked(self.template.use_spintax)
        self.spintax_example_edit.setText(self.template.spintax_text or "")
        
        # Load tags
        if self.template.tags:
            tags_list = self.template.get_tags_list()
            self.tags_edit.setText(", ".join(tags_list))
    
    def save_template(self):
        """Save template data."""
        try:
            # Validate required fields
            if not self.name_edit.text().strip():
                QMessageBox.warning(self, "Validation Error", "Name is required")
                return
            
            if not self.message_edit.toPlainText().strip():
                QMessageBox.warning(self, "Validation Error", "Message text is required")
                return
            
            # Create or update template
            if self.template:
                # Update existing template
                self.template.name = self.name_edit.text().strip()
                self.template.description = self.description_edit.text().strip() or None
                self.template.body = self.message_edit.toPlainText().strip()
                self.template.use_spintax = self.use_spintax_check.isChecked()
                self.template.spintax_text = self.spintax_example_edit.text().strip() or None
            else:
                # Create new template
                self.template = MessageTemplate(
                    name=self.name_edit.text().strip(),
                    description=self.description_edit.text().strip() or None,
                    body=self.message_edit.toPlainText().strip(),
                    use_spintax=self.use_spintax_check.isChecked(),
                    spintax_text=self.spintax_example_edit.text().strip() or None
                )
            
            # Update tags
            tags_text = self.tags_edit.text().strip()
            if tags_text:
                tags_list = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
                self.template.set_tags_list(tags_list)
            else:
                self.template.set_tags_list([])
            
            # Save to database
            session = get_session()
            try:
                if self.template.id is None:
                    session.add(self.template)
                else:
                    session.merge(self.template)
                session.commit()
                
                # Get the saved template ID before closing session
                template_id = self.template.id
                template_name = self.template.name
            finally:
                session.close()
            
            self.logger.info(f"Template saved: {template_name}")
            self.template_saved.emit(template_id)
            self.accept()
            
        except Exception as e:
            self.logger.error(f"Error saving template: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save template: {e}")


class TemplateListWidget(QWidget):
    """Widget for displaying and managing templates."""
    
    template_selected = pyqtSignal(int)
    template_updated = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.setup_ui()
        self.load_templates()
        
        # Setup refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_templates)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
    
    def setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Message Templates")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.add_button = QPushButton("Add Template")
        self.add_button.clicked.connect(self.add_template)
        header_layout.addWidget(self.add_button)
        
        self.edit_button = QPushButton("Edit Template")
        self.edit_button.clicked.connect(self.edit_template)
        self.edit_button.setEnabled(False)
        header_layout.addWidget(self.edit_button)
        
        self.delete_button = QPushButton("Delete Template")
        self.delete_button.clicked.connect(self.delete_template)
        self.delete_button.setEnabled(False)
        header_layout.addWidget(self.delete_button)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_templates)
        header_layout.addWidget(self.refresh_button)
        
        layout.addLayout(header_layout)
        
        # Templates table
        self.templates_table = QTableWidget()
        self.templates_table.setColumnCount(6)
        self.templates_table.setHorizontalHeaderLabels([
            "Name", "Description", "Message Preview", "Spintax", "Tags", "Actions"
        ])
        
        # Configure table
        header = self.templates_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        self.templates_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.templates_table.setSelectionMode(QTableWidget.SingleSelection)
        self.templates_table.setAlternatingRowColors(True)
        self.templates_table.itemSelectionChanged.connect(self.on_selection_changed)
        
        # Set custom styling for black and gray alternating rows
        self.templates_table.setStyleSheet("""
            QTableWidget {
                alternate-background-color: #2d2d2d;
                background-color: #1a1a1a;
                gridline-color: #404040;
                color: white;
                selection-background-color: #0078d4;
                selection-color: white;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #0078d4 !important;
                color: white !important;
            }
            QTableWidget::item:alternate {
                background-color: #2d2d2d;
            }
            QTableWidget::item:alternate:selected {
                background-color: #0078d4 !important;
                color: white !important;
            }
        """)
        
        # Connect cell clicked signal for actions
        self.templates_table.cellClicked.connect(self.on_cell_clicked)
        
        layout.addWidget(self.templates_table)
        
        # Status bar
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
    
    def load_templates(self):
        """Load templates from database."""
        try:
            session = get_session()
            try:
                from ...models import MessageTemplate
                from sqlmodel import select
                templates = session.exec(select(MessageTemplate).where(MessageTemplate.is_deleted == False)).all()
            finally:
                session.close()
            
            self.templates_table.setRowCount(len(templates))
            
            for row, template in enumerate(templates):
                # Name - Disabled text field
                name_item = QTableWidgetItem(template.name)
                name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable | Qt.ItemIsSelectable)
                # Store template ID in the name item for selection handling
                name_item.setData(Qt.UserRole, template.id)
                self.templates_table.setItem(row, 0, name_item)
                
                # Description - Disabled text field
                description_item = QTableWidgetItem(template.description or "")
                description_item.setFlags(description_item.flags() & ~Qt.ItemIsEditable | Qt.ItemIsSelectable)
                self.templates_table.setItem(row, 1, description_item)
                
                # Message Preview - Disabled text field
                message_preview = template.body[:100] + "..." if len(template.body) > 100 else template.body
                message_item = QTableWidgetItem(message_preview)
                message_item.setFlags(message_item.flags() & ~Qt.ItemIsEditable | Qt.ItemIsSelectable)
                self.templates_table.setItem(row, 2, message_item)
                
                # Spintax - Enhanced button-like appearance
                spintax_item = QTableWidgetItem("Yes" if template.use_spintax else "No")
                spintax_item.setFlags(spintax_item.flags() & ~Qt.ItemIsEditable | Qt.ItemIsSelectable)
                
                # Set spintax-specific styling
                if template.use_spintax:
                    spintax_item.setBackground(QColor(34, 197, 94))  # Green
                    spintax_item.setForeground(Qt.white)
                else:
                    spintax_item.setBackground(QColor(107, 114, 128))  # Gray
                    spintax_item.setForeground(Qt.white)
                
                # Center align spintax text
                spintax_item.setTextAlignment(Qt.AlignCenter)
                self.templates_table.setItem(row, 3, spintax_item)
                
                # Tags - Disabled text field
                tags_list = template.get_tags_list()
                tags_text = ", ".join(tags_list) if tags_list else "No tags"
                tags_item = QTableWidgetItem(tags_text)
                tags_item.setFlags(tags_item.flags() & ~Qt.ItemIsEditable | Qt.ItemIsSelectable)
                self.templates_table.setItem(row, 4, tags_item)
                
                # Actions - Create action buttons
                actions_item = QTableWidgetItem("Edit | Delete | Preview")
                actions_item.setFlags(actions_item.flags() & ~Qt.ItemIsEditable | Qt.ItemIsSelectable)
                actions_item.setTextAlignment(Qt.AlignCenter)
                actions_item.setData(Qt.UserRole, template.id)  # Store template ID for actions
                self.templates_table.setItem(row, 5, actions_item)
            
            self.status_label.setText(f"Loaded {len(templates)} templates")
            
        except Exception as e:
            self.logger.error(f"Error loading templates: {e}")
            self.status_label.setText(f"Error loading templates: {e}")
    
    def refresh_templates(self):
        """Refresh templates data."""
        self.load_templates()
    
    def on_cell_clicked(self, row, column):
        """Handle cell click events."""
        if column == 5:  # Actions column
            template_id = self.templates_table.item(row, 0).data(Qt.UserRole)
            if template_id is not None:
                self.show_action_menu(row, column, template_id)
        else:
            # For other columns, ensure the row is selected
            self.templates_table.selectRow(row)
            # Also trigger selection changed manually
            self.on_selection_changed()
    
    def show_action_menu(self, row, column, template_id):
        """Show action menu for template actions."""
        from PyQt5.QtWidgets import QMenu
        
        # Get template name for display
        template_name = self.templates_table.item(row, 0).text()
        
        # Create context menu
        menu = QMenu(self)
        
        # Edit action
        edit_action = menu.addAction("✏️ Edit")
        edit_action.triggered.connect(lambda: self.edit_template_by_id(template_id))
        
        # Delete action
        delete_action = menu.addAction("🗑️ Delete")
        delete_action.triggered.connect(lambda: self.delete_template_by_id(template_id))
        
        # Preview action
        preview_action = menu.addAction("👁️ Preview")
        preview_action.triggered.connect(lambda: self.preview_template_by_id(template_id))
        
        # Show menu at cursor position
        menu.exec_(self.templates_table.mapToGlobal(
            self.templates_table.visualItemRect(self.templates_table.item(row, column)).bottomLeft()
        ))
    
    def edit_template_by_id(self, template_id):
        """Edit template by ID."""
        session = get_session()
        try:
            from ...models import MessageTemplate
            from sqlmodel import select
            template = session.exec(select(MessageTemplate).where(MessageTemplate.id == template_id)).first()
        finally:
            session.close()
        
        if template:
            dialog = TemplateDialog(self, template)
            if dialog.exec_() == QDialog.Accepted:
                self.load_templates()
    
    def delete_template_by_id(self, template_id):
        """Delete template by ID."""
        session = get_session()
        try:
            from ...models import MessageTemplate
            from sqlmodel import select
            template = session.exec(select(MessageTemplate).where(MessageTemplate.id == template_id)).first()
        finally:
            session.close()
        
        if template:
            reply = QMessageBox.question(
                self, 
                "Delete Template", 
                f"Are you sure you want to delete template '{template.name}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                try:
                    template.soft_delete()
                    session.commit()
                    self.logger.info(f"Template deleted: {template.name}")
                    self.load_templates()
                except Exception as e:
                    self.logger.error(f"Error deleting template: {e}")
                    QMessageBox.critical(self, "Error", f"Failed to delete template: {e}")
    
    def preview_template_by_id(self, template_id):
        """Preview template by ID."""
        session = get_session()
        try:
            from ...models import MessageTemplate
            from sqlmodel import select
            template = session.exec(select(MessageTemplate).where(MessageTemplate.id == template_id)).first()
        finally:
            session.close()
        
        if template:
            preview_text = f"Template: {template.name}\n\n"
            preview_text += f"Description: {template.description or 'No description'}\n\n"
            preview_text += f"Message Text:\n{template.body}\n\n"
            preview_text += f"Spintax: {'Yes' if template.use_spintax else 'No'}\n"
            if template.use_spintax and template.spintax_text:
                preview_text += f"Spintax Example: {template.spintax_text}\n"
            preview_text += f"Tags: {', '.join(template.get_tags_list()) if template.get_tags_list() else 'No tags'}"
            
            QMessageBox.information(self, f"Template Preview - {template.name}", preview_text)
    
    def on_selection_changed(self):
        """Handle selection change."""
        selected_rows = self.templates_table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0
        
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        
        if has_selection:
            row = selected_rows[0].row()
            # Try to get template ID from the first column (Name column)
            name_item = self.templates_table.item(row, 0)
            if name_item:
                template_id = name_item.data(Qt.UserRole)
                if template_id is not None:
                    # Emit signal with template ID for further processing
                    self.template_selected.emit(template_id)
                else:
                    self.logger.warning(f"No template ID found for row {row}")
            else:
                self.logger.warning(f"No name item found for row {row}")
    
    def add_template(self):
        """Add new template."""
        dialog = TemplateDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_templates()
    
    def edit_template(self):
        """Edit selected template."""
        selected_rows = self.templates_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        template_id = self.templates_table.item(row, 0).data(Qt.UserRole)
        
        # Load template from database
        session = get_session()
        try:
            from ...models import MessageTemplate
            from sqlmodel import select
            template = session.exec(select(MessageTemplate).where(MessageTemplate.id == template_id)).first()
        finally:
            session.close()
        
        if template:
            dialog = TemplateDialog(self, template)
            if dialog.exec_() == QDialog.Accepted:
                self.load_templates()
    
    def delete_template(self):
        """Delete selected template."""
        selected_rows = self.templates_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        template_name = self.templates_table.item(row, 0).text()
        template_id = self.templates_table.item(row, 0).data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self, 
            "Delete Template", 
            f"Are you sure you want to delete template '{template_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                session = get_session()
                try:
                    from ...models import MessageTemplate
                    from sqlmodel import select
                    template = session.exec(select(MessageTemplate).where(MessageTemplate.id == template_id)).first()
                    if template:
                        template.soft_delete()
                        session.commit()
                finally:
                    session.close()
                
                self.logger.info(f"Template deleted: {template_name}")
                self.load_templates()
                
            except Exception as e:
                self.logger.error(f"Error deleting template: {e}")
                QMessageBox.critical(self, "Error", f"Failed to delete template: {e}")


class TemplateWidget(QWidget):
    """Main template management widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        
        # Template list
        self.template_list = TemplateListWidget()
        layout.addWidget(self.template_list)
        
        # Connect signals
        self.template_list.template_selected.connect(self.on_template_selected)
        self.template_list.template_updated.connect(self.on_template_updated)
    
    def on_template_selected(self, template_id):
        """Handle template selection."""
        # This could show template details in a side panel
        pass
    
    def on_template_updated(self, template_id):
        """Handle template update."""
        # Refresh the list
        self.template_list.refresh_templates()
