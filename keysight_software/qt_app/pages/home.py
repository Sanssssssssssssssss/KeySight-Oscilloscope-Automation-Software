from __future__ import annotations

from typing import Callable

from keysight_software import config

try:
    import pyvisa
except ImportError:  # pragma: no cover - optional runtime dependency
    pyvisa = None

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class HomePage(QWidget):
    def __init__(self, reconnect_callback: Callable[[], None] | None = None):
        super().__init__()
        self.reconnect_callback = reconnect_callback
        self.metric_labels: dict[str, QLabel] = {}
        self.connection_badge: QLabel | None = None
        self.connection_summary: QLabel | None = None
        self.log_output: QPlainTextEdit | None = None
        self.visa_input: QLineEdit | None = None
        self.timeout_input: QLineEdit | None = None
        self.directory_input: QLineEdit | None = None
        self.filename_input: QLineEdit | None = None
        self.build_ui()
        self.try_auto_detect()

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        root.addWidget(self.build_overview_card())

        form_grid = QGridLayout()
        form_grid.setHorizontalSpacing(14)
        form_grid.setVerticalSpacing(14)
        form_grid.setColumnStretch(0, 1)
        form_grid.setColumnStretch(1, 1)
        form_grid.addWidget(self.build_instrument_card(), 0, 0)
        form_grid.addWidget(self.build_workspace_card(), 0, 1)
        root.addLayout(form_grid)

        root.addWidget(self.build_log_card())
        root.addStretch(1)

    def build_overview_card(self):
        card = QFrame()
        card.setObjectName("SurfaceCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(16)

        top = QHBoxLayout()
        top.setSpacing(12)

        title_block = QVBoxLayout()
        title_block.setSpacing(6)
        heading = QLabel("Bench overview")
        heading.setObjectName("SectionTitle")
        body = QLabel(
            "Keep the device target, timeout, and output profile aligned before moving into capture and automation."
        )
        body.setObjectName("MutedBody")
        body.setWordWrap(True)
        title_block.addWidget(heading)
        title_block.addWidget(body)
        top.addLayout(title_block, 1)

        status = QFrame()
        status.setObjectName("InlineStatusCard")
        status_layout = QHBoxLayout(status)
        status_layout.setContentsMargins(12, 10, 12, 10)
        status_layout.setSpacing(10)
        meta = QLabel("Connection")
        meta.setObjectName("StatusMeta")
        self.connection_badge = QLabel("Offline")
        self.connection_badge.setObjectName("StatusText")
        self.connection_badge.setProperty("status", "warn")
        reconnect = QPushButton("Reconnect")
        reconnect.setObjectName("GhostButton")
        reconnect.clicked.connect(self.connect_scope)
        status_layout.addWidget(meta)
        status_layout.addWidget(self.connection_badge)
        status_layout.addWidget(reconnect)
        top.addWidget(status, 0, Qt.AlignTop)
        layout.addLayout(top)

        self.connection_summary = QLabel("Waiting for an automatic discovery pass or a manual connection attempt.")
        self.connection_summary.setObjectName("MutedBody")
        self.connection_summary.setWordWrap(True)
        layout.addWidget(self.connection_summary)

        action_row = QHBoxLayout()
        action_row.setSpacing(10)
        detect = QPushButton("Detect VISA Address")
        detect.setObjectName("GhostButton")
        detect.clicked.connect(self.try_auto_detect)
        connect = QPushButton("Connect Instrument")
        connect.setObjectName("PrimaryButton")
        connect.clicked.connect(self.connect_scope)
        action_row.addWidget(detect)
        action_row.addWidget(connect)
        action_row.addStretch(1)
        layout.addLayout(action_row)

        metrics_row = QGridLayout()
        metrics_row.setHorizontalSpacing(12)
        metrics_row.setVerticalSpacing(12)
        metrics = [
            ("Default VISA", config.VISA_ADDRESS),
            ("Timeout", f"{config.GLOBAL_TIMEOUT} ms"),
            ("Base output", config.BASE_DIRECTORY),
        ]
        for column, (label_text, value_text) in enumerate(metrics):
            metric = QFrame()
            metric.setObjectName("MetricCard")
            metric_layout = QVBoxLayout(metric)
            metric_layout.setContentsMargins(14, 12, 14, 12)
            metric_layout.setSpacing(4)
            label = QLabel(label_text)
            label.setObjectName("MetricLabel")
            value = QLabel(value_text)
            value.setObjectName("MetricValue")
            value.setWordWrap(True)
            metric_layout.addWidget(label)
            metric_layout.addWidget(value)
            metrics_row.addWidget(metric, 0, column)
            self.metric_labels[label_text] = value
        layout.addLayout(metrics_row)
        return card

    def build_instrument_card(self):
        card = QFrame()
        card.setObjectName("SurfaceCard")
        layout = QGridLayout(card)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(10)

        heading = QLabel("Instrument target")
        heading.setObjectName("SectionTitle")
        text = QLabel("Tune address and timeout in a tighter control block.")
        text.setObjectName("MutedBody")
        text.setWordWrap(True)
        layout.addWidget(heading, 0, 0, 1, 2)
        layout.addWidget(text, 1, 0, 1, 2)

        layout.addWidget(self.make_field_label("VISA Address"), 2, 0, 1, 2)
        self.visa_input = QLineEdit(config.VISA_ADDRESS)
        layout.addWidget(self.visa_input, 3, 0, 1, 2)

        layout.addWidget(self.make_field_label("Timeout (ms)"), 4, 0)
        self.timeout_input = QLineEdit(str(config.GLOBAL_TIMEOUT))
        layout.addWidget(self.timeout_input, 5, 0)

        actions = QHBoxLayout()
        actions.setSpacing(10)
        detect = QPushButton("Detect")
        detect.setObjectName("GhostButton")
        detect.clicked.connect(self.try_auto_detect)
        connect = QPushButton("Connect")
        connect.setObjectName("PrimaryButton")
        connect.clicked.connect(self.connect_scope)
        actions.addWidget(detect)
        actions.addWidget(connect)
        actions.addStretch(1)
        layout.addLayout(actions, 5, 1)
        return card

    def build_workspace_card(self):
        card = QFrame()
        card.setObjectName("SurfaceCard")
        layout = QGridLayout(card)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(10)

        heading = QLabel("Workspace profile")
        heading.setObjectName("SectionTitle")
        text = QLabel("Keep storage and naming consistent across exports and scripts.")
        text.setObjectName("MutedBody")
        text.setWordWrap(True)
        layout.addWidget(heading, 0, 0, 1, 2)
        layout.addWidget(text, 1, 0, 1, 2)

        layout.addWidget(self.make_field_label("Base Directory"), 2, 0, 1, 2)
        self.directory_input = QLineEdit(config.BASE_DIRECTORY)
        layout.addWidget(self.directory_input, 3, 0, 1, 2)

        layout.addWidget(self.make_field_label("Base File Name"), 4, 0)
        self.filename_input = QLineEdit(config.BASE_FILENAME)
        layout.addWidget(self.filename_input, 5, 0)

        actions = QHBoxLayout()
        actions.setSpacing(10)
        browse = QPushButton("Browse")
        browse.setObjectName("GhostButton")
        browse.clicked.connect(self.pick_directory)
        save = QPushButton("Save")
        save.setObjectName("PrimaryButton")
        save.clicked.connect(self.save_profile)
        actions.addWidget(browse)
        actions.addWidget(save)
        actions.addStretch(1)
        layout.addLayout(actions, 5, 1)
        return card

    def build_log_card(self):
        card = QFrame()
        card.setObjectName("SurfaceCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(10)

        heading = QLabel("Connection log")
        heading.setObjectName("SectionTitle")
        subtitle = QLabel("A compact event stream for discovery, validation, and profile saves.")
        subtitle.setObjectName("MutedBody")
        subtitle.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(subtitle)

        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFixedHeight(150)
        layout.addWidget(self.log_output)
        return card

    def make_field_label(self, text: str):
        label = QLabel(text)
        label.setObjectName("MetricLabel")
        return label

    def log(self, message: str):
        if self.log_output:
            self.log_output.appendPlainText(message)

    def set_status(self, text: str, summary: str, ok: bool):
        if self.connection_badge is not None:
            self.connection_badge.setText(text)
            self.connection_badge.setProperty("status", "ok" if ok else "warn")
            self.connection_badge.style().unpolish(self.connection_badge)
            self.connection_badge.style().polish(self.connection_badge)
        if self.connection_summary is not None:
            self.connection_summary.setText(summary)

    def refresh_metrics(self):
        self.metric_labels["Default VISA"].setText(config.VISA_ADDRESS)
        self.metric_labels["Timeout"].setText(f"{config.GLOBAL_TIMEOUT} ms")
        self.metric_labels["Base output"].setText(config.BASE_DIRECTORY)

    def try_auto_detect(self):
        if pyvisa is None:
            self.set_status(
                "Manual setup",
                "pyvisa is not installed, so automatic discovery is unavailable in this environment.",
                False,
            )
            self.log("pyvisa is not installed. Please enter the VISA address manually.")
            return
        try:
            manager = pyvisa.ResourceManager()
            resources = manager.list_resources()
            if resources:
                self.visa_input.setText(resources[0])
                self.set_status(
                    "Device found",
                    "A VISA target was discovered automatically. You can connect now or refine the timeout first.",
                    True,
                )
                self.log(f"Found VISA address: {resources[0]}")
            else:
                self.set_status(
                    "No device found",
                    "No VISA resource responded during discovery. Manual entry is still available.",
                    False,
                )
                self.log("No devices found. Please enter the VISA address manually.")
        except Exception as error:
            self.set_status(
                "Auto detect failed",
                "Automatic discovery failed. Manual configuration is still available.",
                False,
            )
            self.log(f"Auto detection failed: {error}")

    def connect_scope(self):
        try:
            timeout = int(self.timeout_input.text().strip())
        except ValueError:
            self.set_status("Invalid timeout", "Timeout must be an integer value in milliseconds.", False)
            self.log("Timeout must be an integer value in milliseconds.")
            return

        config.update_visa_address(self.visa_input.text().strip())
        config.update_global_timeout(timeout)
        self.refresh_metrics()

        if pyvisa is None:
            self.set_status(
                "Manual setup",
                "pyvisa is missing in the current environment, so live verification cannot run here.",
                False,
            )
            self.log("pyvisa is not installed in the current Python environment.")
            return

        try:
            manager = pyvisa.ResourceManager()
            scope = manager.open_resource(config.VISA_ADDRESS)
            scope.timeout = timeout
            identity = scope.query("*IDN?").strip()
            scope.close()
            self.set_status(
                "Connected",
                "Live communication succeeded. This bench target is ready for the rest of the workflow.",
                True,
            )
            self.log(f"Connected to: {identity}")
            if self.reconnect_callback is not None:
                self.reconnect_callback()
        except pyvisa.errors.VisaIOError as error:
            self.set_status(
                "Connection failed",
                "The VISA target did not respond. Check cable, address, and vendor IO libraries.",
                False,
            )
            self.log(f"Could not connect to the oscilloscope: {error}")
        except Exception as error:
            self.set_status(
                "Connection failed",
                "The connection attempt ended unexpectedly. Review the log below for the raw error.",
                False,
            )
            self.log(f"An unexpected error occurred: {error}")

    def pick_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Base Directory", self.directory_input.text().strip())
        if directory:
            self.directory_input.setText(directory)

    def save_profile(self):
        try:
            timeout = int(self.timeout_input.text().strip())
        except ValueError:
            self.set_status("Invalid timeout", "Timeout must be an integer value in milliseconds.", False)
            self.log("Timeout must be an integer value in milliseconds.")
            return

        config.update_visa_address(self.visa_input.text().strip())
        config.update_global_timeout(timeout)
        config.update_base_directory(self.directory_input.text().strip())
        config.update_base_filename(self.filename_input.text().strip())
        self.refresh_metrics()
        self.set_status(
            "Profile saved",
            "Workspace defaults were stored successfully and are now reflected across the app.",
            True,
        )
        self.log(f"Saved VISA address: {config.VISA_ADDRESS}")
        self.log(f"Saved timeout: {config.GLOBAL_TIMEOUT}")
        self.log(f"Saved base directory: {config.BASE_DIRECTORY}")
        self.log(f"Saved base file name: {config.BASE_FILENAME}")

