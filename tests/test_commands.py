import os
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from commands import cleanup_old_local_backups, restore_full_backup


class TestCommands(unittest.TestCase):
    @patch("commands.log_info")
    @patch("commands.run_command")
    @patch("commands.validate_config")
    def test_restore_full_backup_builds_pg_restore_command(self, mock_validate, mock_run_command, _mock_log_info):
        with tempfile.TemporaryDirectory() as tmp_dir:
            backup_file = Path(tmp_dir) / "sample.dump"
            backup_file.write_text("dummy")

            with patch("commands.Config.PG_RESTORE_BIN", "pg_restore"), patch("commands.Config.PG_HOST", "db"), patch(
                "commands.Config.PG_PORT", "5432"
            ), patch("commands.Config.PG_USER", "postgres"), patch("commands.Config.PG_DATABASE", "appdb"):
                restore_full_backup(str(backup_file))

        mock_validate.assert_called_once()
        mock_run_command.assert_called_once()
        command = mock_run_command.call_args.args[0]
        self.assertEqual(command[0], "pg_restore")
        self.assertIn("--clean", command)
        self.assertIn("--if-exists", command)
        self.assertEqual(command[-1], str(backup_file))

    @patch("commands.validate_config")
    def test_restore_full_backup_raises_for_missing_file(self, _mock_validate):
        with self.assertRaises(FileNotFoundError):
            restore_full_backup("/tmp/does-not-exist.dump")

    @patch("commands.validate_config")
    def test_restore_full_backup_raises_for_non_dump_extension(self, _mock_validate):
        with tempfile.TemporaryDirectory() as tmp_dir:
            backup_file = Path(tmp_dir) / "sample.txt"
            backup_file.write_text("dummy")

            with self.assertRaises(RuntimeError):
                restore_full_backup(str(backup_file))

    @patch("commands.log_info")
    def test_cleanup_old_local_backups_respects_retention(self, _mock_log_info):
        with tempfile.TemporaryDirectory() as tmp_dir:
            backup_dir = Path(tmp_dir)
            old_file = backup_dir / "old.dump"
            recent_file = backup_dir / "recent.dump"
            old_file.write_text("old")
            recent_file.write_text("recent")

            old_time = datetime.utcnow() - timedelta(days=10)
            recent_time = datetime.utcnow() - timedelta(days=2)

            os.utime(old_file, (old_time.timestamp(), old_time.timestamp()))
            os.utime(recent_file, (recent_time.timestamp(), recent_time.timestamp()))

            with patch("commands.Config.BACKUP_DIR", backup_dir), patch("commands.Config.RETENTION_DAYS", 7):
                cleanup_old_local_backups()

            self.assertFalse(old_file.exists())
            self.assertTrue(recent_file.exists())


if __name__ == "__main__":
    unittest.main()
