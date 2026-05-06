import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import argparse


load_dotenv()


PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_DATABASE = os.getenv("PG_DATABASE")
PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")

BACKUP_DIR = Path(os.getenv("BACKUP_DIR", "./backups"))
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "14"))

INCREMENTAL_TABLES = [
    table.strip()
    for table in os.getenv("INCREMENTAL_TABLES", "").split(",")
    if table.strip()
]

INCREMENTAL_TIMESTAMP_COLUMN = os.getenv(
    "INCREMENTAL_TIMESTAMP_COLUMN",
    "updated_at"
)


def validate_env():
    required = {
        "PG_HOST": PG_HOST,
        "PG_DATABASE": PG_DATABASE,
        "PG_USER": PG_USER,
        "PG_PASSWORD": PG_PASSWORD,
    }

    missing = [key for key, value in required.items() if not value]

    if missing:
        raise RuntimeError(f"Missing required env values: {', '.join(missing)}")


def run_command(command: list[str]):
    env = os.environ.copy()
    env["PGPASSWORD"] = PG_PASSWORD

    result = subprocess.run(
        command,
        env=env,
        text=True,
        capture_output=True,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())

    return result.stdout


def create_full_backup():
    validate_env()
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"{PG_DATABASE}_full_{timestamp}.dump"

    command = [
        "pg_dump",
        "-h", PG_HOST,
        "-p", PG_PORT,
        "-U", PG_USER,
        "-F", "c",
        "-f", str(backup_file),
        PG_DATABASE,
    ]

    run_command(command)

    print(f"Full backup created: {backup_file}")


def create_incremental_backup(since: str):
    validate_env()

    if not INCREMENTAL_TABLES:
        raise RuntimeError("INCREMENTAL_TABLES is empty in .env")

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"{PG_DATABASE}_incremental_{timestamp}.sql"

    with backup_file.open("w") as output:
        for table in INCREMENTAL_TABLES:
            query = (
                f"COPY ("
                f"SELECT * FROM {table} "
                f"WHERE {INCREMENTAL_TIMESTAMP_COLUMN} >= '{since}'"
                f") TO STDOUT WITH CSV HEADER"
            )

            output.write(f"-- Incremental backup for table: {table}\n")
            output.write(f"-- Since: {since}\n")
            output.write(f"-- Restore target table must already exist.\n\n")

            command = [
                "psql",
                "-h", PG_HOST,
                "-p", PG_PORT,
                "-U", PG_USER,
                "-d", PG_DATABASE,
                "-c", query,
            ]

            data = run_command(command)

            output.write(f"-- DATA FOR {table}\n")
            output.write(data)
            output.write("\n\n")

    print(f"Incremental backup created: {backup_file}")


def restore_full_backup(backup_file: str):
    validate_env()

    backup_path = Path(backup_file)

    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_file}")

    command = [
        "pg_restore",
        "-h", PG_HOST,
        "-p", PG_PORT,
        "-U", PG_USER,
        "-d", PG_DATABASE,
        "--clean",
        "--if-exists",
        str(backup_path),
    ]

    run_command(command)

    print(f"Full backup restored from: {backup_path}")


def cleanup_old_backups():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
    deleted = 0

    for file in BACKUP_DIR.glob("*"):
        if file.is_file():
            modified_time = datetime.fromtimestamp(file.stat().st_mtime)

            if modified_time < cutoff:
                file.unlink()
                deleted += 1

    print(f"Deleted {deleted} old backup(s).")


def list_backups():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    backups = sorted(BACKUP_DIR.glob("*"), reverse=True)

    if not backups:
        print("No backups found.")
        return

    for backup in backups:
        print(backup)


def main():
    parser = argparse.ArgumentParser(description="PostgreSQL backup and restore utility")
    subparsers = parser.add_subparsers(dest="command", required=True)

    backup_parser = subparsers.add_parser("backup")
    backup_parser.add_argument(
        "--type",
        choices=["full", "incremental"],
        default="full",
    )
    backup_parser.add_argument(
        "--since",
        help="Required for incremental backup. Example: 2026-05-06 00:00:00",
    )

    restore_parser = subparsers.add_parser("restore")
    restore_parser.add_argument("backup_file")

    subparsers.add_parser("cleanup")
    subparsers.add_parser("list")

    args = parser.parse_args()

    if args.command == "backup":
        if args.type == "full":
            create_full_backup()
        elif args.type == "incremental":
            if not args.since:
                raise RuntimeError("--since is required for incremental backup")
            create_incremental_backup(args.since)

    elif args.command == "restore":
        restore_full_backup(args.backup_file)

    elif args.command == "cleanup":
        cleanup_old_backups()

    elif args.command == "list":
        list_backups()


if __name__ == "__main__":
    main()