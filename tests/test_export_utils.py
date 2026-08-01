import tempfile
import unittest
from pathlib import Path

from lib.export_utils import build_export_path, resolve_bambu_studio_executable, sanitize_filename_component


class ExportUtilsTests(unittest.TestCase):
    def test_sanitize_filename_component(self):
        self.assertEqual(sanitize_filename_component("My Model #1"), "My_Model_1")

    def test_build_export_path(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            export_dir = Path(tmp_dir) / "exports"
            path = build_export_path(export_dir, "My Model #1", "2024-01-01")
            self.assertEqual(path, export_dir / "My_Model_1_2024-01-01.stl")

    def test_resolve_bambu_studio_executable_uses_configured_path(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            executable_path = Path(tmp_dir) / "Bambu Studio.exe"
            executable_path.write_bytes(b"not-a-real-binary")

            self.assertEqual(
                resolve_bambu_studio_executable(str(executable_path)),
                str(executable_path),
            )


if __name__ == "__main__":
    unittest.main()
