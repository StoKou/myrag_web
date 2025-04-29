import unittest
import os
import sys
import tempfile
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.file_chunk import FileChunkProcessor as FileChunker
from tests.test_logger_utils import test_logger, TestLoggerAdapter


class TestFileChunker(unittest.TestCase):
    """测试文件分块服务"""
    
    def setUp(self):
        """测试前的设置"""
        self.logger = TestLoggerAdapter(test_logger, "FileChunkerTest")
        self.logger.debug("准备测试FileChunker服务")
        
        # 创建临时目录和测试文件
        self.temp_dir = tempfile.mkdtemp()
        self.test_file_path = os.path.join(self.temp_dir, "test_document.txt")
        
        # 写入测试内容
        with open(self.test_file_path, "w", encoding="utf-8") as f:
            f.write("这是第一段落。这是一个测试文档。\n\n")
            f.write("这是第二段落。我们正在测试文件分块功能。\n\n")
            f.write("这是第三段落。希望测试能够成功。\n\n")
            f.write("这是第四段落。分块应该能够按照段落或句子进行。\n\n")
            f.write("这是最后一段。测试结束。")
        
        self.logger.debug(f"创建测试文件: {self.test_file_path}")
        
        # 创建加载和分块临时目录
        self.load_folder = os.path.join(self.temp_dir, "load")
        self.chunk_folder = os.path.join(self.temp_dir, "chunks")
        os.makedirs(self.load_folder, exist_ok=True)
        os.makedirs(self.chunk_folder, exist_ok=True)
        
        # 初始化文件分块器，提供必要的参数
        self.chunker = FileChunker(self.load_folder, self.chunk_folder)
    
    def tearDown(self):
        """测试后的清理"""
        import shutil
        # 删除临时文件和目录
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        self.logger.debug(f"清理临时目录: {self.temp_dir}")
        self.logger.debug("FileChunker服务测试完成")
    
    # 添加测试用的方法
    def create_test_load_file(self, file_id="test_file"):
        """创建测试加载文件"""
        test_data = {
            "文件ID": file_id,
            "文件名": "test_document.txt",
            "文件类型": "text/plain",
            "文件大小": 200,
            "上传时间": "2025-04-29T00:00:00",
            "文件读取内容": "这是第一段落。这是一个测试文档。\n\n这是第二段落。我们正在测试文件分块功能。\n\n这是第三段落。希望测试能够成功。\n\n这是第四段落。分块应该能够按照段落或句子进行。\n\n这是最后一段。测试结束。"
        }
        
        file_path = os.path.join(self.load_folder, f"{file_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        
        return file_id
    
    def test_chunk_by_paragraph(self):
        """测试按段落分块功能"""
        self.logger.debug("开始测试按段落分块功能")
        
        try:
            # 测试自定义分块方法，使用段落分隔符
            file_id = self.create_test_load_file()
            result = self.chunker.process_chunk(file_id, "custom", separator="\n\n")
            
            # 检查分块结果
            self.assertTrue(result["success"])
            self.assertTrue(len(result["chunks"]) > 0)
            
            # 检查块数量（应该有5个段落）
            self.assertEqual(len(result["chunks"]), 5)
            self.logger.debug(f"共生成 {len(result['chunks'])} 个段落块")
            
        except Exception as e:
            self.logger.error(f"段落分块测试失败: {e}")
            self.fail(f"段落分块测试失败: {e}")
        
        self.logger.debug("按段落分块功能测试完成")
    
    def test_chunk_by_sentence(self):
        """测试按句子分块功能"""
        self.logger.debug("开始测试按句子分块功能")
        
        try:
            # 使用LlamaIndex的句子分块
            file_id = self.create_test_load_file()
            result = self.chunker.process_chunk(file_id, "llamaindex", chunk_size=100, chunk_overlap=10)
            
            # 检查分块结果
            self.assertTrue(result["success"])
            self.assertTrue(len(result["chunks"]) > 0)
            
            # 检查每个块的内容
            for i, chunk in enumerate(result["chunks"]):
                self.assertIsInstance(chunk["content"], str)
                self.assertTrue(len(chunk["content"]) > 0)
                
            # 应该至少有一个块（根据实际情况调整）
            # 注意：实际的分块数量可能会因为模型实现而不同
            self.assertTrue(len(result["chunks"]) >= 1)
            self.logger.debug(f"共生成 {len(result['chunks'])} 个句子块")
            
        except Exception as e:
            self.logger.error(f"句子分块测试失败: {e}")
            self.fail(f"句子分块测试失败: {e}")
        
        self.logger.debug("按句子分块功能测试完成")
    
    def test_save_chunks(self):
        """测试保存分块结果功能"""
        self.logger.debug("开始测试保存分块结果功能")
        
        try:
            # 创建测试文件并进行分块
            file_id = self.create_test_load_file()
            result = self.chunker.process_chunk(file_id, "langchain", chunk_size=200, chunk_overlap=20)
            
            # 检查结果
            self.assertTrue(result["success"])
            self.assertTrue(len(result["chunks"]) > 0)
            
            # 验证分块文件是否保存成功
            files = os.listdir(self.chunk_folder)
            self.assertTrue(len(files) > 0)
            
            # 读取已保存的文件验证内容
            saved_file_path = os.path.join(self.chunk_folder, files[0])
            with open(saved_file_path, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
            
            self.assertIn("chunks", saved_data)
            self.assertIn("chunk_method", saved_data)
            self.assertEqual(saved_data["chunk_method"], "langchain")
            
            self.logger.debug("验证保存的分块数据结构正确")
            
        except Exception as e:
            self.logger.error(f"保存分块结果测试失败: {e}")
            self.fail(f"保存分块结果测试失败: {e}")
        
        self.logger.debug("保存分块结果功能测试完成")


if __name__ == "__main__":
    unittest.main() 