from __future__ import annotations

import json
import os

import openpyxl
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from keysight_software.paths import config_path
from keysight_software.qt_app.state import AppState
from keysight_software.qt_app.widgets import create_card, create_inline_status, create_log
from keysight_software.utils.waveform import (
    build_measurement_row,
    collect_channel_measurements,
    collect_shared_measurements,
    format_channel_measurement_lines,
    format_shared_measurement_lines,
    get_measurement_names,
    get_selected_measurement_headers,
    write_waveforms_to_csv,
)


WAVEFORM_CONFIG_FILE = config_path("waveform_config.json")
MEASUREMENT_CONFIG_FILE = config_path("measurement_config.json")


class MeasurementDialog(QDialog):
    def __init__(self, selected_measurements: dict[str, int], channel_1: int, channel_2: int, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Measurement Preset")
        self.resize(430, 520)
        self.measurement_checks: dict[str, QCheckBox] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        info = QLabel("Choose scalar measurements to calculate after each capture.")
        info.setObjectName("MutedBody")
        info.setWordWrap(True)
        root.addWidget(info)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)
        for name in get_measurement_names():
            check = QCheckBox(name)
            check.setChecked(bool(selected_measurements.get(name)))
            content_layout.addWidget(check)
            self.measurement_checks[name] = check
        content_layout.addStretch(1)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        pairs = QHBoxLayout()
        pairs.addWidget(self.make_pair_box("Phase channel A", channel_1))
        pairs.addWidget(self.make_pair_box("Phase channel B", channel_2))
        root.addLayout(pairs)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def make_pair_box(self, label_text: str, value: int):
        box = QFrame()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        label = QLabel(label_text)
        label.setObjectName("MetricLabel")
        combo = QComboBox()
        combo.addItems(["1", "2", "3", "4"])
        combo.setCurrentText(str(value))
        layout.addWidget(label)
        layout.addWidget(combo)
        if "A" in label_text:
            self.channel_1_combo = combo
        else:
            self.channel_2_combo = combo
        return box

    def result_payload(self) -> tuple[dict[str, int], int, int]:
        measurements = {name: int(check.isChecked()) for name, check in self.measurement_checks.items()}
        return measurements, int(self.channel_1_combo.currentText()), int(self.channel_2_combo.currentText())


