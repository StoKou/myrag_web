import unittest
import os
import sys
import tempfile
import io
from unittest.mock import MagicMock
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.file_processor import FileProcessor
from tests.test_logger_utils import test_logger, TestLoggerAdapter


class TestFileProcessor(unittest.TestCase):
    """测试文件处理器服务"""
    
    def setUp(self):
        """测试前的设置"""
        self.logger = TestLoggerAdapter(test_logger, "FileProcessorTest")
        self.logger.debug("准备测试FileProcessor服务")
        
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        self.upload_path = os.path.join(self.temp_dir, "upload")
        self.load_path = os.path.join(self.temp_dir, "load")
        os.makedirs(self.upload_path, exist_ok=True)
        os.makedirs(self.load_path, exist_ok=True)
        
        # 创建测试文本文件
        self.text_file_path = os.path.join(self.upload_path, "test.txt")
        with open(self.text_file_path, "w", encoding="utf-8") as f:
            f.write("这是一个测试文件。\n用于测试文件处理功能。")
        
        self.logger.debug(f"创建测试文件: {self.text_file_path}")
        
        # 初始化文件处理器
        self.processor = FileProcessor(self.upload_path, self.load_path)
        
        # 允许的文件扩展名
        self.allowed_extensions = {'txt', 'pdf', 'md', 'docx', 'xlsx'}
    
    def tearDown(self):
        """测试后的清理"""
        import shutil
        # 删除临时文件和目录
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        self.logger.debug(f"清理临时目录: {self.temp_dir}")
        self.logger.debug("FileProcessor服务测试完成")
    
    def test_allowed_file(self):
        """测试允许的文件类型功能"""
        self.logger.debug("开始测试允许的文件类型功能")
        
        # 测试允许的文件类型
        self.assertTrue(self.processor.allowed_file("test.txt", self.allowed_extensions))
        self.assertTrue(self.processor.allowed_file("test.pdf", self.allowed_extensions))
        self.assertTrue(self.processor.allowed_file("test.docx", self.allowed_extensions))
        
        # 测试不允许的文件类型
        self.assertFalse(self.processor.allowed_file("test.exe", self.allowed_extensions))
        self.assertFalse(self.processor.allowed_file("test.zip", self.allowed_extensions))
        self.assertFalse(self.processor.allowed_file("test", self.allowed_extensions))
        
        self.logger.debug("允许的文件类型功能测试完成")
    
    def test_save_upload_file(self):
        """测试保存上传文件功能"""
        self.logger.debug("开始测试保存上传文件功能")
        
        # 创建模拟文件对象
        mock_file = MagicMock()
        mock_file.filename = "test_upload.txt"
        mock_file.save = MagicMock()
        
        # 测试保存上传文件
        file_info = self.processor.save_upload_file(mock_file, "text")
        
        # 验证返回的文件信息
        self.assertEqual(file_info["original_filename"], "test_upload.txt")
        self.assertTrue(file_info["filename"].startswith("test_upload_"))
        self.assertTrue(file_info["filename"].endswith(".txt"))
        self.assertTrue(os.path.dirname(file_info["upload_path"]) == self.upload_path)
        self.assertTrue(os.path.dirname(file_info["load_path"]) == self.load_path)
        self.assertEqual(file_info["file_type"], "text")
        
        # 验证save方法被调用
        mock_file.save.assert_called_once()
        
        self.logger.debug("保存上传文件功能测试完成")
    
    def test_process_file(self):
        """测试处理文件功能"""
        self.logger.debug("开始测试处理文件功能")
        
        # 准备文件信息
        file_info = {
            "filename": "test_process.txt",
            "upload_path": self.text_file_path,
            "load_path": os.path.join(self.load_path, "test_process.json"),
            "file_type": "text"
        }
        
        # 测试处理文件
        try:
            result = self.processor.process_file(file_info)
            
            # 验证处理结果
            self.assertIn("processed_content", result)
            self.assertIn("content_length", result)
            self.assertTrue(len(result["processed_content"]) > 0)
            self.assertTrue(result["content_length"] > 0)
            
            # 验证输出文件是否已创建
            self.assertTrue(os.path.exists(file_info["load_path"]))
            
            self.logger.debug("处理文件功能测试成功")
        except Exception as e:
            self.logger.error(f"处理文件测试失败: {e}")
            self.fail(f"处理文件测试失败: {e}")
    
    def test_handle_upload_request(self):
        """测试完整的上传请求处理功能"""
        self.logger.debug("开始测试完整的上传请求处理功能")
        
        # 创建模拟文件对象
        class MockFile:
            def __init__(self, filename, content):
                self.filename = filename
                self.content = content
                
            def save(self, path):
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(self.content)
        
        mock_file = MockFile("test_handle.txt", "这是一个测试文件，用于测试上传请求处理功能。")
        
        # 测试上传请求处理
        result, status_code = self.processor.handle_upload_request(
            file=mock_file,
            file_type="text",
            allowed_extensions=self.allowed_extensions,
            logger=self.logger
        )
        
        # 验证结果
        self.assertEqual(status_code, 200)
        self.assertTrue(result["success"])
        self.assertIn("message", result)
        self.assertIn("data", result)
        self.assertTrue(result["data"]["processed"])
        self.assertIn("上传成功并处理完毕", result["message"])
        
        # 验证内容预览
        self.assertIn("content_preview", result["data"])
        self.assertIn("测试文件", result["data"]["content_preview"])
        
        self.logger.debug("完整的上传请求处理功能测试完成")
    
    def test_handle_upload_request_errors(self):
        """测试上传请求处理的错误情况"""
        self.logger.debug("开始测试上传请求处理的错误情况")
        
        # 测试空文件名
        empty_file = MagicMock()
        empty_file.filename = ""
        result, status_code = self.processor.handle_upload_request(
            file=empty_file,
            file_type="text",
            allowed_extensions=self.allowed_extensions,
            logger=self.logger
        )
        self.assertEqual(status_code, 400)
        self.assertFalse(result["success"])
        self.assertIn("没有选择文件", result["error"])
        
        # 测试未指定文件类型
        no_type_file = MagicMock()
        no_type_file.filename = "test.txt"
        result, status_code = self.processor.handle_upload_request(
            file=no_type_file,
            file_type=None,
            allowed_extensions=self.allowed_extensions,
            logger=self.logger
        )
        self.assertEqual(status_code, 400)
        self.assertFalse(result["success"])
        self.assertIn("没有指定文件类型", result["error"])
        
        # 测试不允许的文件类型
        invalid_file = MagicMock()
        invalid_file.filename = "test.exe"
        result, status_code = self.processor.handle_upload_request(
            file=invalid_file,
            file_type="text",
            allowed_extensions=self.allowed_extensions,
            logger=self.logger
        )
        self.assertEqual(status_code, 400)
        self.assertFalse(result["success"])
        self.assertIn("不允许的文件类型", result["error"])
        
        self.logger.debug("上传请求处理的错误情况测试完成")
        
    def test_get_loaded_files(self):
        """测试获取已加载文件列表功能"""
        self.logger.debug("开始测试获取已加载文件列表功能")
        
        # 创建测试JSON文件
        json_content = '{"文件名称": "test_file.txt", "文件读取内容": "测试内容", "文件读取方式": "text"}'
        test_json_path = os.path.join(self.load_path, "test_file_20250429.json")
        with open(test_json_path, 'w', encoding='utf-8') as f:
            f.write(json_content)
        
        # 测试获取已加载文件列表
        files = self.processor.get_loaded_files()
        
        # 验证结果
        self.assertIsInstance(files, list)
        self.assertTrue(len(files) > 0)
        
        # 验证返回的文件信息
        file_found = False
        for file_info in files:
            if file_info["id"] == "test_file_20250429":
                file_found = True
                self.assertEqual(file_info["filename"], "test_file.txt")
                self.assertEqual(file_info["path"], test_json_path)
                break
        
        self.assertTrue(file_found, "应该找到测试创建的JSON文件")
        self.logger.debug("获取已加载文件列表功能测试完成")


if __name__ == "__main__":
    unittest.main() 