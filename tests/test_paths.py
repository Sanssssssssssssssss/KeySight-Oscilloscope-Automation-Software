import tempfile
import unittest
from pathlib import Path

from keysight_software import paths


class PathsTests(unittest.TestCase):
    def test_config_path_copies_bundled_default_to_writable_configs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            project_root = temp_root / "runtime"
            bundle_root = temp_root / "bundle"
            project_root.mkdir()
            (bundle_root / "configs").mkdir(parents=True)
            bundled_file = bundle_root / "configs" / "waveform_config.json"
            bundled_file.write_text('{"source":"bundle"}', encoding="utf-8")

            original_project_root = paths.PROJECT_ROOT
            original_bundle_root = paths.BUNDLE_ROOT
            original_configs_dir = paths.CONFIGS_DIR
            original_bundled_configs_dir = paths.BUNDLED_CONFIGS_DIR
            try:
                paths.PROJECT_ROOT = project_root
                paths.BUNDLE_ROOT = bundle_root
                paths.CONFIGS_DIR = project_root / "configs"
                paths.BUNDLED_CONFIGS_DIR = bundle_root / "configs"

                resolved = paths.config_path("waveform_config.json")

                self.assertEqual(resolved, project_root / "configs" / "waveform_config.json")
                self.assertTrue(resolved.exists())
                self.assertEqual(resolved.read_text(encoding="utf-8"), '{"source":"bundle"}')
            finally:
                paths.PROJECT_ROOT = original_project_root
                paths.BUNDLE_ROOT = original_bundle_root
                paths.CONFIGS_DIR = original_configs_dir
                paths.BUNDLED_CONFIGS_DIR = original_bundled_configs_dir

    def test_config_path_moves_legacy_file_into_configs_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            project_root = temp_root / "runtime"
            bundle_root = temp_root / "bundle"
            project_root.mkdir()
            bundle_root.mkdir()
            legacy_file = project_root / "axis_config.json"
            legacy_file.write_text('{"source":"legacy"}', encoding="utf-8")

            original_project_root = paths.PROJECT_ROOT
            original_bundle_root = paths.BUNDLE_ROOT
            original_configs_dir = paths.CONFIGS_DIR
            original_bundled_configs_dir = paths.BUNDLED_CONFIGS_DIR
            try:
                paths.PROJECT_ROOT = project_root
                paths.BUNDLE_ROOT = bundle_root
                paths.CONFIGS_DIR = project_root / "configs"
                paths.BUNDLED_CONFIGS_DIR = bundle_root / "configs"

                resolved = paths.config_path("axis_config.json")

                self.assertEqual(resolved, project_root / "configs" / "axis_config.json")
                self.assertTrue(resolved.exists())
                self.assertFalse(legacy_file.exists())
                self.assertEqual(resolved.read_text(encoding="utf-8"), '{"source":"legacy"}')
            finally:
                paths.PROJECT_ROOT = original_project_root
                paths.BUNDLE_ROOT = original_bundle_root
                paths.CONFIGS_DIR = original_configs_dir
                paths.BUNDLED_CONFIGS_DIR = original_bundled_configs_dir


if __name__ == "__main__":
    unittest.main()
