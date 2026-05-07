import os
import shutil
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

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
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


def create_physical_backup() -> Path:
    validate_config()

    physical_dir = Config.BACKUP_DIR / "physical"
    physical_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_path = physical_dir / f"{Config.PG_DATABASE}_physical_{timestamp}"

    command = [
        Config.PG_BASEBACKUP_BIN,
        "-h", Config.PG_HOST,
        "-p", Config.PG_PORT,
        "-U", Config.PG_USER,
        "-D", str(backup_path),
        "--checkpoint=fast",
        "--progress",
        "--write-recovery-conf",
    ]

    run_command(command)

    archive_path = shutil.make_archive(
        str(backup_path),
        "gztar",
        root_dir=str(backup_path),
    )

    shutil.rmtree(backup_path)

    log_info(f"Physical backup archive created: {archive_path}")

    return Path(archive_path)


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


def cleanup_old_local_backups():
    Config.BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    cutoff = datetime.utcnow() - timedelta(days=Config.RETENTION_DAYS)
    deleted = 0

    for file in Config.BACKUP_DIR.rglob("*"):
        if file.is_file():
            modified = datetime.utcfromtimestamp(file.stat().st_mtime)

            if modified < cutoff:
                file.unlink()
                deleted += 1

    log_info(f"Deleted {deleted} old local backup file(s).")


def list_local_backups():
    Config.BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    files = [item for item in sorted(Config.BACKUP_DIR.rglob("*")) if item.is_file()]

    if not files:
        log_info("No local backups found.")
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