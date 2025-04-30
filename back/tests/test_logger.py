import unittest
import os
import sys
import logging
import tempfile
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.logger import setup_logger
from tests.test_logger_utils import test_logger, TestLoggerAdapter


class TestLogger(unittest.TestCase):
    """测试日志服务"""
    
    def setUp(self):
        """测试前的设置"""
        self.logger_adapter = TestLoggerAdapter(test_logger, "LoggerTest")
        self.logger_adapter.debug("准备测试Logger服务")
        
        # 创建临时日志目录
        self.temp_log_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """测试后的清理"""
        self.logger_adapter.debug("Logger服务测试完成")
        
        # 清理临时日志目录
        import shutil
        if os.path.exists(self.temp_log_dir):
            shutil.rmtree(self.temp_log_dir)
    
    def test_setup_logger_with_string(self):
        """测试使用字符串名称设置日志记录器功能"""
        self.logger_adapter.debug("开始测试setup_logger与字符串名称功能")
        
        logger_name = "test_string_logger"
        logger = setup_logger(logger_name, self.temp_log_dir)
        
        # 检查logger是否被正确创建
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, logger_name)
        
        # 检查handler是否正确设置
        self.assertTrue(len(logger.handlers) > 0)
        
        # 尝试记录消息
        try:
            logger.info("这是一条测试日志 - 字符串")
            logger.error("这是一条错误日志 - 字符串")
            success = True
        except Exception as e:
            success = False
            self.logger_adapter.error(f"日志记录失败: {e}")
        
        self.assertTrue(success, "日志记录应该成功完成")
        
        # 检查日志文件是否被创建
        app_log_path = os.path.join(self.temp_log_dir, 'app.log')
        error_log_path = os.path.join(self.temp_log_dir, 'error.log')
        self.assertTrue(os.path.exists(app_log_path), "应该创建了app.log文件")
        self.assertTrue(os.path.exists(error_log_path), "应该创建了error.log文件")
        
        self.logger_adapter.debug("setup_logger与字符串名称功能测试完成")
    
    def test_setup_logger_with_flask_app(self):
        """测试使用Flask应用设置日志记录器功能"""
        self.logger_adapter.debug("开始测试setup_logger与Flask应用功能")
        
        # 创建模拟Flask应用
        class MockFlaskApp:
            def __init__(self):
                self.debug = False
                self.logger = logging.getLogger("flask_app_logger")
                # 清除现有的处理器
                self.logger.handlers = []
        
        mock_app = MockFlaskApp()
        logger = setup_logger(mock_app, self.temp_log_dir)
        
        # 检查logger是否正确
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, "flask_app_logger")
        
        # 检查handler是否正确设置
        self.assertTrue(len(logger.handlers) > 0)
        
        # 尝试记录消息
        try:
            logger.info("这是一条测试日志 - Flask")
            logger.error("这是一条错误日志 - Flask")
            success = True
        except Exception as e:
            success = False
            self.logger_adapter.error(f"日志记录失败: {e}")
        
        self.assertTrue(success, "日志记录应该成功完成")
        
        # 检查日志文件是否被创建
        app_log_path = os.path.join(self.temp_log_dir, 'app.log')
        error_log_path = os.path.join(self.temp_log_dir, 'error.log')
        self.assertTrue(os.path.exists(app_log_path), "应该创建了app.log文件")
        self.assertTrue(os.path.exists(error_log_path), "应该创建了error.log文件")
        
        self.logger_adapter.debug("setup_logger与Flask应用功能测试完成")
    
    def test_setup_logger_with_debug_mode(self):
        """测试在调试模式下设置日志记录器功能"""
        self.logger_adapter.debug("开始测试setup_logger在调试模式功能")
        
        # 创建模拟Flask应用，开启调试模式
        class MockFlaskApp:
            def __init__(self):
                self.debug = True
                self.logger = logging.getLogger("flask_app_debug_logger")
                # 清除现有的处理器
                self.logger.handlers = []
        
        mock_app = MockFlaskApp()
        logger = setup_logger(mock_app, self.temp_log_dir)
        
        # 检查logger级别是否设置为DEBUG
        self.assertEqual(logger.level, logging.DEBUG)
        
        # 检查是否有控制台处理器
        has_console_handler = any(
            isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler)
            for handler in logger.handlers
        )
        self.assertTrue(has_console_handler, "调试模式下应该有控制台处理器")
        
        self.logger_adapter.debug("setup_logger在调试模式功能测试完成")


if __name__ == "__main__":
    unittest.main() 