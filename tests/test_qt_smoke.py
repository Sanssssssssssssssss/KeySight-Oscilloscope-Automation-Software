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
        self.assertGreaterEqual(len(window.nav_buttons), 1)
        self.assertEqual(window.page_title.text(), "Instrument workspace")
        window.show_page("script")
        self.assertEqual(window.page_title.text(), "Script editor")
        window.close()


if __name__ == "__main__":
    unittest.main()

