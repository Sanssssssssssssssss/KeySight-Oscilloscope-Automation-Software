from __future__ import annotations

import json
import os

import openpyxl
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
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
from keysight_software.qt_app.widgets import create_card, create_inline_status, create_log, create_metric_card
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
DISPLAY_SAMPLE_LIMIT = 2000


class MeasurementDialog(QDialog):
    def __init__(
        self,
        selected_measurements: dict[str, int],
        channel_1: int,
        channel_2: int,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Measurement Preset")
        self.resize(420, 520)
        self.measurement_checks: dict[str, QCheckBox] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        info = QLabel("Choose which scalar measurements should be calculated after each capture.")
        info.setObjectName("MutedBody")
        info.setWordWrap(True)
        root.addWidget(info)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(6)
        for name in get_measurement_names():
            check = QCheckBox(name)
            check.setChecked(bool(selected_measurements.get(name)))
            self.measurement_checks[name] = check
            content_layout.addWidget(check)
        content_layout.addStretch(1)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        pair_row = QHBoxLayout()
        pair_row.setSpacing(12)
        pair_row.addWidget(self.build_phase_box("Phase channel A", channel_1))
        pair_row.addWidget(self.build_phase_box("Phase channel B", channel_2))
        root.addLayout(pair_row)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def build_phase_box(self, label_text: str, current_value: int):
        shell = QFrame()
        layout = QVBoxLayout(shell)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        label = QLabel(label_text)
        label.setObjectName("MetricLabel")
        combo = QComboBox()
        combo.addItems(["1", "2", "3", "4"])
        combo.setCurrentText(str(current_value))
        layout.addWidget(label)
        layout.addWidget(combo)
        if "A" in label_text:
            self.channel_1_combo = combo
        else:
            self.channel_2_combo = combo
        return shell

    def payload(self) -> tuple[dict[str, int], int, int]:
        measurements = {name: int(check.isChecked()) for name, check in self.measurement_checks.items()}
        return measurements, int(self.channel_1_combo.currentText()), int(self.channel_2_combo.currentText())


class WaveformCapturePage(QWidget):
    def __init__(self, state: AppState):
        super().__init__()
        self.state = state
        self.capture_in_progress = False
        self.connection_badge: QLabel | None = None
        self.connection_hint: QLabel | None = None
        self.capture_button: QPushButton | None = None
        self.save_button: QPushButton | None = None
        self.selection_summary: QLabel | None = None
        self.capture_summary: QLabel | None = None
        self.metric_values: dict[str, QLabel] = {}
        self.log_output = create_log(180)
        self.channel_checks: list[QCheckBox] = []
        self.export_checks: list[QCheckBox] = []
        self.filename_input = QLineEdit()
        self.directory_input = QLineEdit()
        self.cursor_label = QLabel("Cursor: -, -")
        self.cursor_label.setObjectName("MutedBody")
        self.figure = Figure(figsize=(7.2, 3.8), dpi=100)
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
        self.state.changed.connect(self.refresh_status)
        self.refresh_selection_summary()
        self.refresh_status()

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        root.addWidget(self.build_session_card())
        root.addWidget(self.build_canvas_card())

        bottom = QGridLayout()
        bottom.setHorizontalSpacing(14)
        bottom.setVerticalSpacing(14)
        bottom.setColumnStretch(0, 1)
        bottom.setColumnStretch(1, 1)
        bottom.addWidget(self.build_export_card(), 0, 0)
        bottom.addWidget(self.build_results_card(), 0, 1)
        root.addLayout(bottom)

    def build_session_card(self):
        card, layout = create_card(
            "Capture session",
            "Keep selection, bench status, and export defaults visible without forcing the page into a wide split layout.",
        )

        top_row = QHBoxLayout()
        top_row.setSpacing(12)
        status_shell, self.connection_badge = create_inline_status("Connection", "Disconnected", "warn")
        self.connection_hint = QLabel()
        self.connection_hint.setObjectName("MutedBody")
        self.connection_hint.setWordWrap(True)
        top_row.addWidget(status_shell, 0)
        top_row.addWidget(self.connection_hint, 1)
        layout.addLayout(top_row)

        control_row = QHBoxLayout()
        control_row.setSpacing(14)

        selection_card, selection_layout = create_card("Channels and measurements")
        channel_row = QHBoxLayout()
        channel_row.setSpacing(10)
        for index in range(4):
            checkbox = QCheckBox(f"CH{index + 1}")
            checkbox.toggled.connect(self.refresh_selection_summary)
            self.channel_checks.append(checkbox)
            channel_row.addWidget(checkbox)
        channel_row.addStretch(1)
        selection_layout.addLayout(channel_row)
        self.selection_summary = QLabel()
        self.selection_summary.setObjectName("MutedBody")
        self.selection_summary.setWordWrap(True)
        selection_layout.addWidget(self.selection_summary)
        selection_actions = QHBoxLayout()
        select_measurements = QPushButton("Edit Measurements")
        select_measurements.setObjectName("GhostButton")
        select_measurements.clicked.connect(self.open_measurement_dialog)
        self.capture_button = QPushButton("Capture Now")
        self.capture_button.setObjectName("PrimaryButton")
        self.capture_button.clicked.connect(self.capture_waveform)
        selection_actions.addWidget(select_measurements)
        selection_actions.addWidget(self.capture_button)
        selection_actions.addStretch(1)
        selection_layout.addLayout(selection_actions)
        control_row.addWidget(selection_card, 3)

        summary_card, summary_layout = create_card("Latest capture")
        metrics_layout = QGridLayout()
        metrics_layout.setHorizontalSpacing(10)
        metric_defs = [
            ("Channels", "None"),
            ("Samples", "-"),
            ("Measurements", "0"),
        ]
        for column, (label_text, value_text) in enumerate(metric_defs):
            metric_card, value = create_metric_card(label_text, value_text)
            self.metric_values[label_text] = value
            metrics_layout.addWidget(metric_card, 0, column)
        summary_layout.addLayout(metrics_layout)
        self.capture_summary = QLabel("No acquisition has been captured yet.")
        self.capture_summary.setObjectName("MutedBody")
        self.capture_summary.setWordWrap(True)
        summary_layout.addWidget(self.capture_summary)
        control_row.addWidget(summary_card, 2)

        layout.addLayout(control_row)
        return card

    def build_canvas_card(self):
        card, layout = create_card("Waveform canvas", "Rendered view is downsampled for smoother interaction. Saved CSV and measurements still use the full capture.")
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        reset = QPushButton("Reset View")
        reset.setObjectName("GhostButton")
        reset.clicked.connect(self.reset_canvas)
        toolbar.addWidget(self.cursor_label)
        toolbar.addStretch(1)
        toolbar.addWidget(reset)
        layout.addLayout(toolbar)
        self.canvas.setMinimumHeight(320)
        layout.addWidget(self.canvas)
        return card

    def build_export_card(self):
        card, layout = create_card("Export bundle", "Choose the artifacts to write after a capture.")
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)

        for row, label_text in enumerate(("Save Screenshot", "Save Plot", "Save CSV", "Save Measurements")):
            checkbox = QCheckBox(label_text)
            checkbox.setChecked(True)
            self.export_checks.append(checkbox)
            grid.addWidget(checkbox, row, 0, 1, 2)

        directory_label = QLabel("Save directory")
        directory_label.setObjectName("MetricLabel")
        grid.addWidget(directory_label, 4, 0, 1, 2)
        grid.addWidget(self.directory_input, 5, 0)
        browse = QPushButton("Browse")
        browse.setObjectName("GhostButton")
        browse.clicked.connect(self.pick_directory)
        grid.addWidget(browse, 5, 1)

        filename_label = QLabel("Capture name")
        filename_label.setObjectName("MetricLabel")
        grid.addWidget(filename_label, 6, 0, 1, 2)
        self.filename_input.setText("waveform_data")
        grid.addWidget(self.filename_input, 7, 0, 1, 2)
        layout.addLayout(grid)

        actions = QHBoxLayout()
        self.save_button = QPushButton("Save Data")
        self.save_button.setObjectName("PrimaryButton")
        self.save_button.clicked.connect(self.save_data)
        save_config = QPushButton("Save Defaults")
        save_config.setObjectName("GhostButton")
        save_config.clicked.connect(self.save_waveform_config)
        actions.addWidget(self.save_button)
        actions.addWidget(save_config)
        actions.addStretch(1)
        layout.addLayout(actions)
        return card

    def build_results_card(self):
        card, layout = create_card("Measurement results", "Most recent scalar results and export actions.")
        layout.addWidget(self.log_output)
        return card

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

    def save_waveform_config(self, announce: bool = True):
        payload = {
            "channels": [int(check.isChecked()) for check in self.channel_checks],
            "measurements": self.selected_measurements,
            "save_options": [int(check.isChecked()) for check in self.export_checks],
            "save_directory": self.directory_input.text().strip(),
            "file_name": self.filename_input.text().strip(),
        }
        with open(WAVEFORM_CONFIG_FILE, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=4)
        if announce:
            self.log("Capture defaults saved.")

    def refresh_status(self):
        snapshot = self.state.snapshot()
        self.connection_badge.setText(snapshot.label)
        self.connection_badge.setProperty("status", "ok" if snapshot.connected else "warn")
        self.connection_badge.style().unpolish(self.connection_badge)
        self.connection_badge.style().polish(self.connection_badge)
        if snapshot.connected and snapshot.active_channels:
            channels = ", ".join(f"CH{channel}" for channel in snapshot.active_channels)
            self.connection_hint.setText(f"Live acquisition is available. Active channels: {channels}.")
        else:
            self.connection_hint.setText(snapshot.summary)
        if self.capture_button is not None:
            self.capture_button.setEnabled(snapshot.connected and not self.capture_in_progress)
        if self.save_button is not None:
            self.save_button.setEnabled(bool(self.last_waveforms) and not self.capture_in_progress)

    def refresh_selection_summary(self):
        channels = [index + 1 for index, checkbox in enumerate(self.channel_checks) if checkbox.isChecked()]
        selected_measurements = [name for name, enabled in self.selected_measurements.items() if enabled]
        if channels:
            channel_text = ", ".join(f"CH{channel}" for channel in channels)
        else:
            channel_text = "No channels selected"
        measurement_text = f"{len(selected_measurements)} measurements enabled"
        phase_text = f"Phase pair CH{self.selected_channel_1} / CH{self.selected_channel_2}"
        self.selection_summary.setText(f"{channel_text}. {measurement_text}. {phase_text}.")

    def open_measurement_dialog(self):
        dialog = MeasurementDialog(
            self.selected_measurements,
            self.selected_channel_1,
            self.selected_channel_2,
            self,
        )
        if dialog.exec():
            self.selected_measurements, self.selected_channel_1, self.selected_channel_2 = dialog.payload()
            self.save_measurement_config()
            self.refresh_selection_summary()
            self.log("Updated measurement preset.")

    def pick_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory", self.directory_input.text().strip())
        if directory:
            self.directory_input.setText(directory)

    def selected_channels(self) -> list[int]:
        return [index + 1 for index, checkbox in enumerate(self.channel_checks) if checkbox.isChecked()]

    def capture_waveform(self):
        if self.capture_in_progress:
            return
        if not self.state.connected or self.state.oscilloscope is None or self.state.measure is None:
            self.log("Capture skipped because the oscilloscope is not connected.")
            return
        channels = self.selected_channels()
        if not channels:
            QMessageBox.warning(self, "No Channel Selected", "Please select at least one channel.")
            return

        self.capture_in_progress = True
        self.refresh_status()
        self.capture_button.setText("Capturing...")
        QApplication.processEvents()

        try:
            self.log_output.clear()
            waveforms: dict[int, tuple] = {}
            channel_measurements: dict[int, dict[str, float | None]] = {}

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
            self.save_waveform_config(announce=False)
            self.plot_waveforms()
            self.refresh_capture_summary()
        finally:
            self.capture_in_progress = False
            self.capture_button.setText("Capture Now")
            self.refresh_status()

    def refresh_capture_summary(self):
        if not self.last_waveforms:
            self.capture_summary.setText("No acquisition has been captured yet.")
            self.metric_values["Channels"].setText("None")
            self.metric_values["Samples"].setText("-")
            self.metric_values["Measurements"].setText("0")
            return

        channels = ", ".join(f"CH{channel}" for channel in sorted(self.last_waveforms))
        sample_count = max(len(values[1]) for values in self.last_waveforms.values())
        selected_count = sum(1 for enabled in self.selected_measurements.values() if enabled)
        self.metric_values["Channels"].setText(channels)
        self.metric_values["Samples"].setText(str(sample_count))
        self.metric_values["Measurements"].setText(str(selected_count))
        self.capture_summary.setText(
            "Latest capture is cached locally. You can export it again without reacquiring from the instrument."
        )

    def downsample(self, x_values, y_values):
        length = len(y_values)
        if length <= DISPLAY_SAMPLE_LIMIT:
            return x_values, y_values
        step = max(length // DISPLAY_SAMPLE_LIMIT, 1)
        return x_values[::step], y_values[::step]

    def plot_waveforms(self):
        self.axes.clear()
        for channel, (time_values, waveform_data) in self.last_waveforms.items():
            sampled_time, sampled_wave = self.downsample(time_values, waveform_data)
            self.axes.plot(sampled_time, sampled_wave, label=f"CH{channel}", linewidth=1.3)
        self.axes.set_title("Captured Waveforms")
        self.axes.set_xlabel("Time (s)")
        self.axes.set_ylabel("Amplitude (V)")
        self.axes.grid(True, alpha=0.22)
        self.axes.legend(loc="best")
        self.figure.tight_layout(pad=1.2)
        self.canvas.draw_idle()

    def reset_canvas(self):
        if self.last_waveforms:
            self.plot_waveforms()

    def on_mouse_move(self, event):
        if event.inaxes and event.xdata is not None and event.ydata is not None:
            self.cursor_label.setText(f"Cursor: {event.xdata:.5f} s, {event.ydata:.5f} V")
        else:
            self.cursor_label.setText("Cursor: -, -")

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
        self.save_waveform_config(announce=False)