class WaveformCapturePage(QWidget):
    def __init__(self, state: AppState):
        super().__init__()
        self.state = state
        self.connection_badge: QLabel | None = None
        self.connection_hint: QLabel | None = None
        self.capture_button: QPushButton | None = None
        self.save_button: QPushButton | None = None
        self.log_output = create_log(220)
        self.coord_label = QLabel("Cursor: -, -")
        self.coord_label.setObjectName("MutedBody")
        self.channel_checks: list[QCheckBox] = []
        self.export_checks: list[QCheckBox] = []
        self.filename_input = QLineEdit()
        self.directory_input = QLineEdit()
        self.figure = Figure(figsize=(8, 4), dpi=100)
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.selected_measurements: dict[str, int] = {}
        self.selected_channel_1 = 1
        self.selected_channel_2 = 2
        self.last_waveforms: dict[int, tuple] = {}
        self.last_channel_measurements: dict[int, dict[str, float | None]] = {}
        self.last_shared_measurements: dict[str, float | None] = {}
        self.build_ui()
        self.canvas.mpl_connect("motion_notify_event", self.on_mouse_move)
        self.load_measurement_config()
        self.load_waveform_config()
        self.state.changed.connect(self.refresh_from_state)
        self.refresh_from_state()

    def build_ui(self):
        root = QGridLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setHorizontalSpacing(14)
        root.setVerticalSpacing(14)
        root.setColumnStretch(0, 3)
        root.setColumnStretch(1, 2)

        plot_card, plot_layout = create_card("Waveform canvas", "Capture one or more channels, inspect the trace visually, and export the latest acquisition.")
        self.canvas.setMinimumHeight(380)
        plot_layout.addWidget(self.canvas)
        plot_layout.addWidget(self.coord_label)
        root.addWidget(plot_card, 0, 0, 3, 1)

        controls_card, controls_layout = create_card("Capture controls", "Choose active channels and measurement presets before triggering a new acquisition.")
        status_shell, self.connection_badge = create_inline_status("Connection", "Disconnected", "warn")
        self.connection_hint = QLabel()
        self.connection_hint.setObjectName("MutedBody")
        self.connection_hint.setWordWrap(True)
        controls_layout.addWidget(status_shell)
        controls_layout.addWidget(self.connection_hint)

        channel_row = QHBoxLayout()
        for index in range(4):
            checkbox = QCheckBox(f"CH{index + 1}")
            self.channel_checks.append(checkbox)
            channel_row.addWidget(checkbox)
        channel_row.addStretch(1)
        controls_layout.addLayout(channel_row)

        actions = QHBoxLayout()
        self.capture_button = QPushButton("Capture Waveform")
        self.capture_button.setObjectName("PrimaryButton")
        self.capture_button.clicked.connect(self.capture_waveform)
        select = QPushButton("Measurements")
        select.setObjectName("GhostButton")
        select.clicked.connect(self.open_measurement_dialog)
        actions.addWidget(self.capture_button)
        actions.addWidget(select)
        actions.addStretch(1)
        controls_layout.addLayout(actions)
        root.addWidget(controls_card, 0, 1)

        export_card, export_layout = create_card("Export", "Save screenshots, plots, waveform CSVs, and the latest calculated measurements.")
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        export_names = ["Save Screenshot", "Save Plot", "Save CSV", "Save Measurements"]
        for row, label_text in enumerate(export_names):
            check = QCheckBox(label_text)
            check.setChecked(True)
            self.export_checks.append(check)
            grid.addWidget(check, row, 0, 1, 2)

        grid.addWidget(self.label("Save Directory"), 4, 0, 1, 2)
        self.directory_input.setText("")
        grid.addWidget(self.directory_input, 5, 0)
        browse = QPushButton("Browse")
        browse.setObjectName("GhostButton")
        browse.clicked.connect(self.pick_directory)
        grid.addWidget(browse, 5, 1)

        grid.addWidget(self.label("File Name"), 6, 0, 1, 2)
        self.filename_input.setText("waveform_data")
        grid.addWidget(self.filename_input, 7, 0, 1, 2)

        self.save_button = QPushButton("Save Data")
        self.save_button.setObjectName("PrimaryButton")
        self.save_button.clicked.connect(self.save_data)
        grid.addWidget(self.save_button, 8, 0, 1, 2)
        export_layout.addLayout(grid)
        root.addWidget(export_card, 1, 1)

        log_card, log_layout = create_card("Measurement results", "Latest scalar outputs from the selected acquisition.")
        log_layout.addWidget(self.log_output)
        root.addWidget(log_card, 2, 1)

    def label(self, text: str):
        label = QLabel(text)
        label.setObjectName("MetricLabel")
        return label

    def log(self, message: str):
        self.log_output.appendPlainText(message)

    def load_measurement_config(self):
        try:
            with open(MEASUREMENT_CONFIG_FILE, "r", encoding="utf-8") as handle:
                config = json.load(handle)
        except FileNotFoundError:
            config = {}
        self.selected_measurements = config.get("selected_measurements", {})
        self.selected_channel_1 = int(config.get("selected_channel_1", 1))
        self.selected_channel_2 = int(config.get("selected_channel_2", 2))

    def save_measurement_config(self):
        payload = {
            "selected_measurements": self.selected_measurements,
            "selected_channel_1": self.selected_channel_1,
            "selected_channel_2": self.selected_channel_2,
        }
        with open(MEASUREMENT_CONFIG_FILE, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)

    def load_waveform_config(self):
        try:
            with open(WAVEFORM_CONFIG_FILE, "r", encoding="utf-8") as handle:
                config = json.load(handle)
        except FileNotFoundError:
            config = {}
        channels = config.get("channels", [0, 0, 1, 0])
        for checkbox, enabled in zip(self.channel_checks, channels):
            checkbox.setChecked(bool(enabled))
        for checkbox, enabled in zip(self.export_checks, config.get("save_options", [1, 1, 1, 1])):
            checkbox.setChecked(bool(enabled))
        self.directory_input.setText(config.get("save_directory", ""))
        self.filename_input.setText(config.get("file_name", "waveform_data"))

    def save_waveform_config(self):
        payload = {
            "channels": [int(check.isChecked()) for check in self.channel_checks],
            "measurements": self.selected_measurements,
            "save_options": [int(check.isChecked()) for check in self.export_checks],
            "save_directory": self.directory_input.text().strip(),
            "file_name": self.filename_input.text().strip(),
        }
        with open(WAVEFORM_CONFIG_FILE, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=4)

    def refresh_from_state(self):
        snapshot = self.state.snapshot()
        self.connection_badge.setText(snapshot.label)
        self.connection_badge.setProperty("status", "ok" if snapshot.connected else "warn")
        self.connection_badge.style().unpolish(self.connection_badge)
        self.connection_badge.style().polish(self.connection_badge)
        if snapshot.connected and snapshot.active_channels:
            active_text = ", ".join(f"CH{channel}" for channel in snapshot.active_channels)
            self.connection_hint.setText(f"Live acquisition is available. Active channels: {active_text}.")
        else:
            self.connection_hint.setText(snapshot.summary)
        self.capture_button.setEnabled(snapshot.connected)
        self.save_button.setEnabled(bool(self.last_waveforms))

    def open_measurement_dialog(self):
        dialog = MeasurementDialog(self.selected_measurements, self.selected_channel_1, self.selected_channel_2, self)
        if dialog.exec():
            self.selected_measurements, self.selected_channel_1, self.selected_channel_2 = dialog.result_payload()
            self.save_measurement_config()
            self.log("Updated measurement preset.")

    def pick_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory", self.directory_input.text().strip())
        if directory:
            self.directory_input.setText(directory)

    def selected_channels(self) -> list[int]:
        return [index + 1 for index, checkbox in enumerate(self.channel_checks) if checkbox.isChecked()]

    def capture_waveform(self):
        if not self.state.connected or self.state.oscilloscope is None or self.state.measure is None:
            self.log("Capture skipped because the oscilloscope is not connected.")
            return
        channels = self.selected_channels()
        if not channels:
            QMessageBox.warning(self, "No Channel Selected", "Please select at least one channel.")
            return

        self.log_output.clear()
        waveforms = {}
        channel_measurements = {}
        for channel in channels:
            waveforms[channel] = self.state.oscilloscope.capture_waveform(channel=channel)
            channel_measurements[channel] = collect_channel_measurements(
                self.state.measure,
                self.selected_measurements,
                channel,
            )
            for line in format_channel_measurement_lines(channel, channel_measurements[channel]):
                self.log(line)

        shared_measurements = collect_shared_measurements(
            self.state.measure,
            self.selected_measurements,
            self.selected_channel_1,
            self.selected_channel_2,
        )
        for line in format_shared_measurement_lines(
            shared_measurements,
            self.selected_channel_1,
            self.selected_channel_2,
        ):
            self.log(line)

        self.last_waveforms = waveforms
        self.last_channel_measurements = channel_measurements
        self.last_shared_measurements = shared_measurements
        self.save_waveform_config()
        self.plot_waveforms()
        self.save_button.setEnabled(True)

    def plot_waveforms(self):
        self.axes.clear()
        for channel, (time_values, waveform_data) in self.last_waveforms.items():
            self.axes.plot(time_values, waveform_data, label=f"CH{channel}")
        self.axes.set_title("Captured Waveforms")
        self.axes.set_xlabel("Time (s)")
        self.axes.set_ylabel("Amplitude (V)")
        self.axes.grid(True, alpha=0.25)
        self.axes.legend(loc="best")
        self.figure.tight_layout()
        self.canvas.draw_idle()

    def on_mouse_move(self, event):
        if event.inaxes and event.xdata is not None and event.ydata is not None:
            self.coord_label.setText(f"Cursor: {event.xdata:.5f} s, {event.ydata:.5f} V")

    def save_data(self):
        file_name = self.filename_input.text().strip()
        if not file_name:
            QMessageBox.warning(self, "Invalid File Name", "Please enter a valid file name.")
            return
        if not self.last_waveforms:
            QMessageBox.warning(self, "No Waveform Data", "Capture waveform data before saving.")
            return

        save_dir = self.directory_input.text().strip()
        if not save_dir:
            save_dir = QFileDialog.getExistingDirectory(self, "Select Directory to Save Data")
        if not save_dir:
            return
        full_save_dir = os.path.join(save_dir, file_name)
        os.makedirs(full_save_dir, exist_ok=True)

        if self.export_checks[0].isChecked():
            if self.state.connected and self.state.oscilloscope is not None:
                screenshot_path = os.path.join(full_save_dir, f"{file_name}_screenshot.png")
                self.state.oscilloscope.capture_screenshot(screenshot_path)
                self.log(f"Screenshot saved at {screenshot_path}")
            else:
                self.log("Skipped screenshot export because the oscilloscope is offline.")

        if self.export_checks[1].isChecked():
            figure_path = os.path.join(full_save_dir, f"{file_name}_waveform_plot.png")
            self.figure.savefig(figure_path)
            self.log(f"Waveform plot saved at {figure_path}")

        if self.export_checks[2].isChecked():
            csv_path = os.path.join(full_save_dir, f"{file_name}_waveform_data.csv")
            write_waveforms_to_csv(csv_path, self.last_waveforms)
            self.log(f"Waveform data saved at {csv_path}")

        if self.export_checks[3].isChecked():
            excel_path = os.path.join(full_save_dir, f"{file_name}_measurements.xlsx")
            workbook = openpyxl.Workbook()
            sheet = workbook.active
            sheet.title = "Measurements"
            headers = ["Channel"] + get_selected_measurement_headers(self.selected_measurements)
            sheet.append(headers)
            for channel in sorted(self.last_waveforms):
                row = build_measurement_row(
                    channel,
                    self.selected_measurements,
                    self.last_channel_measurements.get(channel, {}),
                    self.last_shared_measurements,
                )
                sheet.append(row)
            workbook.save(excel_path)
            self.log(f"Measurements saved at {excel_path}")

        self.directory_input.setText(save_dir)
        self.save_waveform_config()
