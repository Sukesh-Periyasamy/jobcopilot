"""Logger module with rotating file and console output.

Configures application-wide logging with ISO 8601 timestamps,
rotating file handler (10MB max, 5 backups), and console output.
"""

import logging
import os
from logging.handlers import RotatingFileHandler


LOG_FORMAT = "%(asctime)s | %(levelname)s | %(module)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
LOG_FILE = os.path.join("data", "jobcopilot.log")
MAX_BYTES = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5


def setup_logging() -> logging.Logger:
    """Configure root logger with rotating file handler and console handler.

    - RotatingFileHandler: data/jobcopilot.log, 10MB max, 5 backups
    - StreamHandler: console output
    - Format: ISO 8601 timestamp | LEVEL | module | message

    Returns:
        Configured root logger instance.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # Ensure the data directory exists
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    # Rotating file handler
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
