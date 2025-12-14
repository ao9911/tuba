"""
log.py - Core logging module.

This module provides JSON format logging functionality,
matching the output format of the Go tuba/log package.
"""

import json
import logging
import os
import sys
import time
import traceback
import contextvars
from dataclasses import dataclass
from logging.handlers import TimedRotatingFileHandler
from typing import Any, Optional, Tuple

# Context variable for trace_id
_trace_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "trace_id", default=None
)


@dataclass
class Config:
    """Log configuration.

    Attributes:
        log_path: Log file storage path (日志存放路径)
        app_name: Application name (应用名称)
        debug: Whether to enable debug mode (是否开启Debug模式)
        multi_file: Multi-file mode generates files based on log level
                   (多文件模式根据日志级别生成文件)
    """

    log_path: str = ""
    app_name: str = ""
    debug: bool = False
    multi_file: bool = False


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter to match Go zap output format."""

    def format(self, record: logging.LogRecord) -> str:
        # Build log entry dict
        log_entry = {
            "level": record.levelname.lower(),
            "event_time": str(int(time.time())),
            "msg": record.getMessage(),
        }

        # Add trace_id if available
        trace_id = _trace_id_var.get()
        if trace_id is not None:
            log_entry["trace_id"] = trace_id

        # Add stack trace for warn level and above
        if record.levelno >= logging.WARNING and record.exc_info:
            log_entry["stacktrace"] = "".join(
                traceback.format_exception(*record.exc_info)
            )

        return json.dumps(log_entry, ensure_ascii=False, separators=(",", ":"))


# Global logger instance
_logger: Optional[logging.Logger] = None


def _get_logger() -> logging.Logger:
    """Get the global logger instance."""
    global _logger
    if _logger is None:
        # Initialize with default config
        _logger = _create_logger(Config(debug=True))
    return _logger


def _create_logger(config: Config) -> logging.Logger:
    """Create a logger with the given configuration."""
    logger = logging.getLogger("tubalog")
    logger.handlers.clear()
    logger.propagate = False

    # Set log level based on debug mode
    if config.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    formatter = JSONFormatter()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    if config.debug:
        console_handler.setLevel(logging.DEBUG)
    else:
        console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    # File handlers if log_path is specified
    if config.log_path:
        if config.multi_file:
            # Create separate file handlers for each level
            _add_level_file_handler(
                logger, config, "_info.log", logging.INFO, formatter
            )
            _add_level_file_handler(
                logger, config, "_warn.log", logging.WARNING, formatter
            )
            _add_level_file_handler(
                logger, config, "_error.log", logging.ERROR, formatter
            )
            _add_level_file_handler(
                logger, config, "_fatal.log", logging.CRITICAL, formatter
            )
            if config.debug:
                _add_level_file_handler(
                    logger, config, "_debug.log", logging.DEBUG, formatter
                )
        else:
            # Single file handler
            log_file = os.path.join(config.log_path, f"{config.app_name}.log")
            file_handler = TimedRotatingFileHandler(
                log_file,
                when="H",  # Rotate every hour
                interval=1,
                backupCount=24 * 7,  # Keep 7 days
            )
            file_handler.setFormatter(formatter)
            if config.debug:
                file_handler.setLevel(logging.DEBUG)
            else:
                file_handler.setLevel(logging.INFO)
            logger.addHandler(file_handler)

    return logger


class LevelFilter(logging.Filter):
    """Filter that only allows logs of a specific level."""

    def __init__(self, level: int):
        super().__init__()
        self.level = level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno == self.level


def _add_level_file_handler(
    logger: logging.Logger,
    config: Config,
    suffix: str,
    level: int,
    formatter: logging.Formatter,
) -> None:
    """Add a file handler for a specific log level."""
    log_file = os.path.join(config.log_path, f"{config.app_name}{suffix}")
    file_handler = TimedRotatingFileHandler(
        log_file,
        when="H",  # Rotate every hour
        interval=1,
        backupCount=24 * 7,  # Keep 7 days
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    file_handler.addFilter(LevelFilter(level))
    logger.addHandler(file_handler)


def init(config: Config) -> None:
    """Initialize the logger with the given configuration.

    Args:
        config: Log configuration
    """
    global _logger
    _logger = _create_logger(config)


# Context management functions


def with_trace_id(trace_id: str) -> contextvars.Token:
    """Set trace_id in the context.

    Args:
        trace_id: The trace ID to set

    Returns:
        A token that can be used to reset the context
    """
    return _trace_id_var.set(trace_id)


def from_context() -> Tuple[Optional[str], bool]:
    """Get trace_id from the context.

    Returns:
        A tuple of (trace_id, exists)
    """
    trace_id = _trace_id_var.get()
    return trace_id, trace_id is not None


def reset_trace_id(token: contextvars.Token) -> None:
    """Reset the trace_id context to its previous value.

    Args:
        token: The token returned by with_trace_id
    """
    _trace_id_var.reset(token)


# Basic logging functions


def debug(*args: Any) -> None:
    """Log debug message."""
    _get_logger().debug(" ".join(str(arg) for arg in args))


def debugf(msg: str, *args: Any) -> None:
    """Log formatted debug message."""
    _get_logger().debug(msg % args if args else msg)


def info(*args: Any) -> None:
    """Log info message."""
    _get_logger().info(" ".join(str(arg) for arg in args))


def infof(msg: str, *args: Any) -> None:
    """Log formatted info message."""
    _get_logger().info(msg % args if args else msg)


def warn(*args: Any) -> None:
    """Log warning message."""
    _get_logger().warning(" ".join(str(arg) for arg in args))


def warnf(msg: str, *args: Any) -> None:
    """Log formatted warning message."""
    _get_logger().warning(msg % args if args else msg)


def error(*args: Any) -> None:
    """Log error message."""
    _get_logger().error(" ".join(str(arg) for arg in args))


def errorf(msg: str, *args: Any) -> None:
    """Log formatted error message."""
    _get_logger().error(msg % args if args else msg)


def fatal(*args: Any) -> None:
    """Log fatal message and exit."""
    _get_logger().critical(" ".join(str(arg) for arg in args))
    sys.exit(1)


def fatalf(msg: str, *args: Any) -> None:
    """Log formatted fatal message and exit."""
    _get_logger().critical(msg % args if args else msg)
    sys.exit(1)


# Context-aware logging functions


def ctx_debug(trace_id: str, *args: Any) -> None:
    """Log debug message with trace_id."""
    token = with_trace_id(trace_id)
    try:
        debug(*args)
    finally:
        reset_trace_id(token)


def ctx_debugf(trace_id: str, msg: str, *args: Any) -> None:
    """Log formatted debug message with trace_id."""
    token = with_trace_id(trace_id)
    try:
        debugf(msg, *args)
    finally:
        reset_trace_id(token)


def ctx_info(trace_id: str, *args: Any) -> None:
    """Log info message with trace_id."""
    token = with_trace_id(trace_id)
    try:
        info(*args)
    finally:
        reset_trace_id(token)


def ctx_infof(trace_id: str, msg: str, *args: Any) -> None:
    """Log formatted info message with trace_id."""
    token = with_trace_id(trace_id)
    try:
        infof(msg, *args)
    finally:
        reset_trace_id(token)


def ctx_warn(trace_id: str, *args: Any) -> None:
    """Log warning message with trace_id."""
    token = with_trace_id(trace_id)
    try:
        warn(*args)
    finally:
        reset_trace_id(token)


def ctx_warnf(trace_id: str, msg: str, *args: Any) -> None:
    """Log formatted warning message with trace_id."""
    token = with_trace_id(trace_id)
    try:
        warnf(msg, *args)
    finally:
        reset_trace_id(token)


def ctx_error(trace_id: str, *args: Any) -> None:
    """Log error message with trace_id."""
    token = with_trace_id(trace_id)
    try:
        error(*args)
    finally:
        reset_trace_id(token)


def ctx_errorf(trace_id: str, msg: str, *args: Any) -> None:
    """Log formatted error message with trace_id."""
    token = with_trace_id(trace_id)
    try:
        errorf(msg, *args)
    finally:
        reset_trace_id(token)
