import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger(name: str, log_file: str, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s %(name)s %(message)s'
        )
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=1024 * 1024 * 10,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger


log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

image_logger = setup_logger('image', os.path.join(log_dir, 'image.log'))
container_logger = setup_logger('container', os.path.join(log_dir, 'container.log'))
task_logger = setup_logger('task', os.path.join(log_dir, 'task.log'))
system_logger = setup_logger('system', os.path.join(log_dir, 'system.log'))