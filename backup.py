import argparse
import sys

from commands import (
    create_full_backup,
    create_incremental_backup,
    restore_full_backup,
    cleanup_old_backups,
    list_backups,
)
from validators import validate_backup_file
from monitoring import send_alert, log_info


def main():
    parser = argparse.ArgumentParser(
        description="PostgreSQL Backup and Recovery Automation"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("full", help="Create full logical backup using pg_dump")

    subparsers.add_parser(
        "incremental",
        help="Create PostgreSQL physical/incremental-style backup",
    )

    restore_parser = subparsers.add_parser("restore", help="Restore full backup")
    restore_parser.add_argument("backup_file")

    validate_parser = subparsers.add_parser("validate", help="Validate backup file")
    validate_parser.add_argument("backup_file")

    subparsers.add_parser("cleanup", help="Delete old backups")
    subparsers.add_parser("list", help="List backups")

    args = parser.parse_args()

    try:
        if args.command == "full":
            backup_file = create_full_backup()
            validate_backup_file(str(backup_file))

        elif args.command == "incremental":
            create_incremental_backup()

        elif args.command == "restore":
            restore_full_backup(args.backup_file)

        elif args.command == "validate":
            validate_backup_file(args.backup_file)

        elif args.command == "cleanup":
            cleanup_old_backups()

        elif args.command == "list":
            list_backups()

        log_info("Operation completed successfully.")

    except Exception as exc:
        send_alert(f"Backup system failure: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()