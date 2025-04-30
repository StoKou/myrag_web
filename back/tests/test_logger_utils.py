"""
测试日志工具，用于记录测试结果
"""
import os
import logging
import sys
from datetime import datetime

# 日志格式
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_test_logger():
    """
    设置测试日志记录器
    
    返回:
        logging.Logger: 测试日志记录器
    """
    # 创建日志目录
    log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "log"))
    os.makedirs(log_dir, exist_ok=True)
    
    # 日志文件路径
    log_file = os.path.join(log_dir, "test_result.log")
    
    # 创建日志记录器
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.DEBUG)
    
    # 清除现有的处理器
    if logger.handlers:
        logger.handlers.clear()
    
    # 文件处理器
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    file_handler.setFormatter(file_formatter)
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# 全局测试日志记录器
test_logger = setup_test_logger()

class TestLoggerAdapter:
    """测试日志适配器，用于包装测试结果"""
    
    def __init__(self, logger, test_name):
        """
        初始化测试日志适配器
        
        参数:
            logger (logging.Logger): 日志记录器
            test_name (str): 测试名称
        """
        self.logger = logger
        self.test_name = test_name
        
    def info(self, msg, *args, **kwargs):
        """记录信息级别日志"""
        self.logger.info(f"[{self.test_name}] {msg}", *args, **kwargs)
        
    def error(self, msg, *args, **kwargs):
        """记录错误级别日志"""
        self.logger.error(f"[{self.test_name}] {msg}", *args, **kwargs)
        
    def warning(self, msg, *args, **kwargs):
        """记录警告级别日志"""
        self.logger.warning(f"[{self.test_name}] {msg}", *args, **kwargs)
        
    def debug(self, msg, *args, **kwargs):
        """记录调试级别日志"""
        self.logger.debug(f"[{self.test_name}] {msg}", *args, **kwargs)
        
    def critical(self, msg, *args, **kwargs):
        """记录严重错误级别日志"""
        self.logger.critical(f"[{self.test_name}] {msg}", *args, **kwargs)
        
    def log_test_start(self):
        """记录测试开始"""
        self.info(f"开始测试 {self.test_name}")
        
    def log_test_end(self, success=True, duration=None):
        """记录测试结束"""
        status = "通过" if success else "失败"
        duration_msg = f", 耗时: {duration:.3f}秒" if duration is not None else ""
        self.info(f"测试结束 {self.test_name} - 状态: {status}{duration_msg}")
        
    def log_test_result(self, test_case, success=True, error=None):
        """记录测试用例结果"""
        status = "通过" if success else "失败"
        if success:
            self.info(f"测试用例 {test_case} - 状态: {status}")
        else:
            self.error(f"测试用例 {test_case} - 状态: {status}")
            if error:
                self.error(f"错误信息: {error}") 