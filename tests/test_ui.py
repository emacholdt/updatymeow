import unittest
import os
from PyQt5.QtWidgets import QApplication

# Run in offscreen mode for test suites
os.environ["QT_QPA_PLATFORM"] = "offscreen"

app = QApplication.instance()
if app is None:
    app = QApplication([])

from updatymeow.ui import MainWindow
from updatymeow.models import InstalledItem, Category, Status
from updatymeow.store import Store
import tempfile
import shutil
from pathlib import Path

class TestUI(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.store = Store(config_dir=Path(self.test_dir))
        self.window = MainWindow(store=self.store)

    def tearDown(self):
        self.window.close()
        shutil.rmtree(self.test_dir)

    def test_window_initialization(self):
        self.assertIn("UpdatyMeow", self.window.windowTitle())
        self.assertIsNotNone(self.window.sidebar)
        self.assertIsNotNone(self.window.table)

    def test_set_items_and_filtering(self):
        items = [
            InstalledItem("apt:curl", "curl", Category.SYSTEM, "apt", "1.0", "1.1"),
            InstalledItem("snap:firefox", "firefox", Category.APPS, "snap", "120.0", "120.0"),
        ]
        self.window.set_items(items)
        self.assertEqual(self.window.table.rowCount(), 2)

        # Test search filter
        self.window.search_input.setText("curl")
        visible_rows = [r for r in range(self.window.table.rowCount()) if not self.window.table.isRowHidden(r)]
        self.assertEqual(len(visible_rows), 1)

if __name__ == "__main__":
    unittest.main()
