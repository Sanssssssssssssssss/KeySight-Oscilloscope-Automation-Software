from __future__ import annotations

from typing import Callable

from keysight_software import config

try:
    import pyvisa
except ImportError:  # pragma: no cover - optional runtime dependency
    pyvisa = None

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)


class HomePage(QWidget):
    def __init__(self, reconnect_callback: Callable[[], None] | None = None):
        super().__init__()
        self.reconnect_callback = reconnect_callback
        self.metric_labels: dict[str, QLabel] = {}
        self.log_output: QPlainTextEdit | None = None
        self.connection_badge: QLabel | None = None
        self.connection_summary: QLabel | None = None
        self.visa_input: QLineEdit | None = None
        self.timeout_input: QLineEdit | None = None
        self.directory_input: QLineEdit | None = None
        self.filename_input: QLineEdit | None = None
        self.build_ui()
        self.try_auto_detect()

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)

        top_grid = QGridLayout()
        top_grid.setHorizontalSpacing(16)
        top_grid.setVerticalSpacing(16)
        top_grid.setColumnStretch(0, 8)
        top_grid.setColumnStretch(1, 4)
        root.addLayout(top_grid)

        top_grid.addWidget(self.build_hero_card(), 0, 0)

        side_stack = QVBoxLayout()
        side_stack.setSpacing(16)
        side_stack.addWidget(self.build_status_card())
        side_stack.addWidget(self.build_dark_card())
        top_grid.addLayout(side_stack, 0, 1)

        root.addWidget(self.build_control_center())
        root.addWidget(self.build_log_card(), 1)

    def build_hero_card(self):
        card = QFrame()
        card.setObjectName("HeroCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 26, 28, 26)
        layout.setSpacing(18)

        eyebrow = QLabel("Bench dashboard")
        eyebrow.setObjectName("Eyebrow")
        layout.addWidget(eyebrow)

        title = QLabel("A migration path to a more modern desktop UI.")
        title.setObjectName("HeroTitle")
        title.setWordWrap(True)
        layout.addWidget(title)

        body = QLabel(
            "This Qt shell is the starting point for moving the product away from classic Tk constraints. "
            "The layout is denser, styling is easier to control, and later pages can be built more like a real app shell."
        )
        body.setObjectName("HeroBody")
        body.setWordWrap(True)
        layout.addWidget(body)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        detect = QPushButton("Detect VISA Address")
        detect.setObjectName("GhostButton")
        detect.clicked.connect(self.try_auto_detect)
        connect = QPushButton("Connect Instrument")
        connect.setObjectName("PrimaryButton")
        connect.clicked.connect(self.connect_scope)
        buttons.addWidget(detect)
        buttons.addWidget(connect)
        buttons.addStretch(1)
        layout.addLayout(buttons)

        metrics = QGridLayout()
        metrics.setHorizontalSpacing(12)
        metrics.setVerticalSpacing(12)
        items = [
            ("Default VISA", config.VISA_ADDRESS),
            ("Timeout", f"{config.GLOBAL_TIMEOUT} ms"),
            ("Base output", config.BASE_DIRECTORY),
        ]
        for index, (label_text, value_text) in enumerate(items):
            metric = QFrame()
            metric.setObjectName("MetricCard")
            metric_layout = QVBoxLayout(metric)
            metric_layout.setContentsMargins(16, 14, 16, 14)
            metric_layout.setSpacing(6)
            label = QLabel(label_text)
            label.setObjectName("MetricLabel")
            value = QLabel(value_text)
            value.setObjectName("MetricValue")
            value.setWordWrap(True)
            metric_layout.addWidget(label)
            metric_layout.addWidget(value)
            metrics.addWidget(metric, 0, index)
            self.metric_labels[label_text] = value
        layout.addLayout(metrics)

        footer = QLabel(
            "If this shell feels right, the rest of the workflow can be migrated page by page onto the same foundation."
        )
        footer.setObjectName("MutedBody")
        footer.setWordWrap(True)
        layout.addWidget(footer)
        return card

    def build_status_card(self):
        card = QFrame()
        card.setObjectName("SurfaceCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        title = QLabel("Connection pulse")
        title.setObjectName("MetricValue")
        layout.addWidget(title)

        row = QHBoxLayout()
        row.setSpacing(10)
        meta = QLabel("Status")
        meta.setObjectName("MetricLabel")
        self.connection_badge = QLabel("Offline")
        self.connection_badge.setObjectName("StatusText")
        self.connection_badge.setProperty("status", "warn")
        row.addWidget(meta)
        row.addWidget(self.connection_badge)
        row.addStretch(1)
        layout.addLayout(row)

        self.connection_summary = QLabel("Waiting for an automatic discovery pass or manual connection attempt.")
        self.connection_summary.setObjectName("MutedBody")
        self.connection_summary.setWordWrap(True)
        layout.addWidget(self.connection_summary)

        reconnect = QPushButton("Reconnect")
        reconnect.setObjectName("GhostButton")
        reconnect.clicked.connect(self.connect_scope)
        layout.addWidget(reconnect, 0, Qt.AlignLeft)
        return card

    def build_dark_card(self):
        card = QFrame()
        card.setObjectName("DarkCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(8)

        title = QLabel("Migration note")
        title.setObjectName("DarkTitle")
        layout.addWidget(title)

        body = QLabel(
            "Qt gives us proper stylesheet control, richer layout primitives, and a more realistic path toward polished desktop UI than raw Tk."
        )
        body.setObjectName("DarkBody")
        body.setWordWrap(True)
        layout.addWidget(body)
        return card

    def build_control_center(self):
        card = QFrame()
        card.setObjectName("SurfaceCard")
        layout = QGridLayout(card)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setHorizontalSpacing(18)
        layout.setVerticalSpacing(14)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)

        heading = QLabel("Control center")
        heading.setObjectName("MetricValue")
        sub = QLabel("A denser configuration surface for connection and workspace defaults.")
        sub.setObjectName("MutedBody")
        sub.setWordWrap(True)
        layout.addWidget(heading, 0, 0, 1, 2)
        layout.addWidget(sub, 1, 0, 1, 2)

        left = self.build_instrument_panel()
        right = self.build_workspace_panel()
        layout.addWidget(left, 2, 0)
        layout.addWidget(right, 2, 1)
        return card

    def build_instrument_panel(self):
        panel = QWidget()
        layout = QGridLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(12)

        title = QLabel("Instrument target")
        title.setObjectName("MetricValue")
        desc = QLabel("Tune address and timeout without wasting vertical space.")
        desc.setObjectName("MutedBody")
        desc.setWordWrap(True)
        layout.addWidget(title, 0, 0, 1, 2)
        layout.addWidget(desc, 1, 0, 1, 2)

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
        return panel

    def build_workspace_panel(self):
        panel = QWidget()
        layout = QGridLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(12)

        title = QLabel("Workspace profile")
        title.setObjectName("MetricValue")
        desc = QLabel("Keep storage and naming aligned with the rest of the workflow.")
        desc.setObjectName("MutedBody")
        desc.setWordWrap(True)
        layout.addWidget(title, 0, 0, 1, 2)
        layout.addWidget(desc, 1, 0, 1, 2)

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
        return panel

    def build_log_card(self):
        card = QFrame()
        card.setObjectName("SurfaceCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        heading = QLabel("Connection log")
        heading.setObjectName("MetricValue")
        layout.addWidget(heading)
        subtitle = QLabel("A compact event stream for discovery, validation, and save activity.")
        subtitle.setObjectName("MutedBody")
        subtitle.setWordWrap(True)
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

