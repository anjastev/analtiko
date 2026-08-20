# backend/scripts/pipeline_logging.py

from datetime import datetime
from pathlib import Path


LOG_DIR = Path("logs")


def ensure_log_dir():
    LOG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def write_log(
    filename: str,
    message: str,
):
    ensure_log_dir()

    log_file = (
        LOG_DIR
        / filename
    )

    timestamp = (
        datetime.now()
        .strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    with log_file.open(
        "a",
        encoding="utf-8",
    ) as file:

        file.write(
            f"[{timestamp}] "
            f"{message}\n"
        )