"""
向量嵌入服务模块，为文档内容生成向量嵌入
支持 HuggingFace 的 BAAI/BGE-small-zh-v1.5 和 OpenAI 的 text-embedding-3-small 模型
"""
import os
import json
import time
import datetime
import logging
from typing import List, Dict, Any, Optional, Union, Tuple

# OpenAI API
import openai

# HuggingFace Transformers
from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np

# 环境变量处理
from dotenv import load_dotenv
load_dotenv()

class EmbeddingClass:
    """向量嵌入处理类，支持多种嵌入模型"""
    
    def __init__(self, model_type: str = "huggingface"):
        """
        初始化向量嵌入处理器
        
        Args:
            model_type: 模型类型，可选值: "huggingface", "openai"
        """
        self.model_type = model_type
        self.chunk_folder = os.path.join('files', 'chunk')
        self.embedding_folder = os.path.join('files')
        self.embedding_file = os.path.join(self.embedding_folder, 'embedding.json')
        
        # 确保目录存在
        os.makedirs(self.embedding_folder, exist_ok=True)
        
        # 初始化模型
        self.tokenizer = None
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        if model_type == "huggingface":
            self._init_huggingface_model()
        elif model_type == "openai":
            self._init_openai()
        else:
            raise ValueError(f"不支持的模型类型: {model_type}")
    
    def _init_huggingface_model(self):
        """初始化 HuggingFace 模型""" 
        try:
            model_name = "BAAI/bge-small-zh-v1.5"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name)
            self.model.to(self.device)
            self.model.eval()  # 设置为评估模式
            logging.info(f"成功加载 HuggingFace 模型: {model_name}")
        except Exception as e:
            logging.error(f"初始化 HuggingFace 模型时出错: {e}")
            raise
    
    def _init_openai(self):
        """初始化 OpenAI API"""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("未设置 OPENAI_API_KEY 环境变量")
            
            openai.api_key = api_key
            # 简单测试 API 连接
            try:
                openai.embeddings.create(
                    model="text-embedding-3-small",
                    input="测试连接"
                )
                logging.info("成功连接到 OpenAI API")
            except Exception as e:
                logging.error(f"测试 OpenAI API 连接时出错: {e}")
                raise
        except Exception as e:
            logging.error(f"初始化 OpenAI API 时出错: {e}")
            raise
    
    def _get_huggingface_embedding(self, text: str) -> List[float]:
        """
        使用 HuggingFace 模型获取文本的嵌入向量
        
        Args:
            text: 需要嵌入的文本
            
        Returns:
            List[float]: 嵌入向量
        """
        try:
            # 对文本进行编码
            encoded_input = self.tokenizer(
                text,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors='pt'
            ).to(self.device)
            
            # 进行前向传播，不计算梯度
            with torch.no_grad():
                model_output = self.model(**encoded_input)
                # 获取 [CLS] 向量作为句子表示
                sentence_embeddings = model_output.last_hidden_state[:, 0, :].cpu().numpy()
            
            # 标准化嵌入向量
            embedding = sentence_embeddings[0].tolist()
            return embedding
        except Exception as e:
            logging.error(f"获取 HuggingFace 嵌入向量时出错: {e}")
            raise
    
    def _get_openai_embedding(self, text: str) -> List[float]:
        """
        使用 OpenAI API 获取文本的嵌入向量
        
        Args:
            text: 需要嵌入的文本
            
        Returns:
            List[float]: 嵌入向量
        """
        try:
            # 使用 OpenAI 的嵌入 API
            response = openai.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            embedding = response.data[0].embedding
            return embedding
        except Exception as e:
            logging.error(f"获取 OpenAI 嵌入向量时出错: {e}")
            raise
    
    def get_embedding(self, text: str) -> Dict[str, Any]:
        """
        获取文本的嵌入向量
        
        Args:
            text: 需要嵌入的文本
            
        Returns:
            Dict: 包含嵌入向量和元数据的字典
        """
        start_time = time.time()
        
        try:
            if self.model_type == "huggingface":
                embedding = self._get_huggingface_embedding(text)
                model_name = "BAAI/bge-small-zh-v1.5"
            elif self.model_type == "openai":
                embedding = self._get_openai_embedding(text)
                model_name = "text-embedding-3-small"
            else:
                raise ValueError(f"不支持的模型类型: {self.model_type}")
            
            processing_time = time.time() - start_time
            
            return {
                "embedding": embedding,
                "metadata": {
                    "model_type": self.model_type,
                    "model_name": model_name,
                    "dimension": len(embedding),
                    "processing_time_ms": round(processing_time * 1000, 2),
                    "timestamp": datetime.datetime.now().isoformat()
                }
            }
        except Exception as e:
            logging.error(f"获取嵌入向量时出错: {e}")
            raise
    
    def load_chunks(self, chunk_file_id: str) -> List[Dict[str, Any]]:
        """
        从 chunk 文件夹加载 chunk 数据
        
        Args:
            chunk_file_id: chunk 文件 ID
            
        Returns:
            List[Dict]: 包含 chunk 数据的列表
        """
        # 查找匹配的文件
        for filename in os.listdir(self.chunk_folder):
            if filename.startswith(chunk_file_id) or filename.split('.')[0] == chunk_file_id:
                file_path = os.path.join(self.chunk_folder, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        chunk_data = json.load(f)
                        return chunk_data.get("chunks", []), chunk_data.get("metadata", {})
                except Exception as e:
                    logging.error(f"读取 chunk 文件 {file_path} 时出错: {e}")
                    raise
        
        logging.warning(f"未找到 ID 为 {chunk_file_id} 的 chunk 文件")
        return [], {}
    
    def process_embeddings(self, chunk_file_id: str) -> Dict[str, Any]:
        """
        处理 chunk 文件并生成嵌入向量
        
        Args:
            chunk_file_id: chunk 文件 ID
            
        Returns:
            Dict: 包含处理结果的字典
        """
        try:
            # 加载 chunk 数据
            chunks, metadata = self.load_chunks(chunk_file_id)
            
            if not chunks:
                return {
                    "success": False,
                    "error": f"未找到 ID 为 {chunk_file_id} 的 chunk 文件或文件内容为空"
                }
            
            # 保存嵌入向量的文件名
            start_time = time.time()
            
            # 为每个 chunk 添加嵌入向量
            embedded_chunks = []
            for idx, chunk in enumerate(chunks):
                # 获取嵌入向量
                chunk_text = chunk.get("chunk_text", "")
                if not chunk_text:
                    logging.warning(f"跳过空的 chunk: index={idx}")
                    continue
                
                logging.info(f"正在处理 chunk {idx+1}/{len(chunks)}")
                
                # 获取嵌入向量
                embedding_result = self.get_embedding(chunk_text)
                
                # 将嵌入向量添加到 chunk 中
                embedded_chunk = {
                    **chunk,
                    "embedding": embedding_result["embedding"],
                    "embedding_metadata": embedding_result["metadata"]
                }
                
                embedded_chunks.append(embedded_chunk)
            
            # 计算总处理时间
            total_time = time.time() - start_time
            
            # 构建嵌入结果
            embedding_data = {
                "embedded_chunks": embedded_chunks,
                "metadata": {
                    **metadata,
                    "chunk_file_id": chunk_file_id,
                    "embedding_model": self.model_type,
                    "embedding_model_name": "BAAI/bge-small-zh-v1.5" if self.model_type == "huggingface" else "text-embedding-3-small",
                    "chunk_count": len(embedded_chunks),
                    "embedding_time_seconds": round(total_time, 2),
                    "embedding_timestamp": datetime.datetime.now().isoformat()
                }
            }
            
            # 保存嵌入结果
            with open(self.embedding_file, 'w', encoding='utf-8') as f:
                json.dump(embedding_data, f, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "message": f"成功为 {len(embedded_chunks)} 个 chunks 生成嵌入向量",
                "metadata": embedding_data["metadata"],
                "embedding_file": self.embedding_file
            }
        
        except Exception as e:
            logging.error(f"处理嵌入向量时出错: {e}")
            return {
                "success": False,
                "error": f"处理嵌入向量时出错: {str(e)}"
            }
    
    def get_embedding_stats(self) -> Dict[str, Any]:
        """
        获取嵌入向量的统计信息
        
        Returns:
            Dict: 包含统计信息的字典
        """
        try:
            if not os.path.exists(self.embedding_file):
                return {
                    "exists": False,
                    "message": "嵌入向量文件不存在"
                }
            
            with open(self.embedding_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            metadata = data.get("metadata", {})
            chunks = data.get("embedded_chunks", [])
            
            # 计算一些统计信息
            chunk_count = len(chunks)
            embedding_dimensions = len(chunks[0].get("embedding", [])) if chunk_count > 0 else 0
            
            return {
                "exists": True,
                "metadata": metadata,
                "stats": {
                    "chunk_count": chunk_count,
                    "embedding_dimensions": embedding_dimensions,
                    "file_size_bytes": os.path.getsize(self.embedding_file),
                    "created_at": metadata.get("embedding_timestamp", "未知"),
                    "model_used": metadata.get("embedding_model_name", "未知")
                }
            }
        except Exception as e:
            logging.error(f"获取嵌入向量统计信息时出错: {e}")
            return {
                "exists": False,
                "error": str(e)
            } 