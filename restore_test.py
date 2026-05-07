import sys
from pathlib import Path

from commands import restore_full_backup, run_sql
from validators import validate_backup_file
from storage import get_latest_s3_backup_key, download_file_from_s3
from monitoring import log_info, send_alert


VERIFY_SQL = """
SELECT COUNT(*) FROM information_schema.tables
WHERE table_schema = 'public';
"""


def run_restore_test():
    log_info("Starting automated restore test.")

    latest_key = get_latest_s3_backup_key("full")

    local_backup_path = Path("/tmp/restore-test/latest-full.dump")

    download_file_from_s3(latest_key, str(local_backup_path))

    validate_backup_file(str(local_backup_path))

    restore_full_backup(str(local_backup_path))

    result = run_sql(VERIFY_SQL)

    log_info(f"Restore verification result: {result}")

    log_info("Automated restore test completed successfully.")


if __name__ == "__main__":
    try:
        run_restore_test()
    except Exception as exc:
        send_alert(f"Restore test failed: {exc}")
        sys.exit(1)