import unittest
from unittest import mock

import tkinter as tk

from keysight_software.ui.dialogs.axis_control_config import AxisControlConfig
from keysight_software.ui.dialogs.waveform_config import WaveformConfig
from keysight_software.ui.main_window import MainGUI
from keysight_software.ui.pages.axis_control import AxisControlPage
from keysight_software.ui.pages.batch_process import BatchProcessPage
from keysight_software.ui.pages.home import ConfigHome
from keysight_software.ui.pages.run_script import RunScriptPage
from keysight_software.ui.pages.script_editor import ScriptEditor
from keysight_software.ui.pages.settings import Setting
from keysight_software.ui.pages.waveform_capture import WaveformCapture


class FakeOscilloscope:
    def get_active_channels(self):
        return [1, 2]

    def capture_waveform(self, channel=1):
        return [0.0, 0.1, 0.2], [channel, channel + 0.1, channel + 0.2]

    def plot_all_waveforms(self, waveforms, ax, canvas):
        ax.clear()
        for channel, (time_values, waveform_data) in waveforms.items():
            ax.plot(time_values, waveform_data, label=f"CH{channel}")
        if canvas is not None:
            canvas.draw()

    def capture_screenshot(self, filename):
        return filename

    def set_timebase_scale(self, scale):
        return scale

    def set_timebase_position(self, position):
        return position

    def set_channel_scale(self, channel, scale):
        return channel, scale

    def set_channel_position(self, channel, position):
        return channel, position

    def add_marker_x1(self, value):
        return value

    def add_marker_y1(self, value):
        return value

    def add_marker_x2(self, value):
        return value

    def add_marker_y2(self, value):
        return value


class FakeMeasure:
    def measure_phase(self, channel_1, channel_2):
        return 45.0

    def __getattr__(self, _name):
        return lambda *_args, **_kwargs: 1.23


class UITests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.messagebox_info = mock.patch("tkinter.messagebox.showinfo")
        self.messagebox_error = mock.patch("tkinter.messagebox.showerror")
        self.messagebox_warning = mock.patch("tkinter.messagebox.showwarning")
        self.messagebox_info.start()
        self.messagebox_error.start()
        self.messagebox_warning.start()

    def tearDown(self):
        self.messagebox_info.stop()
        self.messagebox_error.stop()
        self.messagebox_warning.stop()
        self.root.destroy()

    def test_main_window_instantiates(self):
        with mock.patch.object(MainGUI, "initialize_connection", lambda self: None):
            gui = MainGUI(self.root)
        self.assertIsNotNone(gui.display_frame)
        self.assertGreaterEqual(len(gui.nav_buttons), 1)

    def test_primary_pages_instantiates(self):
        pages = [
            ConfigHome(self.root),
            Setting(self.root),
            BatchProcessPage(self.root),
            AxisControlPage(self.root, FakeOscilloscope()),
            RunScriptPage(self.root),
            ScriptEditor(self.root),
            WaveformCapture(self.root, FakeOscilloscope(), FakeMeasure()),
        ]
        self.assertEqual(len(pages), 7)

    def test_dialogs_instantiates(self):
        dialog_root = tk.Toplevel(self.root)
        dialog_root.withdraw()
        axis = AxisControlConfig(dialog_root)
        wave = WaveformConfig(dialog_root)
        self.assertIsNotNone(axis)
        self.assertIsNotNone(wave)
        dialog_root.destroy()


if __name__ == "__main__":
    unittest.main()
