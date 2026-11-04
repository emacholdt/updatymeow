import unittest
from updatymeow.models import Category, Status, InstalledItem, UpdateRecord

class TestModels(unittest.TestCase):
    def test_installed_item_status_derivation(self):
        item = InstalledItem(
            id="apt:curl",
            name="curl",
            category=Category.SYSTEM,
            ecosystem="apt",
            installed_version="7.81.0",
            latest_version="7.88.0",
            update_command="sudo apt-get install --only-upgrade curl -y"
        )
        self.assertEqual(item.status, Status.OUTDATED)
        self.assertFalse(item.is_major)

    def test_installed_item_major_update(self):
        item = InstalledItem(
            id="npm:vite",
            name="vite",
            category=Category.PACKAGES,
            ecosystem="npm",
            installed_version="4.5.0",
            latest_version="5.0.0",
            update_command="npm install -g vite@latest"
        )
        self.assertEqual(item.status, Status.OUTDATED)
        self.assertTrue(item.is_major)

    def test_installed_item_up_to_date(self):
        item = InstalledItem(
            id="snap:firefox",
            name="firefox",
            category=Category.APPS,
            ecosystem="snap",
            installed_version="125.0",
            latest_version="125.0",
            update_command="snap refresh firefox"
        )
        self.assertEqual(item.status, Status.UP_TO_DATE)

    def test_installed_item_pinned(self):
        item = InstalledItem(
            id="flatpak:org.gimp.GIMP",
            name="GIMP",
            category=Category.APPS,
            ecosystem="flatpak",
            installed_version="2.10.36",
            latest_version="3.0.0",
            is_pinned=True,
            update_command="flatpak update org.gimp.GIMP -y"
        )
        self.assertEqual(item.status, Status.PINNED)

    def test_update_record(self):
        rec = UpdateRecord(
            timestamp="2026-11-04T23:00:00",
            item_id="apt:curl",
            item_name="curl",
            from_version="7.81.0",
            to_version="7.88.0",
            success=True,
            output="Unpacking curl..."
        )
        data = rec.to_dict()
        self.assertTrue(data["success"])
        restored = UpdateRecord.from_dict(data)
        self.assertEqual(restored.item_id, "apt:curl")

if __name__ == "__main__":
    unittest.main()
