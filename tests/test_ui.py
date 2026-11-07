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

    def test_sidebar_badges(self):
        items = [
            InstalledItem("apt:curl", "curl", Category.SYSTEM, "apt", "1.0", "1.1"),
            InstalledItem("snap:brave", "brave", Category.APPS, "snap", "1.0", "1.1"),
            InstalledItem("snap:firefox", "firefox", Category.APPS, "snap", "120.0", "120.0", status=Status.UP_TO_DATE),
        ]
        self.window.set_items(items)
        self.assertIn("(2)", self.window.sidebar.item(0).text())
        self.assertIn("(1)", self.window.sidebar.item(1).text())
        self.assertIn("(1)", self.window.sidebar.item(2).text())
        self.assertEqual(self.window.sidebar.item(3).text(), "Runtimes")

    def test_run_updates_cancel_sudo(self):
        item = InstalledItem("apt:curl", "curl", Category.SYSTEM, "apt", "1.0", "1.1", update_command="sudo apt-get install curl")
        with unittest.mock.patch("PyQt5.QtWidgets.QInputDialog.getText", return_value=("", False)):
            with unittest.mock.patch("subprocess.run") as mock_sub:
                mock_sub.return_value.returncode = 1
                self.window._run_updates([item])
                self.assertIn("cancelled", self.window.status_label.text().lower())

    def test_settings_dialog(self):
        from updatymeow.ui import SettingsDialog
        dialog = SettingsDialog(self.window, store=self.store)
        self.assertIsNotNone(dialog)
        self.assertEqual(dialog.interval_combo.currentText(), "Every 6 hours")
        dialog.close()

    def test_about_dialog(self):
        from updatymeow.ui import AboutDialog
        dialog = AboutDialog(self.window)
        self.assertIsNotNone(dialog)
        self.assertIn("About UpdatyMeow", dialog.windowTitle())
        dialog.close()

    def test_tray_menu_rebuild(self):
        items = [
            InstalledItem("apt:curl", "curl", Category.SYSTEM, "apt", "1.0", "1.1"),
        ]
        self.window.set_items(items)
        self.window._rebuild_tray_menu()
        actions = [a.text() for a in self.window.tray_menu.actions()]
        self.assertTrue(any("UpdatyMeow" in a for a in actions))
        self.assertTrue(any("1 update(s) available" in a for a in actions))
        self.assertTrue(any("Update All" in a for a in actions))
        self.assertTrue(any("About UpdatyMeow" in a for a in actions))

if __name__ == "__main__":
    unittest.main()

