import unittest
from unittest.mock import patch
from updatymeow.cli import main
from updatymeow.models import InstalledItem, Category, Status

class TestCLI(unittest.TestCase):
    @patch("updatymeow.cli.scan_all_ecosystems")
    def test_cli_check_mode(self, mock_scan):
        mock_scan.return_value = [
            InstalledItem("apt:curl", "curl", Category.SYSTEM, "apt", "1.0", "1.1"),
        ]
        ret = main(["--check"])
        self.assertEqual(ret, 0)

if __name__ == "__main__":
    unittest.main()
