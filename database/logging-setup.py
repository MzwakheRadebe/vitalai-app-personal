import logging
from logging.handlers import RotatingFileHandler
import os

def setup_security_logging():
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Security event logger
    security_logger = logging.getLogger('security')
    security_logger.setLevel(logging.WARNING)
    
    security_handler = RotatingFileHandler(
        'logs/security.log', 
        maxBytes=5*1024*1024, 
        backupCount=3
    )
    
    formatter = logging.Formatter(
        '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
    )
    security_handler.setFormatter(formatter)
    security_logger.addHandler(security_handler)