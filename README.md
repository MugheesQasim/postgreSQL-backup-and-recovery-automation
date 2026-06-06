# PostgreSQL Backup and Recovery Automation

Automated PostgreSQL backup, validation, S3 upload, and restore testing using Python + PostgreSQL native tools (`pg_dump`, `pg_restore`, `pg_basebackup`, `psql`).

This project is designed for production-style operations:
- logical and physical backup flows
- backup integrity checks
- cloud object storage integration (S3)
- scheduled automation with Kubernetes CronJobs
- restore verification as part of disaster recovery readiness

## Features

- **Full logical backups** (`pg_dump -F c`) as `.dump` files
- **Physical backups** (`pg_basebackup`) archived as `.tar.gz`
- **Validation checks** before restore/upload workflows
- **S3 upload/download** with SSE-S3 encryption (`AES256`)
- **Automated restore test workflow** (`restore_test.py`)
- **Operational commands** for cleanup and listing local backups
- **Alerting hook support** via configurable webhook

## Project Structure

```text
.
├── backup.py                # CLI entrypoint for backup/restore operations
├── restore_test.py          # Automated restore verification workflow
├── commands.py              # PostgreSQL command execution + local file ops
├── storage.py               # S3 key generation/upload/download/listing
├── validators.py            # Backup file integrity checks
├── monitoring.py            # Logging + webhook alerting
├── config.py                # Environment configuration and validation
├── k8s/                     # Kubernetes CronJob and config manifests
├── requirements.txt
└── tests/                   # Unit tests
```

## Prerequisites

- Python **3.11+**
- PostgreSQL client tools available in PATH:
  - `pg_dump`
  - `pg_restore`
  - `pg_basebackup`
  - `psql`
- AWS credentials/role allowing:
  - `s3:PutObject`
  - `s3:GetObject`
  - `s3:ListBucket`

## Configuration

Create a `.env` file in the project root:

```env
PG_HOST=localhost
PG_PORT=5432
PG_DATABASE=mydb
PG_USER=backup_user
PG_PASSWORD=supersecret

BACKUP_DIR=/tmp/backups
RETENTION_DAYS=14

PG_DUMP_BIN=pg_dump
PG_RESTORE_BIN=pg_restore
PG_BASEBACKUP_BIN=pg_basebackup
PG_COMBINEBACKUP_BIN=pg_combinebackup
PSQL_BIN=psql

S3_BUCKET=my-postgres-backups
S3_PREFIX=postgres-backups
AWS_REGION=us-east-1

ALERT_WEBHOOK_URL=
```

Required values:
- `PG_HOST`
- `PG_DATABASE`
- `PG_USER`
- `PG_PASSWORD`
- `S3_BUCKET`

## Local Setup

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

## Usage

### 1. Create full logical backup

```bash
python3 backup.py full
```

### 2. Create physical backup archive and upload to S3

```bash
python3 backup.py incremental
```

### 3. Validate a backup file

```bash
python3 backup.py validate /path/to/backup.dump
```

### 4. Restore a full `.dump` backup

```bash
python3 backup.py restore /path/to/backup.dump
```

### 5. Run local cleanup (retention policy)

```bash
python3 backup.py cleanup
```

### 6. List local backups

```bash
python3 backup.py list
```

### 7. Run restore verification workflow

```bash
python3 restore_test.py
```

## Testing

Run all unit tests:

```bash
python3 -m unittest discover -s tests -v
```

Current test coverage focuses on:
- configuration validation rules
- command construction and filesystem behavior
- S3 key/path behavior and latest-backup selection logic
- backup validation checks

## Kubernetes Automation

The `k8s/` folder includes:
- `cronjob-full-backup.yaml` (daily logical full backup)
- `cronjob-incremental-backup.yaml` (periodic physical backup)
- `cronjob-restore-test.yaml` (scheduled restore verification)
- `configmap.yaml` and `secret.yaml` for runtime configuration
- `serviceaccount.yaml` with IRSA annotation for AWS access

## Logging and Alerting

- Logs are written to `/tmp/backup_system.log`
- Alerts are sent only when `ALERT_WEBHOOK_URL` is set
- Failures call `send_alert(...)` from CLI and restore test entrypoints


## License

This project is licensed under the terms in `LICENSE`.
