import os
import unittest


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication
except ImportError:  # pragma: no cover - optional dependency for migration path
    QApplication = None


@unittest.skipIf(QApplication is None, "PySide6 is not installed")
class QtSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_qt_window_instantiates(self):
        from keysight_software.qt_app.window import MainWindow

        window = MainWindow()
        self.assertEqual(
            set(window.nav_buttons),
            {"home", "capture", "axis", "script", "runner", "batch", "settings"},
        )
        self.assertEqual(window.page_title.text(), "Instrument workspace")
        for key, expected in (
            ("capture", "Waveform capture"),
            ("axis", "Axis control"),
            ("script", "Script editor"),
            ("runner", "Run script"),
            ("batch", "Batch process"),
            ("settings", "Settings"),
        ):
            window.show_page(key)
            self.assertEqual(window.page_title.text(), expected)
        window.close()

    def test_main_entrypoint_uses_qt_app(self):
        import main

        self.assertEqual(main.main.__module__, "keysight_software.qt_app.app")


if __name__ == "__main__":
    unittest.main()
