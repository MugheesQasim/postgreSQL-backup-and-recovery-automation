import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

from storage import build_s3_key, get_latest_s3_backup_key, upload_file_to_s3


class _FixedDatetime:
    @classmethod
    def utcnow(cls):
        return datetime(2026, 6, 6, 10, 0, 0)


class TestStorage(unittest.TestCase):
    def test_build_s3_key_has_expected_structure(self):
        local_file = Path("/tmp/example.dump")

        with patch("storage.datetime", _FixedDatetime), patch("storage.Config.S3_PREFIX", "pg"), patch(
            "storage.Config.PG_DATABASE", "analytics"
        ):
            key = build_s3_key(local_file, "full")

        self.assertEqual(key, "pg/analytics/full/2026/06/06/example.dump")

    def test_upload_file_to_s3_raises_if_file_missing(self):
        with self.assertRaises(FileNotFoundError):
            upload_file_to_s3("/tmp/not-found.dump", "full")

    def test_get_latest_s3_backup_key_returns_most_recent(self):
        mock_client = Mock()
        mock_client.list_objects_v2.return_value = {
            "Contents": [
                {"Key": "a/old.dump", "LastModified": datetime(2025, 1, 1)},
                {"Key": "a/new.dump", "LastModified": datetime(2026, 1, 1)},
            ]
        }

        with patch("storage.get_s3_client", return_value=mock_client), patch("storage.Config.S3_PREFIX", "prefix"), patch(
            "storage.Config.PG_DATABASE", "db"
        ), patch("storage.Config.S3_BUCKET", "bucket"):
            key = get_latest_s3_backup_key("full")

        self.assertEqual(key, "a/new.dump")

    def test_get_latest_s3_backup_key_raises_when_no_backups(self):
        mock_client = Mock()
        mock_client.list_objects_v2.return_value = {}

        with patch("storage.get_s3_client", return_value=mock_client), patch("storage.Config.S3_PREFIX", "prefix"), patch(
            "storage.Config.PG_DATABASE", "db"
        ), patch("storage.Config.S3_BUCKET", "bucket"):
            with self.assertRaises(RuntimeError):
                get_latest_s3_backup_key("full")

    @patch("storage.log_info")
    def test_upload_file_to_s3_sends_expected_arguments(self, _mock_log_info):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "file.dump"
            file_path.write_text("dummy")
            mock_client = Mock()

            with patch("storage.get_s3_client", return_value=mock_client), patch(
                "storage.build_s3_key", return_value="prefix/db/full/2026/06/06/file.dump"
            ), patch("storage.Config.S3_BUCKET", "bucket"):
                s3_uri = upload_file_to_s3(str(file_path), "full")

        mock_client.upload_file.assert_called_once()
        self.assertEqual(s3_uri, "s3://bucket/prefix/db/full/2026/06/06/file.dump")


if __name__ == "__main__":
    unittest.main()
