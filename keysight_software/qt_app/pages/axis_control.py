from __future__ import annotations

import json

from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from keysight_software.paths import config_path
from keysight_software.qt_app.state import AppState
from keysight_software.qt_app.widgets import create_card, create_inline_status, create_log


AXIS_CONFIG_FILE = config_path("axis_config.json")


class AxisControlPage(QWidget):
    def __init__(self, state: AppState):
        super().__init__()
        self.state = state
        self.connection_badge: QLabel | None = None
        self.connection_hint: QLabel | None = None
        self.channels_summary: QLabel | None = None
        self.apply_button: QPushButton | None = None
        self.log_output = create_log(220)
        self.x_scale = self.double_box(0.000001, 1000.0, 6)
        self.x_position = self.double_box(-1000.0, 1000.0, 6)
        self.marker_count = QSpinBox()
        self.marker_count.setRange(1, 2)
        self.marker_fields: list[tuple[QDoubleSpinBox, QDoubleSpinBox]] = []
        self.channel_fields: dict[int, tuple[QDoubleSpinBox, QDoubleSpinBox]] = {}
        self.build_ui()
        self.load_settings()
        self.state.changed.connect(self.refresh_from_state)
        self.refresh_from_state()

    def build_ui(self):
        root = QGridLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setHorizontalSpacing(14)
        root.setVerticalSpacing(14)
        root.setColumnStretch(0, 2)
        root.setColumnStretch(1, 1)

        top = QGridLayout()
        top.setHorizontalSpacing(14)

        time_card, time_layout = create_card("Timebase", "Tune horizontal scale and position before applying channel and marker adjustments.")
        status_shell, self.connection_badge = create_inline_status("Connection", "Disconnected", "warn")
        self.connection_hint = QLabel()
        self.connection_hint.setObjectName("MutedBody")
        self.connection_hint.setWordWrap(True)
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        grid.addWidget(self.label("Scale (s/div)"), 0, 0)
        grid.addWidget(self.label("Position (s)"), 0, 1)
        grid.addWidget(self.x_scale, 1, 0)
        grid.addWidget(self.x_position, 1, 1)
        time_layout.addWidget(status_shell)
        time_layout.addWidget(self.connection_hint)
        time_layout.addLayout(grid)
        top.addWidget(time_card, 0, 0)

        marker_card, marker_layout = create_card("Markers", "Place one or two analysis markers with direct X and Y coordinates.")
        marker_grid = QGridLayout()
        marker_grid.setHorizontalSpacing(12)
        marker_grid.setVerticalSpacing(8)
        marker_grid.addWidget(self.label("Number of Markers"), 0, 0, 1, 2)
        marker_grid.addWidget(self.marker_count, 1, 0, 1, 2)
        for index in range(2):
            x_box = self.double_box(-1000.0, 1000.0, 6)
            y_box = self.double_box(-1000.0, 1000.0, 6)
            marker_grid.addWidget(self.label(f"X Marker {index + 1} (s)"), 2 + index * 2, 0)
            marker_grid.addWidget(self.label(f"Y Marker {index + 1} (V)"), 2 + index * 2, 1)
            marker_grid.addWidget(x_box, 3 + index * 2, 0)
            marker_grid.addWidget(y_box, 3 + index * 2, 1)
            self.marker_fields.append((x_box, y_box))
        marker_layout.addLayout(marker_grid)
        top.addWidget(marker_card, 0, 1)
        root.addLayout(top, 0, 0, 1, 2)

        channels_card, channels_layout = create_card("Channel scaling", "Edit channel presets offline or apply them live when the bench is connected.")
        self.channels_summary = QLabel()
        self.channels_summary.setObjectName("MutedBody")
        self.channels_summary.setWordWrap(True)
        channels_layout.addWidget(self.channels_summary)
        channel_grid = QGridLayout()
        channel_grid.setHorizontalSpacing(12)
        channel_grid.setVerticalSpacing(10)
        for channel in range(1, 5):
            card, card_layout = create_card(f"Channel {channel}")
            scale = self.double_box(0.0, 1000.0, 6)
            position = self.double_box(-1000.0, 1000.0, 6)
            form = QGridLayout()
            form.addWidget(self.label("Scale (V/div)"), 0, 0)
            form.addWidget(self.label("Position (V)"), 0, 1)
            form.addWidget(scale, 1, 0)
            form.addWidget(position, 1, 1)
            card_layout.addLayout(form)
            channel_grid.addWidget(card, (channel - 1) // 2, (channel - 1) % 2)
            self.channel_fields[channel] = (scale, position)
        channels_layout.addLayout(channel_grid)
        actions = QHBoxLayout()
        self.apply_button = QPushButton("Apply Settings")
        self.apply_button.setObjectName("PrimaryButton")
        self.apply_button.clicked.connect(self.apply_settings)
        save_button = QPushButton("Save Preset")
        save_button.setObjectName("GhostButton")
        save_button.clicked.connect(self.save_settings)
        actions.addWidget(self.apply_button)
        actions.addWidget(save_button)
        actions.addStretch(1)
        channels_layout.addLayout(actions)
        root.addWidget(channels_card, 1, 0)

        log_card, log_layout = create_card("Activity log", "Application feedback appears here after loading, saving, or applying axis changes.")
        log_layout.addWidget(self.log_output)
        root.addWidget(log_card, 1, 1)

    def label(self, text: str):
        label = QLabel(text)
        label.setObjectName("MetricLabel")
        return label

    def double_box(self, minimum: float, maximum: float, decimals: int):
        box = QDoubleSpinBox()
        box.setRange(minimum, maximum)
        box.setDecimals(decimals)
        box.setSingleStep(0.1)
        return box

    def log(self, message: str):
        self.log_output.appendPlainText(message)

    def load_settings(self):
        try:
            with open(AXIS_CONFIG_FILE, "r", encoding="utf-8") as handle:
                settings = json.load(handle)
        except FileNotFoundError:
            self.log("No saved settings found.")
            return
        except Exception as error:
            self.log(f"Failed to load settings: {error}")
            return

        timebase = settings.get("timebase", {})
        self.x_scale.setValue(float(timebase.get("scale", 0.01)))
        self.x_position.setValue(float(timebase.get("position", 0.0)))

        channel_settings = settings.get("channels", settings.get("channel_settings", {}))
        for channel in range(1, 5):
            values = channel_settings.get(f"channel_{channel}", {})
            scale, position = self.channel_fields[channel]
            scale.setValue(float(values.get("scale", 0.0)))
            position.setValue(float(values.get("position", 0.0)))

        markers = settings.get("markers", settings.get("marker_positions", []))
        self.marker_count.setValue(max(1, min(len(markers) or 1, 2)))
        for index, (x_box, y_box) in enumerate(self.marker_fields):
            if index < len(markers):
                x_box.setValue(float(markers[index].get("x", 0.0)))
                y_box.setValue(float(markers[index].get("y", 0.0)))
        self.log("Settings loaded successfully.")

    def save_settings(self):
        payload = {
            "timebase": {
                "scale": self.x_scale.value(),
                "position": self.x_position.value(),
            },
            "channels": {},
            "markers": [],
        }
        for channel in range(1, 5):
            scale, position = self.channel_fields[channel]
            payload["channels"][f"channel_{channel}"] = {
                "scale": scale.value(),
                "position": position.value(),
            }
        for index in range(self.marker_count.value()):
            x_box, y_box = self.marker_fields[index]
            payload["markers"].append({"x": x_box.value(), "y": y_box.value()})
        with open(AXIS_CONFIG_FILE, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=4)
        self.log(f"Preset saved to {AXIS_CONFIG_FILE}.")

    def refresh_from_state(self):
        snapshot = self.state.snapshot()
        self.connection_badge.setText(snapshot.label)
        self.connection_badge.setProperty("status", "ok" if snapshot.connected else "warn")
        self.connection_badge.style().unpolish(self.connection_badge)
        self.connection_badge.style().polish(self.connection_badge)
        self.connection_hint.setText(snapshot.summary)
        if snapshot.active_channels:
            channels = ", ".join(f"CH{channel}" for channel in snapshot.active_channels)
            self.channels_summary.setText(f"Active channels: {channels}")
        else:
            self.channels_summary.setText("No live channels detected. You can still edit and save presets offline.")
        self.apply_button.setEnabled(snapshot.connected)

    def apply_settings(self):
        if not self.state.connected or self.state.oscilloscope is None:
            self.log("Apply skipped because no oscilloscope is connected.")
            return
        try:
            osc = self.state.oscilloscope
            osc.set_timebase_scale(self.x_scale.value())
            osc.set_timebase_position(self.x_position.value())
            self.log("Timebase settings applied.")

            active = set(self.state.active_channels)
            for channel in range(1, 5):
                scale, position = self.channel_fields[channel]
                if channel not in active:
                    self.log(f"Channel {channel} skipped because it is not active.")
                    continue
                osc.set_channel_scale(channel, scale.value())
                osc.set_channel_position(channel, position.value())
                self.log(f"Channel {channel} settings applied.")

            if self.marker_count.value() >= 1:
                x_box, y_box = self.marker_fields[0]
                osc.add_marker_x1(x_box.value())
                osc.add_marker_y1(y_box.value())
                self.log("Marker 1 settings applied.")
            if self.marker_count.value() == 2:
                x_box, y_box = self.marker_fields[1]
                osc.add_marker_x2(x_box.value())
                osc.add_marker_y2(y_box.value())
                self.log("Marker 2 settings applied.")

            self.save_settings()
            self.state.refresh_connection()
            self.log("Settings applied and preset saved successfully.")
        except Exception as error:
            self.log(f"Error: {error}")
