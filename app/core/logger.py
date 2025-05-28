import logging
from logging.handlers import TimedRotatingFileHandler
import os
import sys


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Sets up a logger with the specified name and logging level.

    :param name: Name of the logger
    :param level: Logging level (default is INFO)
    :return: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    LOGS_PATH = "./logs"
    if not os.path.exists(LOGS_PATH):
        os.makedirs(LOGS_PATH)

    # if not logger.handlers:
    #     # Console handler
    #     handler = logging.StreamHandler(sys.stdout)
    #     handler.setLevel(level)

    #     # Create formatter and add it to the handler
    #     formatter = logging.Formatter(
    #         "[%(asctime)s] %(levelname)s in %(name)s: %(message)s"
    #     )
    #     handler.setFormatter(formatter)
        
    #     # File handler
    #     file_handler = logging.FileHandler(f"{LOGS_PATH}/{name}.log")
    #     file_handler.setLevel(level)
    #     file_handler.setFormatter(formatter)

    #     # Add the handlers to the logger
    #     logger.addHandler(handler)
    #     logger.addHandler(file_handler)

    # return logger
    handler = TimedRotatingFileHandler(
        filename=f"{LOGS_PATH}/app.log",
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8"
    )
    handler.setLevel(level)
    
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger