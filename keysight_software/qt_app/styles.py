APP_STYLESHEET = """
QWidget {
    background: #f6f7f9;
    color: #111827;
    font-family: "Segoe UI";
    font-size: 13px;
}

QMainWindow, #AppShell {
    background: #f6f7f9;
}

#Sidebar {
    background: #fbfbfc;
    border-right: 1px solid #e5e7eb;
}

#SidebarBrand {
    color: #111827;
    font-size: 24px;
    font-weight: 700;
}

#SidebarSub {
    color: #6b7280;
    font-size: 12px;
}

QPushButton[nav="true"] {
    text-align: left;
    padding: 9px 11px;
    border-radius: 12px;
    border: none;
    background: transparent;
    color: #6b7280;
    font-size: 13px;
    font-weight: 600;
}

QPushButton[nav="true"]:hover {
    background: #eff2f6;
    color: #111827;
}

QPushButton[nav="true"][active="true"] {
    background: #e9eef5;
    color: #111827;
}

QFrame#TopBar {
    background: transparent;
}

QLabel#PageTitle {
    font-size: 28px;
    font-weight: 700;
    color: #111827;
}

QLabel#PageSubtitle {
    color: #6b7280;
    font-size: 14px;
}

QFrame#StatusBar, QFrame#InlineStatusCard {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
}

QLabel#StatusMeta {
    color: #6b7280;
    font-size: 12px;
}

QLabel#StatusText {
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 700;
}

QLabel#StatusText[status="ok"] {
    background: #e7f6ec;
    color: #027a48;
}

QLabel#StatusText[status="warn"] {
    background: #fff5e6;
    color: #b54708;
}

QLabel#StatusHint {
    color: #6b7280;
    font-size: 12px;
}

QPushButton#GhostButton {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 7px 12px;
    color: #374151;
    font-weight: 600;
}

QPushButton#GhostButton:hover {
    background: #eff2f6;
}

QPushButton#PrimaryButton {
    background: #111827;
    border: none;
    border-radius: 10px;
    padding: 7px 12px;
    color: white;
    font-weight: 700;
}

QPushButton#PrimaryButton:hover {
    background: #0f172a;
}

QFrame#SurfaceCard {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 18px;
}

QFrame#MetricCard {
    background: #f9fafb;
    border: 1px solid #edf0f3;
    border-radius: 14px;
}

QLabel#SectionTitle {
    color: #111827;
    font-size: 16px;
    font-weight: 700;
}

QLabel#MetricLabel {
    color: #6b7280;
    font-size: 12px;
}

QLabel#MetricValue {
    color: #111827;
    font-size: 14px;
    font-weight: 700;
}

QLabel#MutedBody {
    color: #6b7280;
    font-size: 13px;
}

QLineEdit {
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 10px;
    padding: 9px 11px;
    font-size: 13px;
}

QLineEdit:focus {
    border: 1px solid #111827;
}

QPlainTextEdit {
    background: #fbfbfc;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 10px;
    font-family: "Cascadia Code";
    font-size: 12px;
}
"""

