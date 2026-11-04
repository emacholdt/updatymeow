import unittest
from updatymeow.runner import execute_command

class TestRunner(unittest.TestCase):
    def test_execute_echo_command(self):
        lines = []
        code, out = execute_command("echo 'Updating package...'", on_output=lines.append)
        self.assertEqual(code, 0)
        self.assertIn("Updating package...", out)
        self.assertEqual(lines, ["Updating package..."])

    def test_execute_failed_command(self):
        code, out = execute_command("false")
        self.assertNotEqual(code, 0)

    def test_execute_with_stdin_input(self):
        lines = []
        code, out = execute_command("cat", on_output=lines.append, sudo_password="secret_pass")
        self.assertEqual(code, 0)
        self.assertIn("secret_pass", out)

if __name__ == "__main__":
    unittest.main()

