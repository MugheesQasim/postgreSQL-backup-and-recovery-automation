import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from validators import validate_backup_file, validate_pg_dump_archive


class TestValidators(unittest.TestCase):
    def test_validate_backup_file_raises_if_missing(self):
        with self.assertRaises(FileNotFoundError):
            validate_backup_file("/tmp/does-not-exist.dump")

    def test_validate_backup_file_raises_if_empty(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "empty.dump"
            file_path.touch()

            with self.assertRaises(RuntimeError):
                validate_backup_file(str(file_path))

    @patch("validators.log_info")
    @patch("validators.validate_pg_dump_archive")
    def test_validate_backup_file_calls_archive_validator_for_dump(self, mock_validate_archive, _mock_log_info):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "backup.dump"
            file_path.write_text("not-empty")
            validate_backup_file(str(file_path))

        mock_validate_archive.assert_called_once_with(file_path)

    @patch("validators.log_info")
    @patch("validators.validate_pg_dump_archive")
    def test_validate_backup_file_skips_archive_validator_for_non_dump(self, mock_validate_archive, _mock_log_info):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "backup.tar.gz"
            file_path.write_text("not-empty")
            validate_backup_file(str(file_path))

        mock_validate_archive.assert_not_called()

    @patch("validators.run_command", return_value="")
    def test_validate_pg_dump_archive_raises_for_empty_list_output(self, _mock_run_command):
        with self.assertRaises(RuntimeError):
            validate_pg_dump_archive(Path("/tmp/test.dump"))

    @patch("validators.run_command", return_value="BLOBS")
    def test_validate_pg_dump_archive_raises_for_missing_db_objects(self, _mock_run_command):
        with self.assertRaises(RuntimeError):
            validate_pg_dump_archive(Path("/tmp/test.dump"))

    @patch("validators.run_command", return_value="; TABLE public.users")
    def test_validate_pg_dump_archive_passes_with_table_output(self, _mock_run_command):
        validate_pg_dump_archive(Path("/tmp/test.dump"))


if __name__ == "__main__":
    unittest.main()
