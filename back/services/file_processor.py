"""
文件处理服务模块，负责使用 unstructured 库解析不同类型的文件。
"""
import os
import json
import datetime
from unstructured.partition.auto import partition
from werkzeug.utils import secure_filename

class FileProcessor:
    def __init__(self, upload_folder, load_folder):
        """
        初始化文件处理器
        
        Args:
            upload_folder: 上传文件存储目录
            load_folder: 处理后文件存储目录
        """
        self.upload_folder = upload_folder
        self.load_folder = load_folder
        
        # 确保目录存在
        os.makedirs(self.upload_folder, exist_ok=True)
        os.makedirs(self.load_folder, exist_ok=True)
    
    def allowed_file(self, filename, allowed_extensions):
        """
        检查文件类型是否允许
        
        Args:
            filename: 文件名
            allowed_extensions: 允许的扩展名集合
            
        Returns:
            bool: 如果文件类型允许则返回 True，否则返回 False
        """
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
    
    def save_upload_file(self, file, file_type):
        """
        保存上传的文件，保留原始文件名（包括非ASCII字符），并在扩展名前添加时间戳。
        
        Args:
            file: 上传的文件对象
            file_type: 文件类型 (来自前端选择)
            
        Returns:
            dict: 包含文件名和路径信息的字典
        """
        # 直接获取原始文件名
        original_filename = file.filename

        # 检查原始文件名是否为空或包含路径分隔符 (基础安全检查)
        if not original_filename or '/' in original_filename or '\\' in original_filename or '..' in original_filename:
            raise ValueError(f"检测到不安全或无效的文件名: {original_filename}")
            
        # 分离原始文件名的基本部分和扩展名
        filename_base, extension = os.path.splitext(original_filename)
        
        # 生成时间戳
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        
        # 构建新的带时间戳的文件名 (格式: 原始基本名称_时间戳.原始扩展名)
        timestamped_filename = f"{filename_base}_{timestamp}{extension}"
        
        # 构建上传路径
        upload_path = os.path.join(self.upload_folder, timestamped_filename)
        
        # 如果需要处理重名文件，可以在这里添加逻辑
        # 当前实现会覆盖同名文件 (虽然时间戳基本保证了唯一性)
        file.save(upload_path)
        
        # 构建处理后 JSON 文件的路径 (也带时间戳，使用原始基本名称)
        load_filename = f"{filename_base}_{timestamp}.json"
        load_path = os.path.join(self.load_folder, load_filename)
        
        return {
            "original_filename": original_filename, # 记录用户上传时的原始名称
            "filename": timestamped_filename,  # 记录处理后带时间戳的文件名
            "upload_path": upload_path,
            "load_path": load_path,
            "timestamp": timestamp,
            "file_type": file_type
        }
    
    def process_file(self, file_info):
        """
        使用 unstructured 处理文件并保存结果为 JSON
        
        Args:
            file_info: 文件信息字典，包含上传路径和输出路径
            
        Returns:
            dict: 包含处理结果的字典
        """
        upload_path = file_info["upload_path"]
        load_path = file_info["load_path"]
        
        try:
            # 使用 unstructured 处理文件
            elements = partition(filename=upload_path, strategy='auto')
            processed_content = "\n\n".join([str(el) for el in elements])
            
            # 创建JSON数据结构
            json_data = {
                "文件名称": file_info["filename"], # 使用带时间戳的文件名
                "文件读取内容": processed_content,
                "文件读取方式": file_info["file_type"] # 记录前端选择的类型
            }
            
            # 保存处理结果为JSON格式
            with open(load_path, 'w', encoding='utf-8') as f_out:
                json.dump(json_data, f_out, ensure_ascii=False, indent=2)
            
            return {
                "processed_content": processed_content,
                "content_length": len(processed_content)
            }
        except Exception as e:
            # 在这里可以添加更详细的日志记录
            print(f"Error processing file {upload_path}: {e}")
            raise # 重新抛出异常，让上层处理 
    
    def get_loaded_files(self):
        """
        获取load文件夹下的所有文件列表
        
        Returns:
            list: 包含文件信息的列表，每个文件信息包含id、filename和path
        """
        files = []
        
        # 检查load文件夹是否存在
        if not os.path.exists(self.load_folder):
            return files
            
        # 获取文件夹中的所有文件
        for filename in os.listdir(self.load_folder):
            # 只处理json文件
            if filename.endswith('.json'):
                file_path = os.path.join(self.load_folder, filename)
                
                # 获取文件元数据
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_data = json.load(f)
                        
                    # 提取原始文件名（如果存在）或使用当前文件名
                    original_name = file_data.get("文件名称", filename)
                    
                    # 构建文件信息
                    file_info = {
                        "id": filename.split('.')[0],  # 使用不带扩展名的文件名作为ID
                        "filename": original_name,
                        "path": file_path
                    }
                    
                    files.append(file_info)
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")
                    # 如果无法读取文件内容，仍添加基本信息
                    files.append({
                        "id": filename.split('.')[0],
                        "filename": filename,
                        "path": file_path
                    })
        
        return files 