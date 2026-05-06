import os
from pathlib import Path
from dotenv import load_dotenv


load_dotenv()


class Config:
    PG_HOST = os.getenv("PG_HOST", "127.0.0.1")
    PG_PORT = os.getenv("PG_PORT", "5432")
    PG_DATABASE = os.getenv("PG_DATABASE")
    PG_USER = os.getenv("PG_USER")
    PG_PASSWORD = os.getenv("PG_PASSWORD")

    BACKUP_DIR = Path(os.getenv("BACKUP_DIR", "./backups"))
    RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "14"))

    PG_DUMP_BIN = os.getenv("PG_DUMP_BIN", "pg_dump")
    PG_RESTORE_BIN = os.getenv("PG_RESTORE_BIN", "pg_restore")
    PG_BASEBACKUP_BIN = os.getenv("PG_BASEBACKUP_BIN", "pg_basebackup")
    PG_COMBINEBACKUP_BIN = os.getenv("PG_COMBINEBACKUP_BIN", "pg_combinebackup")
    PSQL_BIN = os.getenv("PSQL_BIN", "psql")

    ALERT_WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_URL", "")


def validate_config():
    required = {
        "PG_DATABASE": Config.PG_DATABASE,
        "PG_USER": Config.PG_USER,
        "PG_PASSWORD": Config.PG_PASSWORD,
    }

    missing = [key for key, value in required.items() if not value]

    if missing:
        raise RuntimeError(f"Missing required environment values: {', '.join(missing)}")