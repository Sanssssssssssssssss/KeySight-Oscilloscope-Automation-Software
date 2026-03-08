from __future__ import annotations

import json
import os
import time

import openpyxl
from matplotlib import pyplot as plt
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from keysight_software import config
from keysight_software.paths import script_package_config_path
from keysight_software.qt_app.state import AppState
from keysight_software.qt_app.widgets import create_card, create_inline_status, create_log
from keysight_software.utils.waveform import (
    build_measurement_row,
    collect_channel_measurements,
    collect_shared_measurements,
    get_selected_measurement_headers,
    write_waveforms_to_csv,
)


class RunScriptPage(QWidget):
    def __init__(self, state: AppState):
        super().__init__()
        self.state = state
        self.connection_badge: QLabel | None = None
        self.connection_hint: QLabel | None = None
        self.path_input = QLineEdit()
        self.sequence_list = QListWidget()
        self.status_log = create_log(240)
        self.script_data: dict = {}
        self.build_ui()
        self.state.changed.connect(self.refresh_from_state)
        self.refresh_from_state()

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        picker, picker_layout = create_card("Script runner", "Pick a saved automation sequence, preview the module order, and execute it against the instrument.")
        status_shell, self.connection_badge = create_inline_status("Connection", "Disconnected", "warn")
        self.connection_hint = QLabel()
        self.connection_hint.setObjectName("MutedBody")
        self.connection_hint.setWordWrap(True)
        picker_layout.addWidget(status_shell)
        picker_layout.addWidget(self.connection_hint)
        label = QLabel("Sequence path")
        label.setObjectName("MetricLabel")
        picker_layout.addWidget(label)
        picker_layout.addWidget(self.path_input)
        actions = QHBoxLayout()
        browse = QPushButton("Browse Script Folder")
        browse.setObjectName("GhostButton")
        browse.clicked.connect(self.browse_script)
        run = QPushButton("Run Script")
        run.setObjectName("PrimaryButton")
        run.clicked.connect(self.run_script)
        actions.addWidget(browse)
        actions.addWidget(run)
        actions.addStretch(1)
        picker_layout.addLayout(actions)
        root.addWidget(picker)

        sequence_card, sequence_layout = create_card("Script sequence", "Modules in the selected package.")
        self.sequence_list.setMinimumHeight(180)
        sequence_layout.addWidget(self.sequence_list)
        root.addWidget(sequence_card)

        status_card, status_layout = create_card("Execution status", "Live execution and skip reasons appear here.")
        status_layout.addWidget(self.status_log)
        root.addWidget(status_card)

    def log(self, message: str):
        self.status_log.appendPlainText(message)

    def refresh_from_state(self):
        snapshot = self.state.snapshot()
        self.connection_badge.setText(snapshot.label)
        self.connection_badge.setProperty("status", "ok" if snapshot.connected else "warn")
        self.connection_badge.style().unpolish(self.connection_badge)
        self.connection_badge.style().polish(self.connection_badge)
        self.connection_hint.setText(snapshot.summary)

    def browse_script(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Script Package")
        if not directory:
            return
        sequence_path = os.path.join(directory, "sequence.json")
        if not os.path.exists(sequence_path):
            QMessageBox.critical(self, "File Not Found", "sequence.json not found in the selected directory.")
            return
        self.load_script(sequence_path)

    def load_script(self, filepath: str):
        self.sequence_list.clear()
        self.path_input.setText(filepath)
        with open(filepath, "r", encoding="utf-8") as handle:
            self.script_data = json.load(handle)
        for index, module in enumerate(self.script_data.get("modules", []), start=1):
            suffix = ""
            if module.get("type") == "Delay":
                suffix = f" ({module.get('delay', 1.0):.2f}s)"
            self.sequence_list.addItem(f"{index:02d}. {module.get('type', 'Unknown')}{suffix}")

    def run_script(self):
        self.status_log.clear()
        script_path = self.path_input.text().strip()
        if not script_path:
            QMessageBox.warning(self, "Running Error", "Please select a script first.")
            return
        try:
            if not self.script_data:
                self.load_script(script_path)
            for module in self.script_data.get("modules", []):
                module_type = module.get("type")
                self.log(f"Running: {module_type}")
                QApplication.processEvents()
                if module_type == "Delay":
                    delay_time = float(module.get("delay", 1.0))
                    self.log(f"Waiting for {delay_time} seconds...")
                    QApplication.processEvents()
                    time.sleep(delay_time)
                elif module_type == "Wave Cap":
                    self.execute_waveform_capture()
                elif module_type == "Axis Control":
                    self.execute_axis_control()
                self.log(f"{module_type} completed")
                self.log("")
            QMessageBox.information(self, "Execution Complete", "The script has been successfully executed.")
        except Exception as error:
            QMessageBox.critical(self, "Execution Error", f"An error occurred while running the script: {error}")

    def execute_waveform_capture(self):
        if not self.state.connected or self.state.oscilloscope is None or self.state.measure is None:
            self.log("Oscilloscope is not connected. Waveform module skipped.")
            return
        try:
            package_dir = os.path.dirname(self.path_input.text().strip())
            waveform_config_path = script_package_config_path(package_dir, "waveform_config.json")
            measurement_config_path = script_package_config_path(package_dir, "measurement_config.json")
            with open(waveform_config_path, "r", encoding="utf-8") as handle:
                waveform_config = json.load(handle)
            selected_measurements = waveform_config.get("measurements", {})
            if os.path.exists(measurement_config_path):
                with open(measurement_config_path, "r", encoding="utf-8") as handle:
                    measurement_config = json.load(handle)
                selected_measurements = measurement_config.get("selected_measurements", selected_measurements)
                phase_channels = [
                    int(measurement_config.get("selected_channel_1", 1)),
                    int(measurement_config.get("selected_channel_2", 2)),
                ]
            else:
                phase_channels = [1, 2]

            save_dir = waveform_config.get("save_directory") or config.BASE_DIRECTORY
            file_name = waveform_config.get("file_name") or f"script_run_{time.strftime('%Y%m%d_%H%M%S')}"
            full_save_dir = os.path.join(save_dir, file_name)
            os.makedirs(full_save_dir, exist_ok=True)

            selected_channels = [
                index + 1
                for index, enabled in enumerate(waveform_config.get("channels", []))
                if enabled == 1
            ]
            if not selected_channels:
                self.log("No channels selected in the waveform configuration.")
                return

            waveforms = {}
            for channel in selected_channels:
                waveforms[channel] = self.state.oscilloscope.capture_waveform(channel)

            save_options = waveform_config.get("save_options", [1, 1, 1, 1])
            if save_options[0]:
                screenshot_path = os.path.join(full_save_dir, f"{file_name}_screenshot.png")
                self.state.oscilloscope.capture_screenshot(screenshot_path)
                self.log(f"Screenshot saved at {screenshot_path}")
            if save_options[1]:
                figure = plt.figure(figsize=(8, 4), dpi=100)
                axis = figure.add_subplot(111)
                self.state.oscilloscope.plot_all_waveforms(waveforms, axis, None)
                figure_path = os.path.join(full_save_dir, f"{file_name}_waveform_plot.png")
                figure.savefig(figure_path)
                plt.close(figure)
                self.log(f"Waveform plot saved at {figure_path}")
            if save_options[2]:
                csv_path = os.path.join(full_save_dir, f"{file_name}_waveform_data.csv")
                write_waveforms_to_csv(csv_path, waveforms)
                self.log(f"Waveform data saved at {csv_path}")
            if save_options[3]:
                shared = collect_shared_measurements(
                    self.state.measure,
                    selected_measurements,
                    phase_channels[0],
                    phase_channels[1],
                )
                workbook = openpyxl.Workbook()
                sheet = workbook.active
                sheet.title = "Measurements"
                headers = ["Channel"] + get_selected_measurement_headers(selected_measurements)
                sheet.append(headers)
                for channel in selected_channels:
                    channel_measurements = collect_channel_measurements(
                        self.state.measure,
                        selected_measurements,
                        channel,
                    )
                    row = build_measurement_row(channel, selected_measurements, channel_measurements, shared)
                    sheet.append(row)
                excel_path = os.path.join(full_save_dir, f"{file_name}_measurements.xlsx")
                workbook.save(excel_path)
                self.log(f"Measurements saved at {excel_path}")
            self.log("Waveform Capture completed.")
        except Exception as error:
            self.log(f"Waveform Capture failed: {error}")

    def execute_axis_control(self):
        if not self.state.connected or self.state.oscilloscope is None:
            self.log("Oscilloscope is not connected. Axis Control skipped.")
            return
        try:
            package_dir = os.path.dirname(self.path_input.text().strip())
            axis_config_path = script_package_config_path(package_dir, "axis_config.json")
            with open(axis_config_path, "r", encoding="utf-8") as handle:
                axis_config = json.load(handle)

            timebase = axis_config.get("timebase", {})
            self.state.oscilloscope.set_timebase_scale(timebase.get("scale", 0.01))
            self.state.oscilloscope.set_timebase_position(timebase.get("position", 0.0))
            self.log(f"Timebase set to scale: {timebase.get('scale')}, position: {timebase.get('position')}")

            for channel, settings in axis_config.get("channels", axis_config.get("channel_settings", {})).items():
                channel_num = int(channel.split("_")[-1])
                self.state.oscilloscope.set_channel_scale(channel_num, settings.get("scale", 1.0))
                self.state.oscilloscope.set_channel_position(channel_num, settings.get("position", 0.0))
                self.log(f"Channel {channel_num} set to scale: {settings.get('scale')}, position: {settings.get('position')}")

            for index, marker in enumerate(axis_config.get("markers", axis_config.get("marker_positions", []))):
                x_value = marker.get("x", 0.0)
                y_value = marker.get("y", 0.0)
                if index == 0:
                    self.state.oscilloscope.add_marker_x1(x_value)
                    self.state.oscilloscope.add_marker_y1(y_value)
                elif index == 1:
                    self.state.oscilloscope.add_marker_x2(x_value)
                    self.state.oscilloscope.add_marker_y2(y_value)
                self.log(f"Marker {index + 1} set to x: {x_value}, y: {y_value}")

            self.log("Axis Control completed.")
        except Exception as error:
            self.log(f"Axis Control failed: {error}")
