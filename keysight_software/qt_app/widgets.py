from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
)


def create_card(title: str, subtitle: str = "") -> tuple[QFrame, QVBoxLayout]:
    card = QFrame()
    card.setObjectName("SurfaceCard")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(18, 16, 18, 16)
    layout.setSpacing(12)

    heading = QLabel(title)
    heading.setObjectName("SectionTitle")
    layout.addWidget(heading)

    if subtitle:
        body = QLabel(subtitle)
        body.setObjectName("MutedBody")
        body.setWordWrap(True)
        layout.addWidget(body)

    return card, layout


def create_metric_card(label_text: str, value_text: str) -> tuple[QFrame, QLabel]:
    card = QFrame()
    card.setObjectName("MetricCard")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(14, 12, 14, 12)
    layout.setSpacing(4)

    label = QLabel(label_text)
    label.setObjectName("MetricLabel")
    value = QLabel(value_text)
    value.setObjectName("MetricValue")
    value.setWordWrap(True)
    layout.addWidget(label)
    layout.addWidget(value)
    return card, value


def create_inline_status(meta_text: str, status_text: str, status_kind: str = "warn") -> tuple[QFrame, QLabel]:
    card = QFrame()
    card.setObjectName("InlineStatusCard")
    layout = QHBoxLayout(card)
    layout.setContentsMargins(10, 8, 10, 8)
    layout.setSpacing(8)

    meta = QLabel(meta_text)
    meta.setObjectName("StatusMeta")
    status = QLabel(status_text)
    status.setObjectName("StatusText")
    status.setProperty("status", status_kind)
    layout.addWidget(meta)
    layout.addWidget(status)
    layout.addStretch(1)
    return card, status


def create_log(height: int = 160) -> QPlainTextEdit:
    log = QPlainTextEdit()
    log.setObjectName("LogView")
    log.setReadOnly(True)
    log.setMinimumHeight(height)
    return log
