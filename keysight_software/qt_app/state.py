from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal

from keysight_software import config
from keysight_software.device.measure import Measure
from keysight_software.device.oscilloscope import Oscilloscope


@dataclass
class ConnectionSnapshot:
    connected: bool
    label: str
    summary: str
    identity: str = ""
    error: str = ""
    active_channels: tuple[int, ...] = ()


class AppState(QObject):
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.oscilloscope: Oscilloscope | None = None
        self.measure: Measure | None = None
        self.identity = ""
        self.error = ""
        self.active_channels: tuple[int, ...] = ()

    @property
    def connected(self) -> bool:
        return self.oscilloscope is not None and self.measure is not None

    def snapshot(self) -> ConnectionSnapshot:
        if self.connected:
            summary = "Live capture and execution are available."
            if self.identity:
                summary = f"{summary} {self.identity}"
            return ConnectionSnapshot(
                connected=True,
                label="Connected",
                summary=summary,
                identity=self.identity,
                active_channels=self.active_channels,
            )
        if self.error:
            return ConnectionSnapshot(
                connected=False,
                label="Disconnected",
                summary=self.error,
                error=self.error,
                active_channels=self.active_channels,
            )
        return ConnectionSnapshot(
            connected=False,
            label="Disconnected",
            summary="Offline mode is active. Live capture controls will stay disabled.",
            active_channels=self.active_channels,
        )

    def connect_scope(self, visa_address: str | None = None, timeout: int | None = None) -> bool:
        address = (visa_address or config.VISA_ADDRESS).strip()
        timeout_value = timeout if timeout is not None else config.GLOBAL_TIMEOUT
        try:
            timeout_value = int(timeout_value)
        except (TypeError, ValueError):
            self.error = "Timeout must be an integer value in milliseconds."
            self.changed.emit()
            return False

        config.update_visa_address(address)
        config.update_global_timeout(timeout_value)
        self.close_scope()

        try:
            self.oscilloscope = Oscilloscope(address, timeout_value)
            self.measure = Measure(self.oscilloscope)
            self.identity = self.oscilloscope.get_idn().strip()
            self.active_channels = tuple(self.oscilloscope.get_active_channels())
            self.error = ""
            self.changed.emit()
            return True
        except Exception as error:
            self.close_scope()
            self.error = str(error)
            self.changed.emit()
            return False

    def refresh_connection(self) -> bool:
        if not self.connected:
            self.changed.emit()
            return False
        try:
            self.active_channels = tuple(self.oscilloscope.get_active_channels())
            self.identity = self.oscilloscope.get_idn().strip()
            self.error = ""
            self.changed.emit()
            return True
        except Exception as error:
            self.close_scope()
            self.error = str(error)
            self.changed.emit()
            return False

    def close_scope(self):
        if self.oscilloscope is not None:
            try:
                self.oscilloscope.close()
            except Exception:
                pass
        self.oscilloscope = None
        self.measure = None
        self.identity = ""
        self.active_channels = ()
