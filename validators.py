from pathlib import Path

from config import Config
from commands import run_command
from monitoring import log_info


def validate_backup_file(backup_file: str):
    backup_path = Path(backup_file)

    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file does not exist: {backup_file}")

    if backup_path.stat().st_size == 0:
        raise RuntimeError(f"Backup file is empty: {backup_file}")

    if backup_path.suffix == ".dump":
        validate_pg_dump_archive(backup_path)

    log_info(f"Backup validation passed: {backup_path}")


def validate_pg_dump_archive(backup_path: Path):
    command = [
        Config.PG_RESTORE_BIN,
        "--list",
        str(backup_path),
    ]

    output = run_command(command)

    if not output.strip():
        raise RuntimeError("pg_restore --list returned empty output.")

    if "TABLE" not in output and "SCHEMA" not in output:
        raise RuntimeError("Backup archive does not appear to contain DB objects.")