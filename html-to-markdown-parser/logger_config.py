"""
Logging configuration for the HTML-to-Markdown converter.
"""

import os
import logging
from pathlib import Path

def setup_logger(log_path=None, log_level=logging.INFO):
    """
    Configure the logging system for the application.
    
    Args:
        log_path: Path to the log file. If None, logs will only be sent to console.
        log_level: Logging level, defaults to INFO.
    
    Returns:
        The configured logger instance.
    """
    # Create root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Clear existing handlers to avoid duplicate logging
    logger.handlers.clear()
    
    # Format string for log messages
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log path provided)
    if log_path:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_path)
        if log_dir:
            Path(log_dir).mkdir(exist_ok=True, parents=True)
            
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        logger.info(f"Logging to file: {log_path}")
    
    return logger 