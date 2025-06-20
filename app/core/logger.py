import logging
from logging.handlers import RotatingFileHandler
import sys
from pathlib import Path


def setup_logger(name: str, level: int | str = logging.INFO) -> logging.Logger:
    """
    Sets up a logger with the specified name and logging level.

    :param name: Name of the logger
    :param level: Logging level (default is INFO)
    :return: Configured logger instance
    """
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        # If the logger already has handlers, return it
        return logger

    logger_level = logging.getLevelName(level) if isinstance(level, str) else level
    logger.setLevel(logger_level)

    LOGS_PATH = Path("./logs")
    LOGS_PATH.mkdir(exist_ok=True)

    try:
        handler = RotatingFileHandler(
            filename=LOGS_PATH / "app.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=7,
            encoding="utf-8",
        )
        handler.setLevel(level)

        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s in %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        
        # Console handler para desarrollo
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        logger.addHandler(console_handler)
        
    except PermissionError as e:
        # Si falla el archivo, usar solo console
        print(f"Warning: No se pudo crear el archivo de log: {e}")
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s in %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
