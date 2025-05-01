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
        self.embedding_folder = os.path.join('files', 'embedding')
        self.model_folder = os.path.join('files', 'embedding_models')
        
        # 确保目录存在
        os.makedirs(self.embedding_folder, exist_ok=True)
        os.makedirs(self.model_folder, exist_ok=True)
        os.makedirs(self.chunk_folder, exist_ok=True)
        
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
            model_path = os.path.join(self.model_folder, model_name)
            
            # 如果本地模型目录不存在，则从HuggingFace下载并保存
            if not os.path.exists(model_path):
                logging.info(f"从HuggingFace下载模型到: {model_path}")
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModel.from_pretrained(model_name)
                
                # 保存模型和tokenizer到本地
                self.tokenizer.save_pretrained(model_path)
                self.model.save_pretrained(model_path)
                logging.info(f"模型已保存到: {model_path}")
            else:
                logging.info(f"从本地加载模型: {model_path}")
                self.tokenizer = AutoTokenizer.from_pretrained(model_path)
                self.model = AutoModel.from_pretrained(model_path)
            
            self.model.to(self.device)
            self.model.eval()  # 设置为评估模式
            logging.info(f"成功加载模型到设备: {self.device}")
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
    
    def load_chunks(self, chunk_file_id: str) -> Optional[Dict[str, Any]]:
        """
        从 chunk 文件夹加载完整的 chunk JSON 数据

        Args:
            chunk_file_id: chunk 文件 ID (不含扩展名)

        Returns:
            Optional[Dict]: 包含完整 chunk 数据的字典，如果找不到文件则返回 None
        """
        # 查找匹配的 .json 文件
        target_filename = f"{chunk_file_id}.json"
        potential_files = [f for f in os.listdir(self.chunk_folder) if f.endswith('.json')]
        
        found_path = None
        for filename in potential_files:
            # 精确匹配或基于前缀匹配 (去除可能的_chunked_timestamp后缀)
            base_name = filename.split('_chunked_')[0]
            if filename == target_filename or base_name == chunk_file_id:
                found_path = os.path.join(self.chunk_folder, filename)
                logging.info(f"找到 chunk 文件: {found_path}")
                break
        
        if not found_path:
             # 如果精确/前缀匹配失败，尝试只用ID查找 (假设chunk_file_id可能包含后缀)
            for filename in potential_files:
                 if filename.split('.')[0] == chunk_file_id:
                    found_path = os.path.join(self.chunk_folder, filename)
                    logging.info(f"通过ID找到 chunk 文件: {found_path}")
                    break

        if found_path and os.path.exists(found_path):
            try:
                with open(found_path, 'r', encoding='utf-8') as f:
                    chunk_data = json.load(f)
                    return chunk_data
            except Exception as e:
                logging.error(f"读取 chunk 文件 {found_path} 时出错: {e}")
                raise # Reraise after logging
        else:
            logging.warning(f"未找到 ID 对应的 chunk 文件: {chunk_file_id}")
            return None

    def process_embeddings(self, chunk_file_id: str) -> Dict[str, Any]:
        """
        处理 chunk 文件并生成嵌入向量, 将结果保存到 embedding 文件夹下的新文件中。
        新文件将保留原始 chunk 文件的结构，并在每个 chunk 中添加嵌入向量，
        同时在顶层添加嵌入元数据。

        Args:
            chunk_file_id: chunk 文件 ID (通常不包含 .json 后缀)

        Returns:
            Dict: 包含处理结果的字典
        """
        try:
            # 加载完整的 chunk 数据
            chunk_data = self.load_chunks(chunk_file_id)

            if not chunk_data:
                return {
                    "success": False,
                    "error": f"未找到 ID 为 {chunk_file_id} 的 chunk 文件"
                }
            
            chunks = chunk_data.get("chunks")
            if not chunks or not isinstance(chunks, list):
                 return {
                    "success": False,
                    "error": f"Chunk 文件 {chunk_file_id} 中未找到有效的 'chunks' 列表"
                }

            # 定义嵌入向量的输出文件名和路径
            # 使用原始 chunk_file_id 确保一致性
            output_filename = f"{chunk_file_id}_embedded.json"
            output_filepath = os.path.join(self.embedding_folder, output_filename)

            start_time = time.time()
            processed_chunk_count = 0

            # 为每个 chunk 添加嵌入向量 (直接修改 chunk_data)
            for idx, chunk in enumerate(chunks):
                # 从 "content" 字段获取文本 (根据你的示例 JSON)
                chunk_text = chunk.get("content", "") 
                if not chunk_text:
                    logging.warning(f"跳过空的 chunk: index={idx} in {chunk_file_id}")
                    continue

                logging.info(f"正在处理 chunk {idx+1}/{len(chunks)} for {chunk_file_id}")

                try:
                    # 获取嵌入向量和元数据
                    embedding_result = self.get_embedding(chunk_text)
                    
                    # 将嵌入向量添加到 chunk 字典中
                    chunk["embedding"] = embedding_result["embedding"]
                    # 可选：如果需要，也可以添加单个 chunk 的嵌入元数据
                    # chunk["embedding_metadata"] = embedding_result["metadata"]
                    processed_chunk_count += 1
                except Exception as embed_error:
                    logging.error(f"为 chunk {idx+1} 生成嵌入时出错 (ID: {chunk_file_id}): {embed_error}")
                    # 决定是否跳过此 chunk 或中止整个过程
                    # 这里选择跳过
                    chunk["embedding"] = None # Mark as failed
                    chunk["embedding_error"] = str(embed_error)
                    continue 

            # 计算总处理时间
            total_time = time.time() - start_time
            model_name_used = "BAAI/bge-small-zh-v1.5" if self.model_type == "huggingface" else "text-embedding-3-small"

            # 在顶层添加嵌入元数据 (直接修改 chunk_data)
            chunk_data["embedding_metadata"] = {
                 "chunk_file_id": chunk_file_id, # Add original chunk file id
                 "embedding_model_type": self.model_type,
                 "embedding_model_name": model_name_used,
                 "processed_chunk_count": processed_chunk_count,
                 "total_chunk_count": len(chunks),
                 "embedding_time_seconds": round(total_time, 2),
                 "embedding_timestamp": datetime.datetime.now().isoformat()
             }

            # 保存修改后的完整数据结构到指定文件
            with open(output_filepath, 'w', encoding='utf-8') as f:
                json.dump(chunk_data, f, ensure_ascii=False, indent=2)

            logging.info(f"嵌入结果已保存到: {output_filepath}")

            return {
                "success": True,
                "message": f"成功处理 {processed_chunk_count}/{len(chunks)} 个 chunks 并生成嵌入向量",
                "embedding_file": output_filepath, 
                "data": chunk_data # Return the full data including embeddings
            }

        except Exception as e:
            logging.error(f"处理嵌入向量时出错 (chunk_file_id: {chunk_file_id}): {e}", exc_info=True)
            return {
                "success": False,
                "error": f"处理嵌入向量时发生意外错误: {str(e)}"
            }

    def get_embedding_stats(self, embedding_file_id: str) -> Dict[str, Any]:
        """
        获取指定嵌入向量文件的统计信息
        
        Args:
            embedding_file_id: 嵌入文件 ID (通常与 chunk_file_id 相同, 可能含或不含 _embedded 后缀)

        Returns:
            Dict: 包含统计信息的字典
        """
        try:
            # Construct filename based on the ID passed (which might already have _embedded suffix or not)
            if embedding_file_id.endswith("_embedded"):
                embedding_filename = f"{embedding_file_id}.json"
            else:
                # Assume the ID is the base chunk ID, append suffix
                embedding_filename = f"{embedding_file_id}_embedded.json"
                
            embedding_filepath = os.path.join(self.embedding_folder, embedding_filename)

            if not os.path.exists(embedding_filepath):
                # Try finding without _embedded suffix if the first attempt failed, 
                # maybe the ID passed already contained the suffix but we incorrectly added another one.
                alternative_filename = f"{embedding_file_id.replace('_embedded', '')}.json"
                alternative_filepath = os.path.join(self.embedding_folder, alternative_filename)
                
                # Also check if the original ID itself was the filename (without adding suffix)
                direct_filename = f"{embedding_file_id}.json"
                direct_filepath = os.path.join(self.embedding_folder, direct_filename)

                if os.path.exists(direct_filepath):
                     embedding_filepath = direct_filepath
                     embedding_filename = direct_filename
                     logging.info(f"Found embedding file using direct name: {embedding_filename}")
                elif os.path.exists(alternative_filepath):
                     embedding_filepath = alternative_filepath
                     embedding_filename = alternative_filename
                     logging.info(f"Found embedding file using alternative name: {embedding_filename}")
                else:
                    logging.warning(f"嵌入向量文件不存在: {embedding_filepath} or {alternative_filepath} or {direct_filepath}")
                    return {
                        "exists": False,
                        "message": f"嵌入向量文件 {embedding_filename} 或 {alternative_filename} 或 {direct_filename} 不存在"
                    }
            
            with open(embedding_filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Get metadata added during embedding
            embedding_metadata = data.get("embedding_metadata", {})
            # Get original chunking metadata if present (all top-level keys except chunks and embedding_metadata)
            original_metadata = {k: v for k, v in data.items() if k not in ["chunks", "embedding_metadata"]}

            chunks = data.get("chunks", [])
            
            # Calculate stats
            total_chunk_count = len(chunks)
            processed_chunk_count = embedding_metadata.get("processed_chunk_count", total_chunk_count)
            embedding_dimensions = 0
            example_chunk_content = ""
            example_vector = []
            # Find the first successfully embedded chunk for example
            first_successful_chunk = next((chunk for chunk in chunks if chunk.get("embedding") is not None), None)

            if first_successful_chunk:
                 embedding_dimensions = len(first_successful_chunk["embedding"])
                 example_vector = first_successful_chunk["embedding"] # Get first valid chunk's embedding
                 example_chunk_content = first_successful_chunk.get("content", "") # Get first valid chunk's content
            elif chunks: # If no successful chunks, but chunks exist, try getting dimension from metadata
                 embedding_dimensions = embedding_metadata.get("dimension", 0) # Might not be present
                 example_chunk_content = chunks[0].get("content", "(无成功嵌入的块)")
            
            model_used = embedding_metadata.get("embedding_model_name", embedding_metadata.get("embedding_model_type", "未知"))

            # Combine metadata for easier access on frontend
            full_metadata = {**original_metadata, **embedding_metadata}

            return {
                "exists": True,
                "filepath": embedding_filepath,
                "data": data, # Return the full loaded data
                # Keep existing stats for convenience if needed, but primary data is in 'data'
                "stats": { 
                    "total_chunk_count": total_chunk_count,
                    "processed_chunk_count": processed_chunk_count,
                    "embedding_dimensions": embedding_dimensions,
                    "file_size_bytes": os.path.getsize(embedding_filepath),
                    "created_at": embedding_metadata.get("embedding_timestamp", "未知"),
                    "model_used": model_used
                },
                # Keep example for quick preview if needed
                "example_chunk_content": example_chunk_content, 
                "example_vector": example_vector
            }
        except json.JSONDecodeError as json_err:
            logging.error(f"解析嵌入向量文件 JSON 时出错 (file_id: {embedding_file_id}, path: {embedding_filepath}): {json_err}")
            return {"exists": False, "error": f"无法解析文件内容: {json_err}"}
        except Exception as e:
            logging.error(f"获取嵌入向量统计信息时出错 (file_id: {embedding_file_id}): {e}", exc_info=True)
            return {
                "exists": False,
                "error": str(e)
            } 