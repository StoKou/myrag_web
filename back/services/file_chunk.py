"""
文件切分服务模块，基于不同方法对文档进行切分
"""
import os
import json
import datetime
import shutil

# LlamaIndex 相关导入
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import VectorStoreIndex, Document
from llama_index.core import Settings
from llama_index.core.node_parser import SentenceSplitter, TokenTextSplitter

# LangChain 相关导入
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.text_splitter import CharacterTextSplitter

# 环境变量处理
from dotenv import load_dotenv
load_dotenv()

class FileChunkProcessor:
    def __init__(self, load_folder, chunk_folder):
        """
        初始化文件切分处理器
        
        Args:
            load_folder: 已加载文件存储目录
            chunk_folder: 切分后文件存储目录
        """
        self.load_folder = load_folder
        self.chunk_folder = chunk_folder
        
        # 确保目录存在
        os.makedirs(self.chunk_folder, exist_ok=True)
        
        # 初始化LlamaIndex设置
        # self.initialize_llama_index()
        
    def initialize_llama_index(self):
        """初始化LlamaIndex的设置"""
        try:
            # 检查OpenAI API密钥是否设置
            if not os.getenv("OPENAI_API_KEY"):
                print("警告: OPENAI_API_KEY 未设置")
                
            # 初始化嵌入模型和语言模型
            embed_model = OpenAIEmbedding(model="text-embedding-3-small")
            llm = OpenAI(model="gpt-3.5-turbo-0125")
            
            # 配置全局设置
            Settings.embed_model = embed_model
            Settings.llm = llm
            Settings.node_parser = SentenceSplitter(chunk_size=250, chunk_overlap=20)
        except Exception as e:
            print(f"初始化LlamaIndex设置时出错: {e}")
    
    def get_file_content(self, file_id):
        """
        根据文件ID获取load文件夹中的文件内容
        
        Args:
            file_id: 文件ID
            
        Returns:
            dict: 包含文件内容的字典，如果文件不存在则返回None
        """
        # 查找匹配的文件
        for filename in os.listdir(self.load_folder):
            if filename.startswith(file_id) or filename.split('.')[0] == file_id:
                file_path = os.path.join(self.load_folder, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return json.load(f), file_path
                except Exception as e:
                    print(f"读取文件 {file_path} 时出错: {e}")
                    return None, None
        
        print(f"未找到ID为 {file_id} 的文件")
        return None, None
    
    def chunk_document_llama_index(self, content, chunk_size=250, chunk_overlap=20):
        """
        使用LlamaIndex的SentenceSplitter对文档进行切分
        
        Args:
            content: 文档内容
            chunk_size: 每个chunk的大小
            chunk_overlap: chunk之间的重叠大小
            
        Returns:
            list: 包含切分后内容的列表
        """
        try:
            # 创建文档对象
            doc = Document(text=content)
            
            # 配置节点解析器
            node_parser = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            
            # 进行切分
            nodes = node_parser.get_nodes_from_documents([doc])
            
            # 提取切分后的文本内容
            chunks = [node.text for node in nodes]
            
            return chunks
        except Exception as e:
            print(f"使用LlamaIndex切分文档时出错: {e}")
            return []
    
    def chunk_document_langchain(self, content, chunk_size=500, chunk_overlap=50):
        """
        使用LangChain的RecursiveCharacterTextSplitter对文档进行切分
        
        Args:
            content: 文档内容
            chunk_size: 每个chunk的大小
            chunk_overlap: chunk之间的重叠大小
            
        Returns:
            list: 包含切分后内容的列表
        """
        try:
            # 创建文本分割器
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
            
            # 进行切分
            chunks = text_splitter.split_text(content)
            
            return chunks
        except Exception as e:
            print(f"使用LangChain切分文档时出错: {e}")
            return []
    
    def chunk_document_custom(self, content, separator="\n\n"):
        """
        使用自定义分隔符对文档进行切分
        
        Args:
            content: 文档内容
            separator: 分隔符
            
        Returns:
            list: 包含切分后内容的列表
        """
        try:
            # 使用分隔符进行简单切分
            chunks = content.split(separator)
            
            # 移除空白块
            chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
            
            return chunks
        except Exception as e:
            print(f"使用自定义方法切分文档时出错: {e}")
            return []
    
    def process_chunk(self, file_id, method, chunk_size=500, chunk_overlap=50, separator="\n\n"):
        """
        处理文件切分
        
        Args:
            file_id: 文件ID
            method: 切分方法 (langchain, llamaindex, custom)
            chunk_size: 块大小
            chunk_overlap: 块重叠大小
            separator: 自定义切分时的分隔符
            
        Returns:
            dict: 包含处理结果的字典
        """
        # 获取文件内容
        file_data, source_path = self.get_file_content(file_id)
        if not file_data:
            return {
                "success": False,
                "error": f"未找到ID为 {file_id} 的文件"
            }
        
        # 获取文档内容
        content = file_data.get("文件读取内容", "")
        if not content:
            return {
                "success": False,
                "error": "文件内容为空"
            }
        
        # 根据方法选择切分器
        chunks = []
        if method == "llamaindex":
            chunks = self.chunk_document_llama_index(content, chunk_size, chunk_overlap)
        elif method == "langchain":
            chunks = self.chunk_document_langchain(content, chunk_size, chunk_overlap)
        elif method == "custom":
            chunks = self.chunk_document_custom(content, separator)
        else:
            return {
                "success": False,
                "error": f"不支持的切分方法: {method}"
            }
        
        # 检查切分结果
        if not chunks:
            return {
                "success": False,
                "error": "切分过程中未生成任何内容块"
            }
        
        # 构建结果数据
        chunk_data = []
        for i, chunk in enumerate(chunks):
            chunk_data.append({
                "id": i + 1,
                "content": chunk
            })
        
        # 更新原始文件数据
        file_data["chunks"] = chunk_data
        file_data["chunk_method"] = method
        file_data["chunk_size"] = chunk_size
        file_data["chunk_overlap"] = chunk_overlap
        if method == "custom":
            file_data["chunk_separator"] = separator
        
        # 构建输出文件名
        filename = os.path.basename(source_path)
        base_name, _ = os.path.splitext(filename)
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        output_filename = f"{base_name}_chunked_{timestamp}.json"
        output_path = os.path.join(self.chunk_folder, output_filename)
        
        # 保存结果
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(file_data, f, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "file_id": file_id,
                "chunks": chunk_data,
                "chunk_method": method,
                "chunk_count": len(chunks),
                "output_path": output_path
            }
        except Exception as e:
            print(f"保存切分结果时出错: {e}")
            return {
                "success": False,
                "error": f"保存切分结果时出错: {str(e)}"
            }
    
    def get_chunked_files(self):
        """
        获取chunk文件夹下的所有切分文件
        
        Returns:
            list: 包含切分文件信息的列表
        """
        chunked_files = []
        
        try:
            # 检查目录是否存在
            if not os.path.exists(self.chunk_folder):
                print(f"目录不存在: {self.chunk_folder}")
                return chunked_files
            
            # 遍历目录中的所有文件
            for filename in os.listdir(self.chunk_folder):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.chunk_folder, filename)
                    
                    try:
                        # 读取文件以获取元数据
                        with open(file_path, 'r', encoding='utf-8') as f:
                            file_data = json.load(f)
                        
                        # 获取文件信息
                        file_id = os.path.splitext(filename)[0]
                        original_filename = file_data.get("文件名称", "未知")
                        chunk_method = file_data.get("chunk_method", "未知")
                        chunk_count = len(file_data.get("chunks", []))
                        created_time = file_data.get("切分时间", 
                                                  datetime.datetime.fromtimestamp(
                                                      os.path.getctime(file_path)
                                                  ).isoformat())
                        
                        # 构建文件信息对象
                        file_info = {
                            "id": file_id,
                            "filename": filename,
                            "original_filename": original_filename,
                            "chunk_method": chunk_method,
                            "chunk_count": chunk_count,
                            "file_path": file_path,
                            "created_at": created_time,
                            "file_size_bytes": os.path.getsize(file_path)
                        }
                        
                        chunked_files.append(file_info)
                    except Exception as e:
                        print(f"处理文件 {filename} 时出错: {e}")
            
            # 按创建时间排序，最新的排在前面
            chunked_files.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            return chunked_files
        except Exception as e:
            print(f"获取切分文件列表时出错: {e}")
            return [] 