from __future__ import annotations

import os
import shutil

import pandas as pd
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget

from keysight_software.qt_app.widgets import create_card, create_log


class BatchProcessPage(QWidget):
    def __init__(self):
        super().__init__()
        self.directory_input = QLineEdit()
        self.log_output = create_log(280)
        self.build_ui()

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        controls, layout = create_card("Batch merge", "Select a parent folder containing repeated run directories and merge the resulting measurement sheets.")
        label = QLabel("Main directory")
        label.setObjectName("MetricLabel")
        layout.addWidget(label)
        layout.addWidget(self.directory_input)
        actions = QHBoxLayout()
        browse = QPushButton("Browse Folder")
        browse.setObjectName("GhostButton")
        browse.clicked.connect(self.browse_directory)
        run = QPushButton("Start Batch Processing")
        run.setObjectName("PrimaryButton")
        run.clicked.connect(self.start_batch_processing)
        actions.addWidget(browse)
        actions.addWidget(run)
        actions.addStretch(1)
        layout.addLayout(actions)
        root.addWidget(controls)

        log_card, log_layout = create_card("Processing log", "Each subfolder is scanned, merged, and copied into a final consolidated output package.")
        log_layout.addWidget(self.log_output)
        root.addWidget(log_card)

    def log(self, message: str):
        self.log_output.appendPlainText(message)

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Main Directory", self.directory_input.text().strip())
        if directory:
            self.directory_input.setText(directory)
            self.log(f"Selected directory: {directory}")
            self.list_subdirectories(directory)

    def list_subdirectories(self, directory: str):
        subdirs = [
            name
            for name in os.listdir(directory)
            if os.path.isdir(os.path.join(directory, name)) and name != "Final_Process"
        ]
        if not subdirs:
            self.log("No subdirectories found.")
            return
        self.log("Loaded the following file IDs:")
        for subdir in subdirs:
            self.log(f"- {subdir}")

    def start_batch_processing(self):
        main_directory = self.directory_input.text().strip()
        if not main_directory:
            QMessageBox.warning(self, "No Directory Selected", "Please select a main directory first.")
            return

        self.log("Starting batch processing...")
        final_process_dir = os.path.join(main_directory, "Final_Process")
        os.makedirs(final_process_dir, exist_ok=True)
        merged_data = pd.DataFrame()

        for subdir in os.listdir(main_directory):
            subdir_path = os.path.join(main_directory, subdir)
            if not os.path.isdir(subdir_path) or subdir == "Final_Process":
                continue
            self.log(f"Processing {subdir}...")
            for file_path in self.find_measurement_files(subdir_path):
                data = pd.read_excel(file_path)
                if "Unnamed" in str(data.columns[0]):
                    data.rename(columns={data.columns[0]: "Channel"}, inplace=True)
                elif "Channel" not in data.columns:
                    data.insert(0, "Channel", data.columns[0])
                data.insert(0, "ID", subdir)
                merged_data = pd.concat([merged_data, data], ignore_index=True)
            if not merged_data.empty:
                self.log(f"Merged measurement data for {subdir}")

            for file_name in os.listdir(subdir_path):
                if file_name.lower().startswith("measurements"):
                    continue
                source = os.path.join(subdir_path, file_name)
                destination = os.path.join(final_process_dir, file_name)
                if os.path.isfile(source):
                    shutil.copy(source, destination)
                    self.log(f"Copied {file_name} to Final_Process")

        if not merged_data.empty:
            output = os.path.join(final_process_dir, "final_merged_measurements.xlsx")
            merged_data.to_excel(output, index=False)
            self.log(f"Final merged measurements saved at {output}")
        else:
            self.log("No measurement files found for merging.")

        self.log("Batch processing completed.")
        QMessageBox.information(self, "Process Completed", "Batch processing has been completed.")

    def find_measurement_files(self, directory: str) -> list[str]:
        measurement_files = []
        for root, _dirs, files in os.walk(directory):
            for file_name in files:
                if "measurements" in file_name.lower() and file_name.endswith(".xlsx"):
                    measurement_files.append(os.path.join(root, file_name))
        return measurement_files
