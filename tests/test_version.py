import unittest
from updatymeow.version import compare_versions, is_major_update, parse_version_tuple

class TestVersion(unittest.TestCase):
    def test_parse_version_tuple(self):
        self.assertEqual(parse_version_tuple("1.2.3"), (1, 2, 3))
        self.assertEqual(parse_version_tuple("v2.10.4-beta"), (2, 10, 4))
        self.assertEqual(parse_version_tuple("24.04.1"), (24, 4, 1))

    def test_compare_versions(self):
        self.assertLess(compare_versions("1.0.0", "1.0.1"), 0)
        self.assertEqual(compare_versions("2.1.0", "2.1.0"), 0)
        self.assertGreater(compare_versions("3.0.0", "2.9.9"), 0)
        # Debian epoch handling
        self.assertLess(compare_versions("1:1.0", "1:1.1"), 0)

    def test_is_major_update(self):
        self.assertTrue(is_major_update("1.2.3", "2.0.0"))
        self.assertFalse(is_major_update("1.2.3", "1.3.0"))
        self.assertFalse(is_major_update("1.2.3", "1.2.4"))

if __name__ == "__main__":
    unittest.main()

