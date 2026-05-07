from pathlib import Path
from datetime import datetime
import boto3

from config import Config
from monitoring import log_info


def get_s3_client():
    return boto3.client(
        "s3",
        region_name=Config.AWS_REGION,
    )


def build_s3_key(local_file: Path, backup_type: str) -> str:
    date_prefix = datetime.utcnow().strftime("%Y/%m/%d")

    return (
        f"{Config.S3_PREFIX}/"
        f"{Config.PG_DATABASE}/"
        f"{backup_type}/"
        f"{date_prefix}/"
        f"{local_file.name}"
    )


def upload_file_to_s3(local_file: str, backup_type: str) -> str:
    file_path = Path(local_file)

    if not file_path.exists():
        raise FileNotFoundError(f"Cannot upload missing file: {file_path}")

    s3_key = build_s3_key(file_path, backup_type)

    client = get_s3_client()

    client.upload_file(
        str(file_path),
        Config.S3_BUCKET,
        s3_key,
        ExtraArgs={
            "ServerSideEncryption": "AES256",
        },
    )

    s3_uri = f"s3://{Config.S3_BUCKET}/{s3_key}"

    log_info(f"Uploaded backup to S3: {s3_uri}")

    return s3_uri


def download_file_from_s3(s3_key: str, local_path: str):
    client = get_s3_client()

    Path(local_path).parent.mkdir(parents=True, exist_ok=True)

    client.download_file(
        Config.S3_BUCKET,
        s3_key,
        local_path,
    )

    log_info(f"Downloaded s3://{Config.S3_BUCKET}/{s3_key} to {local_path}")


def get_latest_s3_backup_key(backup_type: str = "full") -> str:
    prefix = f"{Config.S3_PREFIX}/{Config.PG_DATABASE}/{backup_type}/"

    client = get_s3_client()

    response = client.list_objects_v2(
        Bucket=Config.S3_BUCKET,
        Prefix=prefix,
    )

    objects = response.get("Contents", [])

    if not objects:
        raise RuntimeError(f"No S3 backups found under prefix: {prefix}")

    latest = sorted(objects, key=lambda item: item["LastModified"], reverse=True)[0]

    return latest["Key"]