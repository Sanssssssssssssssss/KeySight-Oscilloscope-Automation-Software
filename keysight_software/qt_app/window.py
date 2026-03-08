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

from keysight_software.qt_app.pages.home import HomePage
from keysight_software.qt_app.styles import APP_STYLESHEET


class PlaceholderPage(QWidget):
    def __init__(self, title: str, body: str):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        card = QFrame()
        card.setObjectName("SurfaceCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(26, 24, 26, 24)
        heading = QLabel(title)
        heading.setObjectName("MetricValue")
        text = QLabel(body)
        text.setObjectName("MutedBody")
        text.setWordWrap(True)
        card_layout.addWidget(heading)
        card_layout.addWidget(text)
        layout.addWidget(card)
        layout.addStretch(1)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.nav_buttons: dict[str, QPushButton] = {}
        self.page_titles: dict[str, tuple[str, str]] = {}
        self.setWindowTitle("Keysight Automation Studio")
        self.resize(1500, 930)
        self.setMinimumSize(1180, 760)
        self.setStyleSheet(APP_STYLESHEET)
        self.build_ui()

    def build_ui(self):
        shell = QWidget()
        shell.setObjectName("AppShell")
        self.setCentralWidget(shell)

        root = QHBoxLayout(shell)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        sidebar = self.build_sidebar()
        root.addWidget(sidebar)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(28, 18, 28, 18)
        content_layout.setSpacing(14)
        root.addWidget(content, 1)

        topbar = self.build_topbar()
        content_layout.addWidget(topbar)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("QScrollArea { background: transparent; }")
        content_layout.addWidget(self.scroll_area, 1)

        self.page_host = QWidget()
        self.page_host_layout = QVBoxLayout(self.page_host)
        self.page_host_layout.setContentsMargins(0, 0, 0, 0)
        self.page_host_layout.setSpacing(0)
        self.scroll_area.setWidget(self.page_host)

        self.pages = QStackedWidget()
        self.page_host_layout.addWidget(self.pages)

        self.add_page(
            "home",
            "Instrument workspace",
            "Connection setup, workspace defaults and live instrument discovery.",
            HomePage(),
        )
        self.add_page(
            "capture",
            "Waveform capture",
            "Qt migration target. This page will be ported next if the shell direction feels right.",
            PlaceholderPage("Waveform capture", "Planned next: charting, live controls, and export cards."),
        )
        self.add_page(
            "axis",
            "Axis control",
            "Qt migration target. This page will be ported after the shell and home page are approved.",
            PlaceholderPage("Axis control", "Planned next: tighter forms and instrument presets."),
        )
        self.add_page(
            "script",
            "Script editor",
            "Qt migration target. The list-based workflow editor can be ported onto this shell next.",
            PlaceholderPage("Script editor", "Planned next: sequence builder, detail panel, and runner handoff."),
        )
        self.add_page(
            "runner",
            "Run script",
            "Qt migration target. This page can reuse the same shell and condensed status patterns.",
            PlaceholderPage("Run script", "Planned next: script execution timeline and live status feed."),
        )
        self.add_page(
            "settings",
            "Settings",
            "Qt migration target. Remaining workspace defaults can be folded into a more compact settings page.",
            PlaceholderPage("Settings", "Planned next: file paths, device defaults, and build/runtime preferences."),
        )
        self.show_page("home")

    def build_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(164)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(10)

        brand = QLabel("Keysight")
        brand.setObjectName("SidebarBrand")
        layout.addWidget(brand)
        sub = QLabel("Automation Studio")
        sub.setObjectName("SidebarSub")
        layout.addWidget(sub)
        layout.addSpacing(10)

        nav_items = [
            ("home", "Home"),
            ("capture", "Capture"),
            ("axis", "Axis"),
            ("script", "Scripts"),
            ("runner", "Runner"),
            ("settings", "Settings"),
        ]
        for key, label in nav_items:
            button = QPushButton(label)
            button.setProperty("nav", True)
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(partial(self.show_page, key))
            layout.addWidget(button)
            self.nav_buttons[key] = button

        layout.addStretch(1)
        footer = QLabel("Qt shell")
        footer.setObjectName("SidebarSub")
        footer.setWordWrap(True)
        layout.addWidget(footer)
        return sidebar

    def build_topbar(self):
        bar = QFrame()
        bar.setObjectName("TopBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.page_title = QLabel("Instrument workspace")
        self.page_title.setObjectName("PageTitle")
        self.page_subtitle = QLabel("Connection setup, workspace defaults and live instrument discovery.")
        self.page_subtitle.setObjectName("PageSubtitle")
        self.page_subtitle.setWordWrap(True)
        title_box.addWidget(self.page_title)
        title_box.addWidget(self.page_subtitle)
        layout.addLayout(title_box, 1)

        self.status_bar = QFrame()
        self.status_bar.setObjectName("StatusBar")
        self.status_bar.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        status_layout = QHBoxLayout(self.status_bar)
        status_layout.setContentsMargins(10, 7, 10, 7)
        status_layout.setSpacing(8)
        meta = QLabel("Connection")
        meta.setObjectName("StatusMeta")
        self.status_text = QLabel("Offline")
        self.status_text.setObjectName("StatusText")
        self.status_text.setProperty("status", "warn")
        self.status_hint = QLabel("Offline mode available")
        self.status_hint.setObjectName("StatusHint")
        reconnect = QPushButton("Reconnect")
        reconnect.setObjectName("GhostButton")
        reconnect.setFixedHeight(30)
        status_layout.addWidget(meta)
        status_layout.addWidget(self.status_text)
        status_layout.addWidget(self.status_hint)
        status_layout.addWidget(reconnect)
        layout.addWidget(self.status_bar, 0, Qt.AlignTop)
        return bar

    def add_page(self, key: str, title: str, subtitle: str, widget: QWidget):
        self.page_titles[key] = (title, subtitle)
        self.pages.addWidget(widget)

    def show_page(self, key: str):
        page_index = list(self.page_titles.keys()).index(key)
        self.pages.setCurrentIndex(page_index)
        title, subtitle = self.page_titles[key]
        self.page_title.setText(title)
        self.page_subtitle.setText(subtitle)
        for name, button in self.nav_buttons.items():
            button.setProperty("active", name == key)
            button.style().unpolish(button)
            button.style().polish(button)
        self.scroll_area.verticalScrollBar().setValue(0)
