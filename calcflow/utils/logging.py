import sys
import os
import logging

_LOG_FORMAT = "%(asctime)s [%(levelname)s]: %(message)s"


def setup_logging(level=logging.INFO):
    """Configure root logger with console output."""
    root = logging.getLogger()
    root.setLevel(level)
    formatter = logging.Formatter(_LOG_FORMAT)
    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        root.addHandler(handler)


def add_file_logging(output_dir, filename="calcflow.log"):
    """Add a file handler to the root logger."""
    log_path = os.path.join(output_dir, filename)
    root = logging.getLogger()
    formatter = logging.Formatter(_LOG_FORMAT)
    if not any(
        isinstance(h, logging.FileHandler) and h.baseFilename == os.path.abspath(log_path)
        for h in root.handlers
    ):
        handler = logging.FileHandler(log_path)
        handler.setFormatter(formatter)
        root.addHandler(handler)
