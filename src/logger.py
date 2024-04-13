"""Logging module for the project"""

import datetime
from logging import INFO, Formatter, Logger, StreamHandler, getLogger
from typing import Any, Callable, Tuple


def setup_logging(
    logger_name: str | None = None,
    log_level: int = INFO,
    log_format: str | None = None,
) -> Tuple[Logger, Callable]:
    """
    Set up logging configuration and return a logger object and a decorator for logging function execution time.

    Args:
        logger_name (str): The name of the logger (default is None, which uses the root logger).
        log_level (int): The logging level (default is logging.INFO).
        log_format (str): The format of the log messages (default is a standard format including timestamp, log level, and message).

    Returns:
        Tuple[logging.Logger, Callable]: A tuple containing the configured logger object and a decorator function for logging function execution time.
    """
    if log_format is None:
        log_format = "%(asctime)s - %(levelname)s - %(message)s"

    if logger_name is None:
        logger = getLogger()
    else:
        logger = getLogger(logger_name)

    logger.setLevel(log_level)

    handler = StreamHandler()
    handler.setLevel(log_level)

    formatter = Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    def log_time_date(func: Callable) -> Callable:
        """
        Decorator function that logs the start and end times of the decorated function.

        Args:
            func (Callable): The function to be decorated.

        Returns:
            Callable: The decorated function.
        """

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """
            Wrapper function that logs the start and end times of the decorated function.

            Args:
                *args (Any): Positional arguments passed to the decorated function.
                **kwargs (Any): Keyword arguments passed to the decorated function.

            Returns:
                Any: The result of the decorated function.
            """
            logger.info(
                f"Function '{func.__name__}' started at {datetime.datetime.now()}"
            )
            result = func(*args, **kwargs)
            logger.info(
                f"Function '{func.__name__}' finished at {datetime.datetime.now()}"
            )
            return result

        return wrapper

    return logger, log_time_date
