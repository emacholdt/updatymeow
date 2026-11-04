import unittest
from updatymeow.ecosystems import (
    parse_apt_upgradable,
    parse_snap_refresh_list,
    parse_flatpak_updates,
    parse_npm_outdated,
    parse_pip_outdated,
)
from updatymeow.models import Category, Status

class TestEcosystems(unittest.TestCase):
    def test_parse_apt_upgradable(self):
        sample_output = """Listing... Done
curl/noble-updates 7.88.1-10ubuntu2.6 amd64 [upgradable from: 7.88.1-10ubuntu2.5]
git/noble-security 1:2.43.0-1ubuntu7.1 amd64 [upgradable from: 1:2.43.0-1ubuntu7]
"""
        items = parse_apt_upgradable(sample_output)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].id, "apt:curl")
        self.assertEqual(items[0].name, "curl")
        self.assertEqual(items[0].category, Category.SYSTEM)
        self.assertEqual(items[0].installed_version, "7.88.1-10ubuntu2.5")
        self.assertEqual(items[0].latest_version, "7.88.1-10ubuntu2.6")
        self.assertEqual(items[0].status, Status.OUTDATED)
        self.assertIn("apt-get install --only-upgrade -y curl", items[0].update_command)

    def test_parse_snap_refresh_list(self):
        sample_output = """Name     Version   Rev    Size   Publisher   Notes
firefox  125.0.2   4173   260MB  mozilla✓    -
lxd      5.21.1    28400  95MB   canonical✓  -
"""
        items = parse_snap_refresh_list(sample_output)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].id, "snap:firefox")
        self.assertEqual(items[0].name, "firefox")
        self.assertEqual(items[0].category, Category.APPS)
        self.assertEqual(items[0].latest_version, "125.0.2")
        self.assertEqual(items[0].update_command, "snap refresh firefox")

    def test_parse_flatpak_updates(self):
        sample_output = """org.mozilla.firefox\t125.0.1\t125.0.2
org.gimp.GIMP\t2.10.36\t2.10.38
"""
        items = parse_flatpak_updates(sample_output)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].id, "flatpak:org.mozilla.firefox")
        self.assertEqual(items[0].name, "org.mozilla.firefox")
        self.assertEqual(items[0].category, Category.APPS)
        self.assertEqual(items[0].installed_version, "125.0.1")
        self.assertEqual(items[0].latest_version, "125.0.2")
        self.assertEqual(items[0].update_command, "flatpak update -y org.mozilla.firefox")

    def test_parse_npm_outdated(self):
        sample_json = """{
            "vite": {
                "current": "5.0.0",
                "wanted": "5.2.0",
                "latest": "5.2.0",
                "location": "/usr/local/lib/node_modules/vite"
            }
        }"""
        items = parse_npm_outdated(sample_json)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].id, "npm:vite")
        self.assertEqual(items[0].name, "vite")
        self.assertEqual(items[0].category, Category.PACKAGES)
        self.assertEqual(items[0].installed_version, "5.0.0")
        self.assertEqual(items[0].latest_version, "5.2.0")
        self.assertEqual(items[0].update_command, "npm install -g vite@latest")

    def test_parse_pip_outdated(self):
        sample_json = """[
            {"name": "black", "version": "23.1.0", "latest_version": "24.1.0"}
        ]"""
        items = parse_pip_outdated(sample_json)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].id, "pip:black")
        self.assertEqual(items[0].name, "black")
        self.assertEqual(items[0].category, Category.PACKAGES)
        self.assertEqual(items[0].installed_version, "23.1.0")
        self.assertEqual(items[0].latest_version, "24.1.0")
        self.assertEqual(items[0].update_command, "pip install -U black")

if __name__ == "__main__":
    unittest.main()
