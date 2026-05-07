import argparse
import sys

from commands import (
    create_full_backup,
    create_physical_backup,
    restore_full_backup,
    cleanup_old_local_backups,
    list_local_backups,
)
from validators import validate_backup_file
from storage import upload_file_to_s3
from monitoring import send_alert, log_info


def main():
    parser = argparse.ArgumentParser(
        description="PostgreSQL Backup and Recovery Automation"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("full", help="Create full logical backup and upload to S3")

    subparsers.add_parser(
        "incremental",
        help="Create physical backup archive and upload to S3",
    )

    restore_parser = subparsers.add_parser("restore", help="Restore full backup")
    restore_parser.add_argument("backup_file")

    validate_parser = subparsers.add_parser("validate", help="Validate backup file")
    validate_parser.add_argument("backup_file")

    subparsers.add_parser("cleanup", help="Delete old local backups")
    subparsers.add_parser("list", help="List local backups")

    args = parser.parse_args()

    try:
        if args.command == "full":
            backup_file = create_full_backup()
            validate_backup_file(str(backup_file))
            # upload_file_to_s3(str(backup_file), "full")

        elif args.command == "incremental":
            backup_file = create_physical_backup()
            validate_backup_file(str(backup_file))
            upload_file_to_s3(str(backup_file), "physical")

        elif args.command == "restore":
            restore_full_backup(args.backup_file)

        elif args.command == "validate":
            validate_backup_file(args.backup_file)

        elif args.command == "cleanup":
            cleanup_old_local_backups()

        elif args.command == "list":
            list_local_backups()

        log_info("Operation completed successfully.")

    except Exception as exc:
        send_alert(f"Backup system failure: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()