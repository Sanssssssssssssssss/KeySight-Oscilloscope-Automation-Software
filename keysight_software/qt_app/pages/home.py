from __future__ import annotations

from keysight_software import config
from keysight_software.qt_app.state import AppState
from keysight_software.qt_app.widgets import create_card, create_inline_status, create_log, create_metric_card

try:
    import pyvisa
except ImportError:  # pragma: no cover - optional runtime dependency
    pyvisa = None

from PySide6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class HomePage(QWidget):
    def __init__(self, state: AppState):
        super().__init__()
        self.state = state
        self.metric_labels: dict[str, QLabel] = {}
        self.connection_badge: QLabel | None = None
        self.connection_summary: QLabel | None = None
        self.log_output = create_log(132)
        self.visa_input: QLineEdit | None = None
        self.timeout_input: QLineEdit | None = None
        self.directory_input: QLineEdit | None = None
        self.filename_input: QLineEdit | None = None
        self.build_ui()
        self.state.changed.connect(self.refresh_from_state)
        self.try_auto_detect()
        self.refresh_from_state()

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        root.addWidget(self.build_overview_card())

        cards = QGridLayout()
        cards.setHorizontalSpacing(14)
        cards.setVerticalSpacing(14)
        cards.addWidget(self.build_instrument_card(), 0, 0)
        cards.addWidget(self.build_workspace_card(), 0, 1)
        cards.setColumnStretch(0, 1)
        cards.setColumnStretch(1, 1)
        root.addLayout(cards)

        log_card, log_layout = create_card(
            "Connection log",
            "A compact event stream for discovery, validation, and workspace updates.",
        )
        log_layout.addWidget(self.log_output)
        root.addWidget(log_card)

    def build_overview_card(self):
        card, layout = create_card(
            "Bench overview",
            "Keep the device target, timeout, and output profile aligned before moving into capture and automation.",
        )

        top = QHBoxLayout()
        top.setSpacing(12)

        status_shell, self.connection_badge = create_inline_status("Connection", "Disconnected", "warn")
        reconnect = QPushButton("Reconnect")
        reconnect.setObjectName("GhostButton")
        reconnect.clicked.connect(self.connect_scope)
        status_shell.layout().addWidget(reconnect)
        top.addWidget(status_shell, 0)
        top.addStretch(1)
        layout.addLayout(top)

        self.connection_summary = QLabel()
        self.connection_summary.setObjectName("MutedBody")
        self.connection_summary.setWordWrap(True)
        layout.addWidget(self.connection_summary)

        actions = QHBoxLayout()
        detect = QPushButton("Detect VISA Address")
        detect.setObjectName("GhostButton")
        detect.clicked.connect(self.try_auto_detect)
        connect = QPushButton("Connect Instrument")
        connect.setObjectName("PrimaryButton")
        connect.clicked.connect(self.connect_scope)
        actions.addWidget(detect)
        actions.addWidget(connect)
        actions.addStretch(1)
        layout.addLayout(actions)

        metrics = QGridLayout()
        metrics.setHorizontalSpacing(12)
        for index, (label_text, value_text) in enumerate(
            [
                ("Default VISA", config.VISA_ADDRESS),
                ("Timeout", f"{config.GLOBAL_TIMEOUT} ms"),
                ("Base output", config.BASE_DIRECTORY),
            ]
        ):
            metric, value = create_metric_card(label_text, value_text)
            metrics.addWidget(metric, 0, index)
            self.metric_labels[label_text] = value
        layout.addLayout(metrics)
        return card

    def build_instrument_card(self):
        card, layout = create_card("Instrument target", "Tune address and timeout in a tighter control block.")
        form = QGridLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)

        form.addWidget(self.field_label("VISA Address"), 0, 0, 1, 2)
        self.visa_input = QLineEdit(config.VISA_ADDRESS)
        form.addWidget(self.visa_input, 1, 0, 1, 2)

        form.addWidget(self.field_label("Timeout (ms)"), 2, 0)
        self.timeout_input = QLineEdit(str(config.GLOBAL_TIMEOUT))
        form.addWidget(self.timeout_input, 3, 0)

        actions = QHBoxLayout()
        detect = QPushButton("Detect")
        detect.setObjectName("GhostButton")
        detect.clicked.connect(self.try_auto_detect)
        connect = QPushButton("Connect")
        connect.setObjectName("PrimaryButton")
        connect.clicked.connect(self.connect_scope)
        actions.addWidget(detect)
        actions.addWidget(connect)
        actions.addStretch(1)
        form.addLayout(actions, 3, 1)
        layout.addLayout(form)
        return card

    def build_workspace_card(self):
        card, layout = create_card("Workspace profile", "Keep storage and naming consistent across exports and scripts.")
        form = QGridLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)

        form.addWidget(self.field_label("Base Directory"), 0, 0, 1, 2)
        self.directory_input = QLineEdit(config.BASE_DIRECTORY)
        form.addWidget(self.directory_input, 1, 0, 1, 2)

        form.addWidget(self.field_label("Base File Name"), 2, 0)
        self.filename_input = QLineEdit(config.BASE_FILENAME)
        form.addWidget(self.filename_input, 3, 0)

        actions = QHBoxLayout()
        browse = QPushButton("Browse")
        browse.setObjectName("GhostButton")
        browse.clicked.connect(self.pick_directory)
        save = QPushButton("Save")
        save.setObjectName("PrimaryButton")
        save.clicked.connect(self.save_profile)
        actions.addWidget(browse)
        actions.addWidget(save)
        actions.addStretch(1)
        form.addLayout(actions, 3, 1)
        layout.addLayout(form)
        return card

    def field_label(self, text: str):
        label = QLabel(text)
        label.setObjectName("MetricLabel")
        return label

    def log(self, message: str):
        self.log_output.appendPlainText(message)

    def refresh_from_state(self):
        snapshot = self.state.snapshot()
        self.connection_badge.setText(snapshot.label)
        self.connection_badge.setProperty("status", "ok" if snapshot.connected else "warn")
        self.connection_badge.style().unpolish(self.connection_badge)
        self.connection_badge.style().polish(self.connection_badge)
        self.connection_summary.setText(snapshot.summary)
        self.refresh_metrics()

    def refresh_metrics(self):
        self.metric_labels["Default VISA"].setText(config.VISA_ADDRESS)
        self.metric_labels["Timeout"].setText(f"{config.GLOBAL_TIMEOUT} ms")
        self.metric_labels["Base output"].setText(config.BASE_DIRECTORY)

    def try_auto_detect(self):
        if pyvisa is None:
            self.log("pyvisa is not installed. Please enter the VISA address manually.")
            return
        try:
            manager = pyvisa.ResourceManager()
            resources = manager.list_resources()
            if resources:
                self.visa_input.setText(resources[0])
                self.log(f"Found VISA address: {resources[0]}")
            else:
                self.log("No VISA resources detected. Manual entry is still available.")
        except Exception as error:
            self.log(f"Auto detection failed: {error}")

    def connect_scope(self):
        try:
            timeout = int(self.timeout_input.text().strip())
        except ValueError:
            self.log("Timeout must be an integer value in milliseconds.")
            return
        success = self.state.connect_scope(self.visa_input.text().strip(), timeout)
        if success:
            self.log(f"Connected to: {self.state.identity}")
        else:
            self.log(f"Connection failed: {self.state.error}")

    def pick_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Base Directory", self.directory_input.text().strip())
        if directory:
            self.directory_input.setText(directory)

    def save_profile(self):
        try:
            timeout = int(self.timeout_input.text().strip())
        except ValueError:
            self.log("Timeout must be an integer value in milliseconds.")
            return
        config.update_visa_address(self.visa_input.text().strip())
        config.update_global_timeout(timeout)
        config.update_base_directory(self.directory_input.text().strip())
        config.update_base_filename(self.filename_input.text().strip())
        self.refresh_metrics()
        self.refresh_from_state()
        self.log(f"Saved VISA address: {config.VISA_ADDRESS}")
        self.log(f"Saved timeout: {config.GLOBAL_TIMEOUT}")
        self.log(f"Saved base directory: {config.BASE_DIRECTORY}")
        self.log(f"Saved base file name: {config.BASE_FILENAME}")
