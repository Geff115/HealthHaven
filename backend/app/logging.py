#!/usr/bin/env python3
"""
Logging handler
"""
import logging
import os
from logging.handlers import RotatingFileHandler


# Ensure the log directory exists
log_directory = "logs"
os.makedirs(log_directory, exist_ok=True)

# Log file configurations
SECURITY_LOG_FILE = os.path.join(log_directory, "security.log")
SQL_LOG_FILE = os.path.join(log_directory, "sql.log")

# File size rotation settings
MAX_LOG_FILE_SIZE = 5_000_000   # 5 MB
BACKUP_COUNT = 5   # Keeping up to 5 backup files

# General log format
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Configure security logger
security_logger = logging.getLogger("security")
security_handler = RotatingFileHandler(
    SECURITY_LOG_FILE, maxBytes=MAX_LOG_FILE_SIZE, backupCount=BACKUP_COUNT
)
security_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
security_logger.setLevel(logging.INFO)
security_logger.addHandler(security_handler)

# Configure SQL logger
sql_logger = logging.getLogger("sqlalchemy.engine")
sql_handler = RotatingFileHandler(
    SQL_LOG_FILE, maxBytes=MAX_LOG_FILE_SIZE, backupCount=BACKUP_COUNT
)
sql_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
sql_logger.setLevel(logging.INFO)  # Set to DEBUG if you need detailed SQL logs
sql_logger.addHandler(sql_handler)

# Suppress SQL logs in the root logger
sql_logger.propagate = False

# Stream handler for console output (optional)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
logging.getLogger().addHandler(console_handler)