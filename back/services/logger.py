"""
日志配置模块，负责设置日志记录格式和输出。
"""
import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logger(app, log_folder='log'):
    """
    设置应用程序日志记录器
    
    Args:
        app: Flask 应用实例或日志记录器名称
        log_folder: 日志文件存储目录
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 确保日志目录存在
    os.makedirs(log_folder, exist_ok=True)
    
    # 配置日志记录器
    log_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    
    # 文件处理器 - 记录所有日志
    log_file = os.path.join(log_folder, 'app.log')
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.INFO)
    
    # 错误日志处理器 - 仅记录错误和以上级别
    error_log_file = os.path.join(log_folder, 'error.log')
    error_file_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    error_file_handler.setFormatter(log_formatter)
    error_file_handler.setLevel(logging.ERROR)
    
    # 决定是创建新的日志记录器还是使用Flask应用的记录器
    if isinstance(app, str):
        # 如果提供的是名称字符串，创建新的日志记录器
        logger = logging.getLogger(app)
        logger.handlers = []  # 清除已有的处理器
        logger.addHandler(file_handler)
        logger.addHandler(error_file_handler)
        logger.setLevel(logging.INFO)
        
        # 添加控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        console_handler.setLevel(logging.DEBUG)
        logger.addHandler(console_handler)
    else:
        # 否则，假设是Flask应用
        logger = app.logger
        logger.addHandler(file_handler)
        logger.addHandler(error_file_handler)
        logger.setLevel(logging.INFO)
        
        # 在开发环境中保留控制台输出
        if hasattr(app, 'debug') and app.debug:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(log_formatter)
            console_handler.setLevel(logging.DEBUG)
            logger.addHandler(console_handler)
            logger.setLevel(logging.DEBUG)
    
    return logger 