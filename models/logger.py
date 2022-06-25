"""Different types of logging handlers."""

import logging
import sys


def get_file_handler(formatter: logging.Formatter, log_filename: str) -> logging.FileHandler:
    """File handler for logger.

    Args:
        formatter: Formatter class for custom logger.
        log_filename: Filename for logger.

    Returns:
        logging.FileHandler:
        Handler class.
    """
    file_handler = logging.FileHandler(filename=log_filename)
    file_handler.setLevel(level=logging.DEBUG)
    file_handler.setFormatter(fmt=formatter)
    return file_handler


def get_stream_handler(formatter: logging.Formatter) -> logging.StreamHandler:
    """Stream handler for logger.

    Args:
        formatter: Formatter class for custom logger.

    Returns:
        logging.StreamHandler:
        Handler class.
    """
    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setLevel(level=logging.DEBUG)
    stream_handler.setFormatter(fmt=formatter)
    return stream_handler


def get_logger(name: str, handler: logging.Handler) -> logging.Logger:
    """Stream handler for logger.

    Args:
        name: Logger name.
        handler: Either ``FileHandler`` or ``StreamHandler``.

    Returns:
        logging.Logger:
        Logger class.
    """
    logger = logging.getLogger(name=name)
    logger.setLevel(level=logging.DEBUG)
    logger.addHandler(hdlr=handler)
    return logger
