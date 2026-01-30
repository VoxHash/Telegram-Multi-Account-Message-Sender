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
from ...services import get_logger
from ...services.db import get_session
from ...services.translation import _, get_translation_manager
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
        self.setWindowTitle(_("templates.add_template") if not self.template else _("templates.edit_template"))
        self.setModal(True)
        self.resize(600, 500)
        
        # Enable help button
        self.setWindowFlags(self.windowFlags() | Qt.WindowContextHelpButtonHint)
        
        layout = QVBoxLayout(self)
        
        # Basic Information
        basic_group = QGroupBox(_("templates.basic_information"))
        basic_layout = QFormLayout(basic_group)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(_("templates.template_name_placeholder"))
        basic_layout.addRow(_("common.name") + ":", self.name_edit)
        
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText(_("templates.template_description_placeholder"))
        basic_layout.addRow(_("common.description") + ":", self.description_edit)
        
        layout.addWidget(basic_group)
        
        # Message Content
        message_group = QGroupBox(_("templates.message_content"))
        message_layout = QVBoxLayout(message_group)
        
        # Message text
        message_layout.addWidget(QLabel(_("common.message_text") + ":"))
        self.message_edit = QTextEdit()
        self.message_edit.setPlaceholderText(_("templates.message_template_placeholder"))
        self.message_edit.setMinimumHeight(150)
        message_layout.addWidget(self.message_edit)
        
        # Variables help
        variables_help = QLabel(_("templates.available_variables"))
        variables_help.setStyleSheet("color: #888888; font-style: italic;")
        message_layout.addWidget(variables_help)
        
        # Variables vs Spintax explanation
        explanation = QLabel(_("templates.variables_explanation"))
        explanation.setStyleSheet("color: #4CAF50; font-weight: bold; padding: 8px; background-color: #1a1a1a; border: 1px solid #4CAF50; border-radius: 4px;")
        explanation.setWordWrap(True)
        message_layout.addWidget(explanation)
        
        layout.addWidget(message_group)
        
        # Spintax Settings
        spintax_group = QGroupBox(_("templates.spintax_settings"))
        spintax_layout = QFormLayout(spintax_group)
        
        self.use_spintax_check = QCheckBox(_("templates.enable_spintax"))
        self.use_spintax_check.toggled.connect(self.toggle_spintax_settings)
        spintax_layout.addRow(self.use_spintax_check)
        
        self.spintax_example_edit = QLineEdit()
        self.spintax_example_edit.setPlaceholderText(_("templates.spintax_example_placeholder"))
        spintax_layout.addRow(_("templates.spintax_example") + ":", self.spintax_example_edit)
        
        # Spintax preview button
        self.preview_spintax_button = QPushButton(_("templates.preview_spintax"))
        self.preview_spintax_button.clicked.connect(self.preview_spintax)
        self.preview_spintax_button.setEnabled(False)
        spintax_layout.addRow("", self.preview_spintax_button)
        
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
    
    def event(self, event):
        """Handle events including help button clicks."""
        if event.type() == event.EnterWhatsThisMode:
            self.show_help()
            return True
        return super().event(event)
    
    def show_help(self):
        """Show help dialog."""
        help_text = """
        <h3>Template Creation Help</h3>
        
        <h4>Basic Information:</h4>
        <ul>
        <li><b>Name:</b> A unique identifier for your template</li>
        <li><b>Description:</b> Brief description of the template's purpose</li>
        </ul>
        
        <h4>Message Content:</h4>
        <ul>
        <li><b>Message Text:</b> Your main message template</li>
        <li><b>Variables:</b> Use {name}, {email}, {phone}, {company}, {date}, {time} for personalization</li>
        </ul>
        
        <h4>⚠️ IMPORTANT: Variables vs Spintax</h4>
        <p><b>VARIABLES</b> (for personalization - what you probably want):</p>
        <ul>
        <li>{name}, {email}, {company} - Replaced with actual values</li>
        <li>Example: "Hello {name}!" becomes "Hello John!"</li>
        </ul>
        
        <p><b>SPINTAX PATTERNS</b> (for variations - random text selection):</p>
        <ul>
        <li>{option1|option2|option3} - Creates random variations</li>
        <li>Example: "Hello {friend|buddy|pal}!" becomes "Hello friend!" or "Hello buddy!"</li>
        </ul>
        
        <h4>Spintax Settings:</h4>
        <ul>
        <li><b>Enable Spintax:</b> Check to enable message variations</li>
        <li><b>Spintax Example:</b> Use {option1|option2|option3} syntax for variations</li>
        <li><b>Example:</b> Hello {friend|buddy|pal}, welcome to {our company|our service}!</li>
        </ul>
        
        <h4>Tags:</h4>
        <ul>
        <li>Comma-separated keywords for organizing templates</li>
        <li>Example: welcome, onboarding, marketing</li>
        </ul>
        
        <h4>Spintax Syntax:</h4>
        <ul>
        <li>Use {option1|option2|option3} for random selection</li>
        <li>Nested spintax: {Hello {name|friend}|Hi {buddy|pal}}</li>
        <li>Empty options: {|option1|option2} (includes empty string)</li>
        </ul>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle(_("templates.help"))
        msg.setTextFormat(Qt.RichText)
        msg.setText(help_text)
        msg.setIcon(QMessageBox.Information)
        msg.exec_()
    
    def toggle_spintax_settings(self, enabled: bool):
        """Toggle spintax settings visibility."""
        self.spintax_example_edit.setEnabled(enabled)
        self.preview_spintax_button.setEnabled(enabled)
        
        # If enabling spintax, validate the current message for spintax syntax
        if enabled:
            # Set a helpful example if the field is empty
            if not self.spintax_example_edit.text().strip():
                self.spintax_example_edit.setText("Hello {name|friend|buddy}, welcome to {our company|our service}!")
            self.validate_spintax_syntax()
    
    def validate_spintax_syntax(self):
        """Validate spintax syntax in the message."""
        message_text = self.message_edit.toPlainText()
        if not message_text.strip():
            return True
        
        try:
            # Validate spintax syntax
            validation_result = self.spintax_processor.validate_spintax(message_text)
            
            if validation_result["patterns_count"] == 0:
                # Check if message contains variables but no spintax patterns
                message_text = self.message_edit.toPlainText()
                has_variables = any(var in message_text for var in ['{name}', '{email}', '{phone}', '{company}', '{date}', '{time}'])
                
                if has_variables:
                    # Message has variables but no spintax patterns
                    QMessageBox.information(
                        self, _("templates.spintax_validation"),
                        _("templates.variables_help") + "\n\n"
                        "VARIABLES (what you have):\n"
                        "• {name}, {email}, {company} - These are replaced with actual values\n"
                        "• Example: 'Hello {name}!' becomes 'Hello John!'\n\n"
                        "SPINTAX PATTERNS (for variations):\n"
                        "• {option1|option2|option3} - Creates random variations\n"
                        "• Example: 'Hello {friend|buddy|pal}!' becomes 'Hello friend!' or 'Hello buddy!'\n\n"
                        "To create message variations, change your variables to spintax:\n"
                        "• Instead of: 'Hello {name}!'\n"
                        "• Use: 'Hello {friend|buddy|pal}!'\n\n"
                        "Your current message will be sent as-is with variables replaced."
                    )
                else:
                    # No variables or spintax patterns
                    QMessageBox.information(
                        self, _("templates.spintax_validation"),
                        _("templates.no_patterns_found") + "\n\n"
                        "To use spintax, add patterns like:\n"
                        "• {option1|option2|option3}\n"
                        "• Hello {name|friend|buddy}\n"
                        "• Get {20%|25%|30%} off\n\n"
                        "The message will be sent as-is without variations."
                    )
                return True
            
            if not validation_result["valid"]:
                error_msg = "Invalid spintax syntax:\n\n" + "\n".join(validation_result["errors"])
                QMessageBox.warning(
                    self, _("templates.spintax_validation"),
                    f"{error_msg}\n\n{_('templates.spintax_help')}"
                )
                return False
            return True
        except Exception as e:
            QMessageBox.warning(
                self, _("templates.spintax_validation"),
                f"Error validating spintax syntax:\n\n{str(e)}\n\n"
                "Please check your spintax syntax. Use {{option1|option2|option3}} format."
            )
            return False
    
    def preview_spintax(self):
        """Preview spintax generation."""
        message_text = self.message_edit.toPlainText()
        if not message_text.strip():
            QMessageBox.warning(self, _("templates.spintax_preview"), _("templates.no_message_text"))
            return
        
        try:
            # Check if text contains spintax patterns
            validation_result = self.spintax_processor.validate_spintax(message_text)
            
            if validation_result["patterns_count"] == 0:
                # Check if message contains variables but no spintax patterns
                has_variables = any(var in message_text for var in ['{name}', '{email}', '{phone}', '{company}', '{date}', '{time}'])
                
                if has_variables:
                    # Message has variables but no spintax patterns
                    QMessageBox.information(
                        self, _("templates.spintax_preview"),
                        _("templates.variables_help") + "\n\n"
                        "VARIABLES (what you have):\n"
                        "• {name}, {email}, {company} - These are replaced with actual values\n"
                        "• Example: 'Hello {name}!' becomes 'Hello John!'\n\n"
                        "SPINTAX PATTERNS (for variations):\n"
                        "• {option1|option2|option3} - Creates random variations\n"
                        "• Example: 'Hello {friend|buddy|pal}!' becomes 'Hello friend!' or 'Hello buddy!'\n\n"
                        "To create message variations, change your variables to spintax:\n"
                        "• Instead of: 'Hello {name}!'\n"
                        "• Use: 'Hello {friend|buddy|pal}!'\n\n"
                        "Current message:\n" + message_text
                    )
                else:
                    # No variables or spintax patterns
                    QMessageBox.information(
                        self, _("templates.spintax_preview"),
                        _("templates.no_patterns_found") + "\n\n"
                        "To use spintax, add patterns like:\n"
                        "• {option1|option2|option3}\n"
                        "• Hello {name|friend|buddy}\n"
                        "• Get {20%|25%|30%} off\n\n"
                        "Current message:\n" + message_text
                    )
                return
            
            # Generate multiple variations using the correct method
            variations = self.spintax_processor.get_preview_samples(message_text, count=5)
            
            # Check if all variations are the same (no actual spintax)
            unique_variations = list(set(variations))
            if len(unique_variations) == 1:
                QMessageBox.information(
                    self, _("templates.spintax_preview"),
                    "No variations generated. This might be because:\n\n"
                    "• Spintax patterns are malformed\n"
                    "• All options in patterns are identical\n"
                    "• Nested spintax is not supported\n\n"
                    "Original message:\n" + message_text
                )
                return
            
            preview_text = f"Spintax Preview ({len(unique_variations)} unique variations):\n\n"
            for i, variation in enumerate(variations, 1):
                preview_text += f"Variation {i}: {variation}\n\n"
            
            msg = QMessageBox(self)
            msg.setWindowTitle(_("templates.spintax_preview"))
            msg.setText(preview_text)
            msg.setIcon(QMessageBox.Information)
            msg.exec_()
            
        except Exception as e:
            QMessageBox.warning(
                self, _("templates.spintax_preview"),
                f"Error generating spintax preview:\n\n{str(e)}\n\n"
                "Please check your spintax syntax."
            )
    
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
                QMessageBox.warning(self, _("common.error"), _("templates.name_required"))
                return
            
            if not self.message_edit.toPlainText().strip():
                QMessageBox.warning(self, _("common.error"), _("templates.message_required"))
                return
            
            # Validate spintax if enabled
            if self.use_spintax_check.isChecked():
                if not self.validate_spintax_syntax():
                    return
                
                # Validate spintax example if provided
                spintax_example = self.spintax_example_edit.text().strip()
                if spintax_example:
                    try:
                        validation_result = self.spintax_processor.validate_spintax(spintax_example)
                        if not validation_result["valid"]:
                            error_msg = "Invalid spintax syntax in example:\n\n" + "\n".join(validation_result["errors"])
                            QMessageBox.warning(
                                self, _("templates.spintax_validation"),
                                f"{error_msg}\n\n{_('templates.spintax_help')}"
                            )
                            return
                    except Exception as e:
                        QMessageBox.warning(
                            self, _("templates.spintax_validation"),
                            f"Error validating spintax example:\n\n{str(e)}\n\n"
                            "Please check your spintax syntax. Use {{option1|option2|option3}} format."
                        )
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
        self.translation_manager = get_translation_manager()
        
        # Connect language change signal
        self.translation_manager.language_changed.connect(self.on_language_changed)
        
        self.setup_ui()
        self.load_templates()
        
    
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
        
        self.import_button = QPushButton("Import CSV")
        self.import_button.clicked.connect(self.import_csv)
        header_layout.addWidget(self.import_button)
        
        self.export_button = QPushButton("Export CSV")
        self.export_button.clicked.connect(self.export_csv)
        header_layout.addWidget(self.export_button)
        
        self.edit_button = QPushButton("Edit Template")
        self.edit_button.clicked.connect(self.edit_template)
        self.edit_button.setEnabled(False)
        header_layout.addWidget(self.edit_button)
        
        self.delete_button = QPushButton("Delete Template")
        self.delete_button.clicked.connect(self.delete_template)
        self.delete_button.setEnabled(False)
        header_layout.addWidget(self.delete_button)
        
        layout.addLayout(header_layout)
        
        # Search field
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        search_label.setStyleSheet("color: white; font-weight: bold;")
        search_layout.addWidget(search_label)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search templates by name, description, tags, or content...")
        self.search_edit.textChanged.connect(self.filter_templates)
        self.search_edit.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #404040;
                border-radius: 4px;
                background-color: #2d2d2d;
                color: white;
            }
            QLineEdit:focus {
                border-color: #0078d4;
            }
        """)
        search_layout.addWidget(self.search_edit)
        search_layout.addStretch()
        
        layout.addLayout(search_layout)
        
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
            
            # Apply search filter if there's search text
            self.filter_templates()
            
        except Exception as e:
            self.logger.error(f"Error loading templates: {e}")
            self.status_label.setText(f"Error loading templates: {e}")
    
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
    
    def import_csv(self):
        """Import templates from CSV file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Templates from CSV", "", "CSV Files (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            import pandas as pd
            
            # Read CSV file
            df = pd.read_csv(file_path)
            
            # Validate required columns
            required_columns = ['name', 'description', 'body']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                QMessageBox.warning(
                    self, "Invalid CSV", 
                    f"Missing required columns: {', '.join(missing_columns)}\n"
                    f"Required columns: {', '.join(required_columns)}"
                )
                return
            
            # Import templates
            session = get_session()
            imported_count = 0
            
            try:
                for _, row in df.iterrows():
                    # Check if template already exists
                    existing = session.query(MessageTemplate).filter(
                        MessageTemplate.name == row['name']
                    ).first()
                    
                    if existing:
                        self.logger.warning(f"Template '{row['name']}' already exists, skipping")
                        continue
                    
                    # Create new template
                    template = MessageTemplate(
                        name=row['name'],
                        description=row.get('description', ''),
                        body=row['body'],
                        use_spintax=row.get('use_spintax', False),
                        spintax_text=row.get('spintax_text', ''),
                        category=row.get('category', 'general'),
                        is_active=row.get('is_active', True)
                    )
                    
                    # Handle tags
                    if 'tags' in row and pd.notna(row['tags']):
                        tags = [tag.strip() for tag in str(row['tags']).split(',') if tag.strip()]
                        template.set_tags_list(tags)
                    
                    session.add(template)
                    imported_count += 1
                
                session.commit()
                self.logger.info(f"Imported {imported_count} templates from CSV")
                QMessageBox.information(
                    self, "Import Successful", 
                    f"Successfully imported {imported_count} templates from CSV file."
                )
                self.load_templates()
                
            finally:
                session.close()
                
        except Exception as e:
            self.logger.error(f"Error importing CSV: {e}")
            QMessageBox.critical(self, "Import Error", f"Failed to import CSV: {e}")
    
    def export_csv(self):
        """Export templates to CSV file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Templates to CSV", "templates.csv", "CSV Files (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            import pandas as pd
            
            # Get all templates
            session = get_session()
            try:
                templates = session.query(MessageTemplate).filter(
                    MessageTemplate.deleted_at.is_(None)
                ).all()
                
                if not templates:
                    QMessageBox.information(self, "No Data", "No templates to export.")
                    return
                
                # Prepare data for export
                data = []
                for template in templates:
                    data.append({
                        'name': template.name,
                        'description': template.description or '',
                        'body': template.body,
                        'use_spintax': template.use_spintax,
                        'spintax_text': template.spintax_text or '',
                        'category': template.category,
                        'is_active': template.is_active,
                        'tags': ', '.join(template.get_tags_list()) if template.get_tags_list() else '',
                        'created_at': template.created_at.isoformat() if template.created_at else '',
                        'updated_at': template.updated_at.isoformat() if template.updated_at else ''
                    })
                
                # Create DataFrame and export
                df = pd.DataFrame(data)
                df.to_csv(file_path, index=False)
                
                self.logger.info(f"Exported {len(templates)} templates to CSV")
                QMessageBox.information(
                    self, "Export Successful", 
                    f"Successfully exported {len(templates)} templates to CSV file."
                )
                
            finally:
                session.close()
                
        except Exception as e:
            self.logger.error(f"Error exporting CSV: {e}")
            QMessageBox.critical(self, "Export Error", f"Failed to export CSV: {e}")
    
    def filter_templates(self):
        """Filter templates based on search text."""
        search_text = self.search_edit.text().lower().strip()
        
        if not search_text:
            # Show all templates
            for row in range(self.templates_table.rowCount()):
                self.templates_table.setRowHidden(row, False)
            return
        
        # Filter templates (exclude Actions column - column 5)
        for row in range(self.templates_table.rowCount()):
            should_show = False
            
            # Check all columns except Actions column for search text
            for col in range(self.templates_table.columnCount() - 1):  # Exclude last column (Actions)
                item = self.templates_table.item(row, col)
                if item and search_text in item.text().lower():
                    should_show = True
                    break
            
            self.templates_table.setRowHidden(row, not should_show)
    
    def on_language_changed(self, language: str):
        """Handle language change."""
        self.logger.info(f"Language changed to: {language}")
        # Recreate the UI with new translations
        self.setup_ui()
        self.load_templates()


class TemplateWidget(QWidget):
    """Main template management widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.translation_manager = get_translation_manager()
        
        # Connect language change signal
        self.translation_manager.language_changed.connect(self.on_language_changed)
        
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
        self.template_list.load_templates()
    
    def on_language_changed(self, language: str):
        """Handle language change."""
        self.logger.info(f"Language changed to: {language}")
        # The template_list widget will handle its own language change
        # No need to recreate the UI since it only contains the template_list
