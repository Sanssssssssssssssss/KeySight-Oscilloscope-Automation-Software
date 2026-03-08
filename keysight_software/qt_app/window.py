from __future__ import annotations

from functools import partial

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from keysight_software import config
from keysight_software.qt_app.pages.axis_control import AxisControlPage
from keysight_software.qt_app.pages.batch_process import BatchProcessPage
from keysight_software.qt_app.pages.home import HomePage
from keysight_software.qt_app.pages.run_script import RunScriptPage
from keysight_software.qt_app.pages.script_editor import ScriptEditorPage
from keysight_software.qt_app.pages.settings import SettingsPage
from keysight_software.qt_app.pages.waveform_capture import WaveformCapturePage
from keysight_software.qt_app.state import AppState
from keysight_software.qt_app.styles import APP_STYLESHEET


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.state = AppState()
        self.nav_buttons: dict[str, QPushButton] = {}
        self.page_titles: dict[str, tuple[str, str]] = {}
        self.page_indexes: dict[str, int] = {}
        self.page_widgets: dict[str, QWidget] = {}
        self.runner_page: RunScriptPage | None = None
        self.setWindowTitle("Keysight Automation Studio")
        self.resize(1490, 920)
        self.setMinimumSize(1160, 760)
        self.setStyleSheet(APP_STYLESHEET)
        self.build_ui()
        self.state.changed.connect(self.refresh_status)
        self.refresh_status()

    def build_ui(self):
        shell = QWidget()
        shell.setObjectName("AppShell")
        self.setCentralWidget(shell)

        root = QHBoxLayout(shell)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self.build_sidebar())

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(22, 14, 22, 14)
        content_layout.setSpacing(12)
        root.addWidget(content, 1)

        content_layout.addWidget(self.build_topbar())

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content_layout.addWidget(self.scroll_area, 1)

        host = QWidget()
        host_layout = QVBoxLayout(host)
        host_layout.setContentsMargins(0, 0, 0, 0)
        self.pages = QStackedWidget()
        host_layout.addWidget(self.pages)
        self.scroll_area.setWidget(host)

        self.runner_page = RunScriptPage(self.state)
        self.add_page(
            "home",
            "Instrument workspace",
            "Connection setup, workspace defaults, and live instrument discovery.",
            HomePage(self.state),
        )
        self.add_page(
            "capture",
            "Waveform capture",
            "Acquire channels, inspect traces, and export the latest waveform bundle.",
            WaveformCapturePage(self.state),
        )
        self.add_page(
            "axis",
            "Axis control",
            "Tune timebase, channel scale, and marker presets for the active bench.",
            AxisControlPage(self.state),
        )
        self.add_page(
            "script",
            "Script editor",
            "Compose reusable module sequences and hand them off to the runner.",
            ScriptEditorPage(self.show_page, self.open_runner, self.status_tuple),
        )
        self.add_page(
            "runner",
            "Run script",
            "Load sequence packages and execute them with shared bench state.",
            self.runner_page,
        )
        self.add_page(
            "batch",
            "Batch process",
            "Merge repeated run folders into a final consolidated measurements package.",
            BatchProcessPage(),
        )
        self.add_page(
            "settings",
            "Settings",
            "Adjust runtime defaults, export preferences, and fallback workspace values.",
            SettingsPage(),
        )
        self.show_page("home")

    def build_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(148)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(10, 14, 10, 14)
        layout.setSpacing(8)

        brand = QLabel("Keysight")
        brand.setObjectName("SidebarBrand")
        layout.addWidget(brand)
        sub = QLabel("Automation Studio")
        sub.setObjectName("SidebarSub")
        layout.addWidget(sub)
        layout.addSpacing(6)

        nav_items = [
            ("home", "Home"),
            ("capture", "Capture"),
            ("axis", "Axis"),
            ("script", "Scripts"),
            ("runner", "Runner"),
            ("batch", "Batch"),
            ("settings", "Settings"),
        ]
        for key, label_text in nav_items:
            button = QPushButton(label_text)
            button.setProperty("nav", True)
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(partial(self.show_page, key))
            layout.addWidget(button)
            self.nav_buttons[key] = button

        layout.addStretch(1)
        footer = QLabel("Qt client")
        footer.setObjectName("SidebarSub")
        layout.addWidget(footer)
        return sidebar

    def build_topbar(self):
        bar = QFrame()
        bar.setObjectName("TopBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        title_box = QVBoxLayout()
        title_box.setSpacing(0)
        self.page_title = QLabel()
        self.page_title.setObjectName("PageTitle")
        self.page_subtitle = QLabel()
        self.page_subtitle.setObjectName("PageSubtitle")
        self.page_subtitle.setWordWrap(True)
        title_box.addWidget(self.page_title)
        title_box.addWidget(self.page_subtitle)
        layout.addLayout(title_box, 1)

        self.status_bar = QFrame()
        self.status_bar.setObjectName("StatusBar")
        self.status_bar.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        status_layout = QHBoxLayout(self.status_bar)
        status_layout.setContentsMargins(9, 6, 9, 6)
        status_layout.setSpacing(7)
        meta = QLabel("Connection")
        meta.setObjectName("StatusMeta")
        self.status_text = QLabel("Disconnected")
        self.status_text.setObjectName("StatusText")
        self.status_text.setProperty("status", "warn")
        self.status_hint = QLabel("Offline mode available")
        self.status_hint.setObjectName("StatusHint")
        reconnect = QPushButton("Reconnect")
        reconnect.setObjectName("GhostButton")
        reconnect.setFixedHeight(28)
        reconnect.clicked.connect(self.reconnect_scope)
        status_layout.addWidget(meta)
        status_layout.addWidget(self.status_text)
        status_layout.addWidget(self.status_hint)
        status_layout.addWidget(reconnect)
        layout.addWidget(self.status_bar, 0, Qt.AlignRight | Qt.AlignTop)
        return bar

    def add_page(self, key: str, title: str, subtitle: str, widget: QWidget):
        self.page_titles[key] = (title, subtitle)
        self.page_widgets[key] = widget

        wrapper = QWidget()
        wrapper_layout = QHBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.setSpacing(0)
        wrapper_layout.addStretch(1)
        widget.setMaximumWidth(1200)
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        wrapper_layout.addWidget(widget, 0, Qt.AlignTop)
        wrapper_layout.addStretch(1)

        self.page_indexes[key] = self.pages.addWidget(wrapper)

    def show_page(self, key: str):
        self.pages.setCurrentIndex(self.page_indexes[key])
        title, subtitle = self.page_titles[key]
        self.page_title.setText(title)
        self.page_subtitle.setText(subtitle)
        for name, button in self.nav_buttons.items():
            button.setProperty("active", name == key)
            button.style().unpolish(button)
            button.style().polish(button)
        self.scroll_area.verticalScrollBar().setValue(0)

    def status_tuple(self) -> tuple[str, str, bool]:
        snapshot = self.state.snapshot()
        return snapshot.label, snapshot.summary, snapshot.connected

    def refresh_status(self):
        snapshot = self.state.snapshot()
        self.status_text.setText(snapshot.label)
        self.status_text.setProperty("status", "ok" if snapshot.connected else "warn")
        self.status_text.style().unpolish(self.status_text)
        self.status_text.style().polish(self.status_text)
        if snapshot.connected and snapshot.active_channels:
            channels = ", ".join(f"CH{channel}" for channel in snapshot.active_channels)
            self.status_hint.setText(f"{channels} ready")
        elif snapshot.connected:
            self.status_hint.setText("Bench ready")
        else:
            self.status_hint.setText("Offline mode available")
        for widget in self.page_widgets.values():
            if hasattr(widget, "refresh_status"):
                widget.refresh_status()

    def reconnect_scope(self):
        self.state.connect_scope(config.VISA_ADDRESS, config.GLOBAL_TIMEOUT)

    def open_runner(self, sequence_path: str):
        if self.runner_page is not None:
            self.runner_page.load_script(sequence_path)
        self.show_page("runner")

    def closeEvent(self, event):
        self.state.close_scope()
        super().closeEvent(event)
