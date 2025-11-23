"""Logging utilities for the Tourism Planner"""

import logging
import sys

class TourismLogger:
    """Custom logger with console output only"""
    
    def __init__(self, name: str = "TourismPlanner"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
        
        # Console handler only
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(levelname)s | %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(console_handler)
    
    def debug(self, msg: str, **kwargs):
        """Log debug message"""
        extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        full_message = f"{msg} | {extra_info}" if extra_info else msg
        self.logger.debug(full_message)
    
    def info(self, msg: str, **kwargs):
        """Log info message"""
        extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        full_message = f"{msg} | {extra_info}" if extra_info else msg
        self.logger.info(full_message)
    
    def warning(self, msg: str, **kwargs):
        """Log warning message"""
        extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        full_message = f"{msg} | {extra_info}" if extra_info else msg
        self.logger.warning(full_message)
    
    def error(self, msg: str, **kwargs):
        """Log error message"""
        extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        full_message = f"{msg} | {extra_info}" if extra_info else msg
        self.logger.error(full_message)
    
    def critical(self, msg: str, **kwargs):
        """Log critical message"""
        extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        full_message = f"{msg} | {extra_info}" if extra_info else msg
        self.logger.critical(full_message)

# Global logger instance
logger = TourismLogger()