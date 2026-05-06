import logging
import requests
from config import Config


logging.basicConfig(
    filename="backup_system.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def log_info(message: str):
    print(message)
    logging.info(message)


def log_error(message: str):
    print(message)
    logging.error(message)


def send_alert(message: str):
    log_error(message)

    if not Config.ALERT_WEBHOOK_URL:
        return

    try:
        requests.post(
            Config.ALERT_WEBHOOK_URL,
            json={"text": message},
            timeout=10,
        )
    except Exception as exc:
        logging.error(f"Failed to send alert: {exc}")