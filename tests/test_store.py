import unittest
import tempfile
import os
import shutil
from pathlib import Path
from updatymeow.store import Store
from updatymeow.models import InstalledItem, Category, Status, UpdateRecord

class TestStore(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.store = Store(config_dir=Path(self.test_dir))

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_pin_and_favorite(self):
        self.assertFalse(self.store.is_pinned("apt:curl"))
        self.store.pin("apt:curl")
        self.assertTrue(self.store.is_pinned("apt:curl"))

        self.assertFalse(self.store.is_favorite("apt:curl"))
        self.store.favorite("apt:curl")
        self.assertTrue(self.store.is_favorite("apt:curl"))

        # Test reload persistence
        store2 = Store(config_dir=Path(self.test_dir))
        self.assertTrue(store2.is_pinned("apt:curl"))
        self.assertTrue(store2.is_favorite("apt:curl"))

        self.store.unpin("apt:curl")
        self.assertFalse(self.store.is_pinned("apt:curl"))
        self.store.unfavorite("apt:curl")
        self.assertFalse(self.store.is_favorite("apt:curl"))

    def test_history(self):
        self.assertEqual(len(self.store.get_history()), 0)
        rec = UpdateRecord(
            timestamp="2026-11-04T23:00:00",
            item_id="apt:curl",
            item_name="curl",
            from_version="1.0",
            to_version="1.1",
            success=True,
            output="Done"
        )
        self.store.add_history(rec)
        history = self.store.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].item_id, "apt:curl")

    def test_apply_preferences(self):
        self.store.pin("apt:git")
        self.store.favorite("apt:curl")
        items = [
            InstalledItem("apt:git", "git", Category.SYSTEM, "apt", "1.0", "1.1"),
            InstalledItem("apt:curl", "curl", Category.SYSTEM, "apt", "1.0", "1.1")
        ]
        self.store.apply_preferences(items)
        self.assertTrue(items[0].is_pinned)
        self.assertEqual(items[0].status, Status.PINNED)
        self.assertTrue(items[1].is_favorite)

    def test_settings_persistence(self):
        settings = self.store.get_settings()
        self.assertEqual(settings.get("check_interval"), "6h")
        settings["check_interval"] = "12h"
        self.store.save_settings(settings)

        store2 = Store(config_dir=Path(self.test_dir))
        self.assertEqual(store2.get_settings().get("check_interval"), "12h")

    def test_autostart_toggle(self):
        autostart_dir = Path(self.test_dir) / "autostart"
        self.store.autostart_dir = autostart_dir
        self.assertFalse(self.store.is_autostart_enabled())
        self.store.set_autostart(True)
        self.assertTrue(self.store.is_autostart_enabled())
        self.store.set_autostart(False)
        self.assertFalse(self.store.is_autostart_enabled())

if __name__ == "__main__":
    unittest.main()

