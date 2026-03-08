from __future__ import annotations

import os

from PySide6.QtWidgets import QFileDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from keysight_software import config
from keysight_software.paths import project_path
from keysight_software.qt_app.widgets import create_card, create_log


CONFIG_FILE = project_path("config.txt")


class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.save_directory_input = QLineEdit()
        self.base_directory_input = QLineEdit(config.BASE_DIRECTORY)
        self.base_filename_input = QLineEdit(config.BASE_FILENAME)
        self.visa_input = QLineEdit(config.VISA_ADDRESS)
        self.timeout_input = QLineEdit(str(config.GLOBAL_TIMEOUT))
        self.log_output = create_log(180)
        self.build_ui()
        self.load_settings()

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        card, layout = create_card("Workspace settings", "Adjust default directories, naming, and runtime instrument preferences.")
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        fields = [
            ("Export save directory", self.save_directory_input),
            ("Base output directory", self.base_directory_input),
            ("Base file name", self.base_filename_input),
            ("Default VISA address", self.visa_input),
            ("Global timeout (ms)", self.timeout_input),
        ]
        for row, (label_text, widget) in enumerate(fields):
            label = QLabel(label_text)
            label.setObjectName("MetricLabel")
            grid.addWidget(label, row * 2, 0, 1, 2)
            grid.addWidget(widget, row * 2 + 1, 0, 1, 2)

        actions = QHBoxLayout()
        browse = QPushButton("Browse Folder")
        browse.setObjectName("GhostButton")
        browse.clicked.connect(self.browse_directory)
        save = QPushButton("Save Settings")
        save.setObjectName("PrimaryButton")
        save.clicked.connect(self.save_settings)
        actions.addWidget(browse)
        actions.addWidget(save)
        actions.addStretch(1)
        layout.addLayout(grid)
        layout.addLayout(actions)
        root.addWidget(card)

        log_card, log_layout = create_card("Settings activity", "Persistence and validation feedback appears here.")
        log_layout.addWidget(self.log_output)
        root.addWidget(log_card)

    def log(self, message: str):
        self.log_output.appendPlainText(message)

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Save Directory", self.save_directory_input.text().strip())
        if directory:
            self.save_directory_input.setText(directory)

    def load_settings(self):
        for encoding in ("utf-8", "gbk", "cp1252", "latin-1"):
            try:
                with open(CONFIG_FILE, "r", encoding=encoding) as handle:
                    for line in handle:
                        if line.startswith("SAVE_DIRECTORY="):
                            self.save_directory_input.setText(line.split("=", 1)[1].strip())
                            self.log(f"Loaded export save directory from {CONFIG_FILE}.")
                            return
            except (FileNotFoundError, UnicodeDecodeError):
                continue

    def save_settings(self):
        try:
            timeout = int(self.timeout_input.text().strip())
        except ValueError:
            self.log("Timeout must be an integer value in milliseconds.")
            return

        save_directory = self.save_directory_input.text().strip() or "C:/Users/Public/OscilloscopeData"
        os.makedirs(save_directory, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as handle:
            handle.write(f"SAVE_DIRECTORY={save_directory}\n")

        config.update_base_directory(self.base_directory_input.text().strip())
        config.update_base_filename(self.base_filename_input.text().strip())
        config.update_visa_address(self.visa_input.text().strip())
        config.update_global_timeout(timeout)
        self.log("Settings saved successfully.")
