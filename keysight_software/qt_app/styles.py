APP_STYLESHEET = """
QWidget {
    background: #f5f6f8;
    color: #111827;
    font-family: "Segoe UI";
    font-size: 13px;
}

QMainWindow, #AppShell {
    background: #f5f6f8;
}

#Sidebar {
    background: #fbfbfc;
    border-right: 1px solid #e7eaf0;
}

#SidebarBrand {
    color: #111827;
    font-size: 23px;
    font-weight: 700;
}

#SidebarSub {
    color: #6b7280;
    font-size: 11px;
}

QPushButton[nav="true"] {
    text-align: left;
    padding: 8px 10px;
    border-radius: 11px;
    border: none;
    background: transparent;
    color: #6b7280;
    font-size: 12px;
    font-weight: 600;
}

QPushButton[nav="true"]:hover {
    background: #eef2f7;
    color: #111827;
}

QPushButton[nav="true"][active="true"] {
    background: #e7edf6;
    color: #111827;
}

QFrame#TopBar {
    background: transparent;
}

QLabel#PageTitle {
    font-size: 26px;
    font-weight: 700;
    color: #111827;
}

QLabel#PageSubtitle {
    color: #6b7280;
    font-size: 13px;
}

QFrame#StatusBar, QFrame#InlineStatusCard {
    background: rgba(255, 255, 255, 0.94);
    border: 1px solid #e5e7eb;
    border-radius: 14px;
}

QLabel#StatusMeta {
    color: #6b7280;
    font-size: 11px;
}

QLabel#StatusText {
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 11px;
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
    font-size: 11px;
}

QPushButton#GhostButton {
    background: #f8fafc;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 7px 11px;
    color: #374151;
    font-weight: 600;
}

QPushButton#GhostButton:hover {
    background: #eef2f7;
}

QPushButton#PrimaryButton {
    background: #111827;
    border: none;
    border-radius: 10px;
    padding: 7px 11px;
    color: white;
    font-weight: 700;
}

QPushButton#PrimaryButton:hover {
    background: #0f172a;
}

QFrame#SurfaceCard {
    background: rgba(255, 255, 255, 0.96);
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
    font-size: 15px;
    font-weight: 700;
}

QLabel#MetricLabel {
    color: #6b7280;
    font-size: 11px;
}

QLabel#MetricValue {
    color: #111827;
    font-size: 13px;
    font-weight: 700;
}

QLabel#MutedBody {
    color: #6b7280;
    font-size: 12px;
}

QLineEdit,
QListWidget,
QPlainTextEdit,
QComboBox,
QAbstractSpinBox {
    background: #fbfbfc;
    border: 1px solid #d8dde6;
    border-radius: 10px;
    padding: 8px 10px;
    font-size: 12px;
}

QLineEdit:focus,
QListWidget:focus,
QPlainTextEdit:focus,
QComboBox:focus,
QAbstractSpinBox:focus {
    border: 1px solid #111827;
}

QListWidget {
    padding: 6px;
}

QListWidget::item {
    padding: 9px 10px;
    border-radius: 9px;
}

QListWidget::item:selected {
    background: #e7edf6;
    color: #111827;
}

QPlainTextEdit, #LogView {
    font-family: "Cascadia Code";
    font-size: 11px;
}

QCheckBox {
    spacing: 7px;
    color: #374151;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 5px;
    border: 1px solid #cfd5df;
    background: white;
}

QCheckBox::indicator:checked {
    background: #111827;
    border: 1px solid #111827;
}
"""
