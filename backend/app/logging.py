#!/usr/bin/env python3
"""
Logging handler
"""
import logging
import os


# Configure logging
log_directory = "logs"
os.makedirs(log_directory, exist_ok=True)

log_file = os.path.join(log_directory, "security.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)