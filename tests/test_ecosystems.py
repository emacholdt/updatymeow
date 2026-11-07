import unittest
from updatymeow.ecosystems import (
    parse_apt_upgradable,
    parse_snap_refresh_list,
    parse_flatpak_updates,
    parse_npm_outdated,
    parse_pip_outdated,
)
from updatymeow.models import Category, InstalledItem, Status

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
        self.assertEqual(items[0].update_command, "sudo snap refresh firefox")

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
        items = parse_pip_outdated(sample_json, is_user=False)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].id, "pip:black")
        self.assertEqual(items[0].name, "black")
        self.assertEqual(items[0].category, Category.PACKAGES)
        self.assertEqual(items[0].installed_version, "23.1.0")
        self.assertEqual(items[0].latest_version, "24.1.0")
        self.assertEqual(items[0].update_command, "pip install -U black")

        user_items = parse_pip_outdated(sample_json, is_user=True)
        self.assertEqual(user_items[0].update_command, "pip install --user -U black")

    def test_parse_custom_tools(self):
        from updatymeow.ecosystems import parse_custom_tools
        sample = """[
            {
                "id": "custom:foo",
                "name": "FooCLI",
                "installed_version": "1.0.0",
                "latest_version": "1.2.0",
                "update_command": "foo update"
            }
        ]"""
        items = parse_custom_tools(sample)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].name, "FooCLI")
        self.assertEqual(items[0].category, Category.TOOLS)
        self.assertEqual(items[0].status, Status.OUTDATED)

    def test_parse_snap_inventory(self):
        from updatymeow.ecosystems import parse_snap_inventory
        list_out = """Name     Version   Rev    Tracking  Publisher   Notes
brave    1.98.60   698    latest    brave✓      -
firefox  125.0.1   9171   latest    mozilla✓    -
spotify  1.2.0     99     latest    spotify✓    -
"""
        refresh_out = """Name   Version  Rev  Size   Publisher  Notes
brave  1.99.55  705  234MB  brave✓     -
"""
        items = parse_snap_inventory(list_out, refresh_out)
        self.assertEqual(len(items), 3)
        brave = next(i for i in items if i.name == "brave")
        firefox = next(i for i in items if i.name == "firefox")
        spotify = next(i for i in items if i.name == "spotify")

        self.assertEqual(brave.status, Status.OUTDATED)
        self.assertEqual(brave.installed_version, "1.98.60")
        self.assertEqual(brave.latest_version, "1.99.55")
        self.assertIn("snap refresh brave", brave.update_command)

        self.assertEqual(firefox.status, Status.UP_TO_DATE)
        self.assertEqual(firefox.installed_version, "125.0.1")
        self.assertEqual(firefox.latest_version, "125.0.1")
        self.assertEqual(firefox.update_command, "")

        self.assertEqual(spotify.status, Status.UP_TO_DATE)

    def test_parse_flatpak_inventory(self):
        from updatymeow.ecosystems import parse_flatpak_inventory
        list_out = """Application ID\tVersion\tName
com.bambulab.BambuStudio\t2.8.2\tBambu Studio
org.gnome.baobab\t50.0\tDisk Usage Analyzer
"""
        updates_out = """com.bambulab.BambuStudio\t2.9.0
"""
        items = parse_flatpak_inventory(list_out, updates_out)
        self.assertEqual(len(items), 2)
        bambu = next(i for i in items if "BambuStudio" in i.id)
        baobab = next(i for i in items if "baobab" in i.id)

        self.assertEqual(bambu.status, Status.OUTDATED)
        self.assertEqual(bambu.installed_version, "2.8.2")
        self.assertEqual(bambu.latest_version, "2.9.0")
        self.assertIn("flatpak update -y", bambu.update_command)

        self.assertEqual(baobab.status, Status.UP_TO_DATE)
        self.assertEqual(baobab.installed_version, "50.0")
        self.assertEqual(baobab.update_command, "")

    def test_parse_apt_inventory(self):
        from updatymeow.ecosystems import parse_apt_inventory
        upgradable_out = """Listing... Done
curl/noble-updates 7.88.1-10ubuntu2.6 amd64 [upgradable from: 7.88.1-10ubuntu2.5]
"""
        manual_names = {"curl", "git", "vim"}
        installed_pkgs = {"curl": "7.88.1-10ubuntu2.5", "git": "2.43.0", "vim": "9.1.0"}
        items = parse_apt_inventory(upgradable_out, manual_names, installed_pkgs)

        self.assertEqual(len(items), 3)
        curl = next(i for i in items if i.name == "curl")
        git = next(i for i in items if i.name == "git")

        self.assertEqual(curl.status, Status.OUTDATED)
        self.assertEqual(curl.installed_version, "7.88.1-10ubuntu2.5")
        self.assertEqual(curl.latest_version, "7.88.1-10ubuntu2.6")

        self.assertEqual(git.status, Status.UP_TO_DATE)
        self.assertEqual(git.installed_version, "2.43.0")
        self.assertEqual(git.latest_version, "2.43.0")

    def test_build_batch_update_commands(self):
        from updatymeow.ecosystems import build_batch_update_commands
        items = [
            InstalledItem("apt:curl", "curl", Category.SYSTEM, "apt", "1.0", "1.1"),
            InstalledItem("apt:git", "git", Category.SYSTEM, "apt", "2.0", "2.1"),
            InstalledItem("snap:brave", "brave", Category.APPS, "snap", "1.0", "1.1"),
            InstalledItem("snap:firefox", "firefox", Category.APPS, "snap", "120.0", "121.0"),
            InstalledItem("flatpak:org.foo", "org.foo", Category.APPS, "flatpak", "1.0", "2.0"),
        ]
        batches = build_batch_update_commands(items, elevate="sudo")
        self.assertEqual(len(batches), 3)

        apt_cmd, apt_ids = next(b for b in batches if "apt-get" in b[0])
        snap_cmd, snap_ids = next(b for b in batches if "snap refresh" in b[0])
        flat_cmd, flat_ids = next(b for b in batches if "flatpak update" in b[0])

        self.assertIn("curl git", apt_cmd)
        self.assertEqual(apt_ids, ["apt:curl", "apt:git"])

        self.assertIn("brave firefox", snap_cmd)
        self.assertEqual(snap_ids, ["snap:brave", "snap:firefox"])

        self.assertIn("org.foo", flat_cmd)
        self.assertEqual(flat_ids, ["flatpak:org.foo"])

if __name__ == "__main__":
    unittest.main()

