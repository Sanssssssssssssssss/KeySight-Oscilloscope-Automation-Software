APP_STYLESHEET = """
QWidget {
    background: #f4f6fb;
    color: #101828;
    font-family: "Segoe UI";
    font-size: 13px;
}

QMainWindow {
    background: #f4f6fb;
}

#AppShell {
    background: #f4f6fb;
}

#Sidebar {
    background: #ffffff;
    border-right: 1px solid #e4e7ec;
}

#SidebarBrand {
    color: #111827;
    font-size: 26px;
    font-weight: 700;
}

#SidebarSub {
    color: #667085;
    font-size: 12px;
}

QPushButton[nav="true"] {
    text-align: left;
    padding: 10px 12px;
    border-radius: 14px;
    border: none;
    background: transparent;
    color: #667085;
    font-size: 13px;
    font-weight: 600;
}

QPushButton[nav="true"]:hover {
    background: #eef4ff;
    color: #175cd3;
}

QPushButton[nav="true"][active="true"] {
    background: #e6efff;
    color: #175cd3;
}

QFrame#TopBar {
    background: transparent;
}

QLabel#PageTitle {
    font-size: 30px;
    font-weight: 700;
    color: #101828;
}

QLabel#PageSubtitle {
    color: #667085;
    font-size: 14px;
}

QFrame#StatusBar {
    background: #ffffff;
    border: 1px solid #e4e7ec;
    border-radius: 16px;
}

QLabel#StatusMeta {
    color: #667085;
    font-size: 12px;
}

QLabel#StatusText {
    padding: 5px 10px;
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
    color: #667085;
    font-size: 12px;
}

QPushButton#GhostButton {
    background: #f8fafc;
    border: 1px solid #e4e7ec;
    border-radius: 12px;
    padding: 8px 14px;
    color: #344054;
    font-weight: 600;
}

QPushButton#GhostButton:hover {
    background: #eef2f7;
}

QPushButton#PrimaryButton {
    background: #175cd3;
    border: none;
    border-radius: 12px;
    padding: 8px 14px;
    color: white;
    font-weight: 700;
}

QPushButton#PrimaryButton:hover {
    background: #1849a9;
}

QFrame#HeroCard, QFrame#SurfaceCard, QFrame#DarkCard {
    border-radius: 24px;
}

QFrame#HeroCard {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 #f8fbff, stop:0.55 #eef4ff, stop:1 #dbeafe);
    border: 1px solid #dbe7ff;
}

QFrame#SurfaceCard {
    background: #ffffff;
    border: 1px solid #e4e7ec;
}

QFrame#DarkCard {
    background: #101828;
    border: 1px solid #0f172a;
}

QLabel#Eyebrow {
    color: #175cd3;
    font-size: 12px;
    font-weight: 700;
}

QLabel#HeroTitle {
    color: #101828;
    font-size: 26px;
    font-weight: 700;
}

QLabel#HeroBody, QLabel#MutedBody {
    color: #667085;
    font-size: 13px;
}

QFrame#MetricCard {
    background: rgba(255, 255, 255, 0.75);
    border: 1px solid rgba(219, 234, 254, 0.9);
    border-radius: 18px;
}

QLabel#MetricLabel {
    color: #667085;
    font-size: 12px;
}

QLabel#MetricValue {
    color: #111827;
    font-size: 14px;
    font-weight: 700;
}

QLabel#DarkTitle {
    color: #ffffff;
    font-size: 15px;
    font-weight: 700;
}

QLabel#DarkBody {
    color: #cbd5e1;
    font-size: 13px;
}

QLineEdit {
    background: #ffffff;
    border: 1px solid #d0d5dd;
    border-radius: 12px;
    padding: 10px 12px;
    font-size: 13px;
}

QLineEdit:focus {
    border: 1px solid #175cd3;
}

QPlainTextEdit {
    background: #fbfcfe;
    border: 1px solid #d0d5dd;
    border-radius: 16px;
    padding: 10px;
    font-family: "Cascadia Code";
    font-size: 12px;
}
"""

