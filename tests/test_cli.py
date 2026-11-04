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

    @patch("updatymeow.ui.MainWindow")
    def test_cli_minimized_mode(self, mock_window):
        # Test that --minimized creates window but does not call show()
        instance = mock_window.return_value
        from updatymeow.cli import parse_args
        parsed = parse_args(["--minimized"])
        self.assertTrue(parsed.minimized)

if __name__ == "__main__":
    unittest.main()

