""" Module to setup logging for IoT Hub."""

import logging
import logging.handlers
import platform
import sys


def setup_logging(app_name: str) -> logging.Logger:
    """Setup logger settings for the application.

    Args:
        app_name (str): Application name.

    Returns:
        logging.Logger: Instance of the logger created for the application.
    """
    logger = logging.getLogger(app_name)
    # Set logging level to INFO or DEBUG as needed
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # Check if the operating system is Windows
    if platform.system().lower() == 'windows':
        # For Windows, log to the Windows Event Log
        nt_event_log_handler = logging.handlers.NTEventLogHandler(app_name)
        nt_event_log_handler.setLevel(logging.INFO)
        nt_event_log_handler.setFormatter(formatter)
        logger.addHandler(nt_event_log_handler)
    else:
        # For other OS, log to the console and/or a file
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Optionally, log to a file
        file_handler = logging.FileHandler(f'{app_name}.log')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def log_error(logger: logging.Logger, error_message: str) -> None:
    """Log an error message to the logger.

    Args:
        logger (logging.Logger): Logger instance.
        error_message (str): Error message to log.
    """
    logger.error(error_message)


def log_info(logger: logging.Logger, info_message: str) -> None:
    """Log an information message to the logger.

    Args:
        logger (logging.Logger): Logger instance.
        info_message (str): Information message to log.
    """
    logger.info(info_message)
