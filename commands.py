import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from config import Config, validate_config
from monitoring import log_info


def run_command(command: list[str]):
    env = os.environ.copy()
    env["PGPASSWORD"] = Config.PG_PASSWORD

    result = subprocess.run(
        command,
        env=env,
        text=True,
        capture_output=True,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())

    return result.stdout


def create_full_backup() -> Path:
    validate_config()

    full_dir = Config.BACKUP_DIR / "full"
    full_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = full_dir / f"{Config.PG_DATABASE}_full_{timestamp}.dump"

    command = [
        Config.PG_DUMP_BIN,
        "-h", Config.PG_HOST,
        "-p", Config.PG_PORT,
        "-U", Config.PG_USER,
        "-d", Config.PG_DATABASE,
        "-F", "c",
        "-f", str(backup_file),
    ]

    run_command(command)

    log_info(f"Full backup created: {backup_file}")
    return backup_file


def create_incremental_backup() -> Path:
    """
    PostgreSQL 18 native incremental physical backup wrapper.

    Important:
    - This requires PostgreSQL 18 server/client support.
    - A previous full/base physical backup must exist.
    - Real production setup also needs WAL archiving.
    """

    validate_config()

    incremental_dir = Config.BACKUP_DIR / "incremental"
    incremental_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = incremental_dir / f"{Config.PG_DATABASE}_incremental_{timestamp}"

    command = [
        Config.PG_BASEBACKUP_BIN,
        "-h", Config.PG_HOST,
        "-p", Config.PG_PORT,
        "-U", Config.PG_USER,
        "-D", str(backup_path),
        "--checkpoint=fast",
        "--progress",
    ]

    run_command(command)

    log_info(f"Incremental/physical backup created: {backup_path}")
    return backup_path


def restore_full_backup(backup_file: str):
    validate_config()

    backup_path = Path(backup_file)

    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_file}")

    if backup_path.suffix != ".dump":
        raise RuntimeError("Only full .dump backups can be restored with pg_restore.")

    command = [
        Config.PG_RESTORE_BIN,
        "-h", Config.PG_HOST,
        "-p", Config.PG_PORT,
        "-U", Config.PG_USER,
        "-d", Config.PG_DATABASE,
        "--clean",
        "--if-exists",
        str(backup_path),
    ]

    run_command(command)

    log_info(f"Full backup restored from: {backup_path}")


def cleanup_old_backups():
    Config.BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    cutoff = datetime.now() - timedelta(days=Config.RETENTION_DAYS)
    deleted = 0

    for file in Config.BACKUP_DIR.rglob("*"):
        if file.is_file():
            modified = datetime.fromtimestamp(file.stat().st_mtime)

            if modified < cutoff:
                file.unlink()
                deleted += 1

    log_info(f"Deleted {deleted} old backup file(s).")


def list_backups():
    Config.BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    backups = sorted(Config.BACKUP_DIR.rglob("*"), reverse=True)

    files = [item for item in backups if item.is_file()]

    if not files:
        log_info("No backups found.")
        return

    for file in files:
        print(file)


def run_sql(sql: str):
    validate_config()

    command = [
        Config.PSQL_BIN,
        "-h", Config.PG_HOST,
        "-p", Config.PG_PORT,
        "-U", Config.PG_USER,
        "-d", Config.PG_DATABASE,
        "-c", sql,
    ]

    return run_command(command)