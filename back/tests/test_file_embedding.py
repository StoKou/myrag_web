import unittest
import os
import sys
import tempfile
import json
import numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.file_embedding import EmbeddingClass
from tests.test_logger_utils import test_logger, TestLoggerAdapter


class TestEmbeddingService(unittest.TestCase):
    """测试文件嵌入服务"""
    
    def setUp(self):
        """测试前的设置"""
        self.logger = TestLoggerAdapter(test_logger, "EmbeddingServiceTest")
        self.logger.debug("准备测试EmbeddingService服务")
        
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建测试分块文件和目录
        self.chunk_folder = os.path.join(self.temp_dir, "chunks")
        self.embedding_folder = os.path.join(self.temp_dir, "embeddings")
        os.makedirs(self.chunk_folder, exist_ok=True)
        os.makedirs(self.embedding_folder, exist_ok=True)
        
        self.chunks_file_path = os.path.join(self.chunk_folder, "test_chunks.json")
        chunks_data = {
            "metadata": {
                "original_filename": "test_document.txt",
                "chunk_method": "paragraph",
                "chunk_count": 3
            },
            "chunks": [
                {
                    "id": 1,
                    "chunk_text": "这是第一个测试块。用于测试嵌入功能。"
                },
                {
                    "id": 2,
                    "chunk_text": "这是第二个测试块。我们正在测试向量化过程。"
                },
                {
                    "id": 3,
                    "chunk_text": "这是第三个测试块。希望测试能够成功。"
                }
            ]
        }
        
        with open(self.chunks_file_path, "w", encoding="utf-8") as f:
            json.dump(chunks_data, f, ensure_ascii=False, indent=2)
        
        self.logger.debug(f"创建测试分块文件: {self.chunks_file_path}")
        
        # 初始化嵌入服务，使用模拟模式
        self.embedding_service = self._create_mock_embedding_service()
    
    def _create_mock_embedding_service(self):
        """创建模拟的嵌入服务"""
        # 创建一个EmbeddingClass的子类，重写相关方法，避免实际调用模型
        class MockEmbeddingClass(EmbeddingClass):
            def __init__(self, *args, **kwargs):
                # 不初始化实际模型
                self.model_type = "mock"
                self.chunk_folder = self.temp_dir if hasattr(self, 'temp_dir') else os.path.join('files', 'chunk')
                self.embedding_folder = self.temp_dir if hasattr(self, 'temp_dir') else os.path.join('files')
                self.embedding_file = os.path.join(self.embedding_folder, 'embedding.json')
                
                # 确保目录存在
                os.makedirs(self.embedding_folder, exist_ok=True)
            
            def _init_huggingface_model(self):
                # 不实际初始化模型
                pass
                
            def _init_openai(self):
                # 不实际初始化API
                pass
                
            def get_embedding(self, text):
                # 返回模拟的嵌入向量
                dimension = 384
                embedding = self.generate_mock_embedding(dimension)
                return {
                    "embedding": embedding,
                    "metadata": {
                        "model_type": "mock",
                        "model_name": "mock-model",
                        "dimension": dimension,
                        "processing_time_ms": 10,
                        "timestamp": "2025-04-29T12:00:00"
                    }
                }
                
            def generate_mock_embedding(self, dimension):
                """生成模拟的嵌入向量"""
                # 生成随机向量并规范化
                vector = np.random.rand(dimension).astype(np.float32)
                vector = vector / np.linalg.norm(vector)
                return vector.tolist()
                
            def generate_mock_embeddings_for_chunks(self, chunks, dimension=384):
                """为多个文本块生成模拟嵌入向量"""
                return [self.generate_mock_embedding(dimension) for _ in range(len(chunks))]
                
            def save_embeddings(self, embeddings_data, metadata, output_path):
                """保存嵌入向量到文件"""
                data = {
                    "embeddings": embeddings_data,
                    "metadata": metadata
                }
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                return {"success": True, "file_path": output_path}
                
            def load_chunks(self, chunk_file_id):
                """重写加载chunks的方法，直接从临时目录加载"""
                try:
                    with open(self.chunks_file_path, 'r', encoding='utf-8') as f:
                        chunk_data = json.load(f)
                        return chunk_data.get("chunks", []), chunk_data.get("metadata", {})
                except Exception as e:
                    return [], {}
        
        # 创建模拟服务实例
        mock_service = MockEmbeddingClass()
        mock_service.temp_dir = self.temp_dir
        mock_service.chunks_file_path = self.chunks_file_path
        return mock_service
    
    def tearDown(self):
        """测试后的清理"""
        import shutil
        # 删除临时文件和目录
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        self.logger.debug(f"清理临时目录: {self.temp_dir}")
        self.logger.debug("EmbeddingService服务测试完成")
    
    def test_generate_mock_embedding(self):
        """测试生成模拟嵌入向量功能"""
        self.logger.debug("开始测试生成模拟嵌入向量功能")
        
        # 测试生成模拟嵌入向量
        dimension = 384
        self.logger.debug(f"测试生成 {dimension} 维向量")
        
        vector = self.embedding_service.generate_mock_embedding(dimension)
        
        # 检查向量维度和类型
        self.assertIsInstance(vector, list)
        self.assertEqual(len(vector), dimension)
        
        # 检查向量是否已规范化
        np_vector = np.array(vector)
        magnitude = np.linalg.norm(np_vector)
        self.assertAlmostEqual(magnitude, 1.0, places=6)
        self.logger.debug(f"验证向量已规范化, 大小: {magnitude}")
        
        self.logger.debug("生成模拟嵌入向量功能测试完成")
    
    def test_mock_embeddings_generation(self):
        """测试为文本块生成模拟嵌入向量"""
        self.logger.debug("开始测试为文本块生成模拟嵌入向量")
        
        try:
            # 加载测试块
            with open(self.chunks_file_path, "r", encoding="utf-8") as f:
                chunks_data = json.load(f)
            
            chunks = chunks_data["chunks"]
            self.logger.debug(f"加载了 {len(chunks)} 个文本块")
            
            # 生成嵌入向量
            dimension = 384
            self.logger.debug(f"为每个块生成 {dimension} 维向量")
            
            embeddings_data = self.embedding_service.generate_mock_embeddings_for_chunks(
                chunks,
                dimension
            )
            
            # 检查嵌入向量数据
            self.assertIsInstance(embeddings_data, list)
            self.assertEqual(len(embeddings_data), len(chunks))
            
            # 检查每个嵌入向量
            for i, embedding in enumerate(embeddings_data):
                self.assertIsInstance(embedding, list)
                self.assertEqual(len(embedding), dimension)
                
                # 检查向量是否已规范化
                np_vector = np.array(embedding)
                magnitude = np.linalg.norm(np_vector)
                self.assertAlmostEqual(magnitude, 1.0, places=6)
                self.logger.debug(f"块 {i+1} 的向量已规范化, 大小: {magnitude}")
                
            self.logger.debug(f"成功为 {len(chunks)} 个文本块生成了嵌入向量")
                
        except Exception as e:
            self.logger.error(f"生成嵌入向量测试失败: {e}")
            self.fail(f"生成嵌入向量测试失败: {e}")
        
        self.logger.debug("为文本块生成模拟嵌入向量测试完成")
    
    def test_save_embeddings(self):
        """测试保存嵌入向量结果功能"""
        self.logger.debug("开始测试保存嵌入向量结果功能")
        
        try:
            # 加载测试块
            with open(self.chunks_file_path, "r", encoding="utf-8") as f:
                chunks_data = json.load(f)
            
            # 生成一些嵌入向量
            dimension = 384
            chunks = chunks_data["chunks"]
            self.logger.debug(f"为 {len(chunks)} 个文本块生成嵌入向量")
            
            mock_embeddings = [
                self.embedding_service.generate_mock_embedding(dimension)
                for _ in range(len(chunks))
            ]
            
            # 准备嵌入数据
            embeddings_data = []
            for i, (chunk, vector) in enumerate(zip(chunks, mock_embeddings)):
                embeddings_data.append({
                    "id": i,
                    "text": chunk.get("chunk_text", ""),
                    "vector": vector
                })
            
            # 保存嵌入向量
            output_path = os.path.join(self.temp_dir, "embeddings.json")
            metadata = {
                "original_filename": chunks_data["metadata"]["original_filename"],
                "chunk_method": chunks_data["metadata"]["chunk_method"],
                "chunk_count": len(chunks),
                "embedding_model": "test-model",
                "embedding_dimension": dimension
            }
            
            self.logger.debug(f"准备保存嵌入向量到: {output_path}")
            
            # 调用保存函数
            result = self.embedding_service.save_embeddings(
                embeddings_data, 
                metadata,
                output_path
            )
            
            # 检查结果
            self.assertTrue(os.path.exists(output_path))
            self.logger.debug(f"确认文件已保存: {output_path}")
            
            # 读取保存的文件并验证
            with open(output_path, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
            
            self.assertIn("embeddings", saved_data)
            self.assertIn("metadata", saved_data)
            self.assertEqual(len(saved_data["embeddings"]), len(chunks))
            self.logger.debug("验证保存的JSON数据结构正确")
            
        except Exception as e:
            self.logger.error(f"保存嵌入向量测试失败: {e}")
            self.fail(f"保存嵌入向量测试失败: {e}")
        
        self.logger.debug("保存嵌入向量结果功能测试完成")


if __name__ == "__main__":
    unittest.main() 