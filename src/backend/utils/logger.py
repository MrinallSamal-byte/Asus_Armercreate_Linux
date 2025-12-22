"""
Logging utilities for ASUS Armoury Crate Linux.
"""

import logging
import os
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "asus-armoury",
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    debug_mode: bool = False
) -> logging.Logger:
    """
    Set up and configure a logger instance.
    
    Args:
        name: Logger name
        level: Logging level
        log_file: Optional path to log file
        debug_mode: Enable debug mode with verbose output
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if debug_mode:
        level = logging.DEBUG
    
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = "asus-armoury") -> logging.Logger:
    """
    Get an existing logger or create a new one.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    
    # If no handlers are configured, set up default logging
    if not logger.handlers:
        setup_logger(name)
    
    return logger


# Default logger instance
_default_logger: Optional[logging.Logger] = None


def init_default_logger(debug_mode: bool = False) -> logging.Logger:
    """
    Initialize the default application logger.
    
    Args:
        debug_mode: Enable debug mode
        
    Returns:
        Default logger instance
    """
    global _default_logger
    
    # Determine log file location
    if os.geteuid() == 0:
        log_dir = "/var/log/asus-armoury"
    else:
        log_dir = os.path.expanduser("~/.local/share/asus-armoury/logs")
    
    log_file = os.path.join(log_dir, "asus-armoury.log")
    
    _default_logger = setup_logger(
        name="asus-armoury",
        log_file=log_file,
        debug_mode=debug_mode
    )
    
    return _default_logger
