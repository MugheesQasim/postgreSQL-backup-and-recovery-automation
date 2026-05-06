import sys

from commands import create_full_backup, restore_full_backup, run_sql
from validators import validate_backup_file
from monitoring import log_info, send_alert


TEST_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS backup_restore_test (
    id SERIAL PRIMARY KEY,
    test_value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

INSERT_TEST_DATA_SQL = """
INSERT INTO backup_restore_test (test_value)
VALUES ('restore-test-before-backup');
"""

VERIFY_SQL = """
SELECT COUNT(*) FROM backup_restore_test
WHERE test_value = 'restore-test-before-backup';
"""

DROP_TEST_TABLE_SQL = """
DROP TABLE IF EXISTS backup_restore_test;
"""


def run_restore_test():
    log_info("Starting automated restore test.")

    run_sql(TEST_TABLE_SQL)
    run_sql(INSERT_TEST_DATA_SQL)

    backup_file = create_full_backup()
    validate_backup_file(str(backup_file))

    run_sql(DROP_TEST_TABLE_SQL)

    restore_full_backup(str(backup_file))

    result = run_sql(VERIFY_SQL)

    if "1" not in result:
        raise RuntimeError("Restore test failed. Expected test row was not restored.")

    log_info("Automated restore test passed.")


if __name__ == "__main__":
    try:
        run_restore_test()
    except Exception as exc:
        send_alert(f"Restore test failed: {exc}")
        sys.exit(1)