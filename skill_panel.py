from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QComboBox
from PyQt5.QtCore import Qt
from upgrade import Upgrade  # Import Upgrade to access upgrade types

class SkillPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Upgrade")
        self.setFixedSize(300, 200)  # Adjust panel size
        # Ensure background covers entire panel
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("""
                    SkillPanel {
                        background-color: white; 
                        border: 1px solid black;
                    }
                """)
        # Layout
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(10, 10, 10, 10)  # Ensure padding inside panel
        self.setLayout(self.layout)

        # Labels and Inputs
        self.name_label = QLabel("Upgrade Name:")
        self.name_input = QLineEdit()

        self.desc_label = QLabel("Upgrade Description:")
        self.desc_input = QTextEdit()

        self.type_label = QLabel("Upgrade Type:")
        self.type_dropdown = QComboBox()
        self.type_dropdown.addItems([
            Upgrade.Upgrade_Type.WEAPON_UNLOCK,
            Upgrade.Upgrade_Type.CLASS_UNLOCK,
            Upgrade.Upgrade_Type.ACTIVE_ABILITY,
            Upgrade.Upgrade_Type.PASSIVE_ABILITY
        ])
        # Save Button
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_changes)

        # Add widgets to layout
        self.layout.addWidget(self.name_label)
        self.layout.addWidget(self.name_input)
        self.layout.addWidget(self.desc_label)
        self.layout.addWidget(self.desc_input)
        self.layout.addWidget(self.type_label)
        self.layout.addWidget(self.type_dropdown)
        self.layout.addWidget(self.save_button)

        self.current_node = None  # Track selected SkillNode

    def load_node(self, node):
        self.current_node = node
        self.name_input.setText(node.upgrade.name)
        self.desc_input.setText(node.upgrade.description)
        # Set dropdown to match current upgrade type
        index = self.type_dropdown.findText(node.upgrade.upgrade_type)
        if index != -1:
            self.type_dropdown.setCurrentIndex(index)
        self.show()  # Show the panel

    def save_changes(self):
        if self.current_node:
            self.current_node.upgrade.name = self.name_input.text()
            self.current_node.upgrade.description = self.desc_input.toPlainText()
            new_type = self.type_dropdown.currentText()
            self.current_node.change_upgrade_type(new_type)
            print(f"Saved Upgrade: {self.current_node.upgrade.name}, {self.current_node.upgrade.description}")

        self.hide_panel()

    def hide_panel(self):
        self.hide()
