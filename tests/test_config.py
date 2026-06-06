import unittest
from unittest.mock import patch

from config import validate_config


class TestValidateConfig(unittest.TestCase):
    def test_validate_config_raises_for_missing_required_values(self):
        with patch("config.Config.PG_HOST", None), patch("config.Config.PG_DATABASE", "demo"), patch(
            "config.Config.PG_USER", None
        ), patch("config.Config.PG_PASSWORD", "secret"), patch("config.Config.S3_BUCKET", None):
            with self.assertRaises(RuntimeError) as exc:
                validate_config()

        message = str(exc.exception)
        self.assertIn("PG_HOST", message)
        self.assertIn("PG_USER", message)
        self.assertIn("S3_BUCKET", message)

    def test_validate_config_passes_when_required_values_exist(self):
        with patch("config.Config.PG_HOST", "localhost"), patch("config.Config.PG_DATABASE", "demo"), patch(
            "config.Config.PG_USER", "postgres"
        ), patch("config.Config.PG_PASSWORD", "secret"), patch("config.Config.S3_BUCKET", "bucket"):
            validate_config()


if __name__ == "__main__":
    unittest.main()
