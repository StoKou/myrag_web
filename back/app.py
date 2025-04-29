"""
Flask 应用主入口
提供 RESTful API 服务，用于文件上传和内容提取。
"""
import os
import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# 导入自定义服务模块
from services.file_processor import FileProcessor
from services.file_chunk import FileChunkProcessor
from services.logger import setup_logger

# 配置常量
UPLOAD_FOLDER = os.path.join('files', 'upload')
LOAD_FOLDER = os.path.join('files', 'load')
CHUNK_FOLDER = os.path.join('files', 'chunk')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'md', 'xlsx', 'xls', 'docx', 'pptx'}

# 初始化 Flask 应用
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['LOAD_FOLDER'] = LOAD_FOLDER

# 配置 CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# 设置日志记录器
logger = setup_logger(app)

# 初始化文件处理器
file_processor = FileProcessor(UPLOAD_FOLDER, LOAD_FOLDER)
file_chunk_processor = FileChunkProcessor(LOAD_FOLDER, CHUNK_FOLDER)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    处理文件上传请求，解析文件内容并返回结果
    """
    # 检查是否有文件部分
    if 'file' not in request.files:
        logger.warning("没有文件部分在请求中")
        return jsonify({"error": "没有文件部分"}), 400
    
    file = request.files['file']
    file_type = request.form.get('type')
    
    # 检查文件名是否为空
    if file.filename == '':
        logger.warning("没有选择文件")
        return jsonify({"error": "没有选择文件"}), 400
    
    # 检查文件类型是否指定
    if not file_type:
        logger.warning("没有指定文件类型")
        return jsonify({"error": "没有指定文件类型"}), 400
    
    # 检查文件类型是否允许
    if not file_processor.allowed_file(file.filename, ALLOWED_EXTENSIONS):
        logger.warning(f"不允许的文件类型: {file.filename}")
        return jsonify({"error": "不允许的文件类型"}), 400
    
    try:
        # 保存上传的文件
        logger.info(f"开始处理文件: {file.filename}, 类型: {file_type}")
        file_info = file_processor.save_upload_file(file, file_type)
        
        # 处理文件
        logger.info(f"文件已保存到: {file_info['upload_path']}, 开始提取内容")
        result = file_processor.process_file(file_info)
        
        processed_content = result["processed_content"]
        logger.info(f"内容提取完成，长度: {result['content_length']} 字符")
        logger.info(f"处理结果已保存到: {file_info['load_path']}")
        
        # 返回结果
        result_payload = {
            "message": f"文件 '{file_info['filename']}' (类型: {file_type}) 上传成功并处理完毕。",
            "data": {
                "processed": True,
                "timestamp": datetime.datetime.now().isoformat(),
                "original_filename": file_info['filename'],
                "filename": file_info['filename'],
                "upload_path": file_info['upload_path'],
                "processed_file_path": file_info['load_path'],
                "content_preview": processed_content[:500] + ('... (截断)' if len(processed_content) > 500 else '')
            }
        }
        
        return jsonify(result_payload), 200
    
    except Exception as e:
        # 记录完整错误日志
        logger.error(f"处理文件 {file.filename} 时出错: {str(e)}", exc_info=True)
        return jsonify({"error": f"处理文件失败: {str(e)}"}), 500

@app.route('/api/files/load', methods=['GET']) 
def get_loaded_files():
    """
    获取load文件夹下的文件列表
    """
    try:
        files = file_processor.get_loaded_files()
        logger.info(f"获取到 {len(files)} 个已加载文件")
        
        return jsonify({
            "success": True,
            "files": files,
            "timestamp": datetime.datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"获取文件列表时出错: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"获取文件列表失败: {str(e)}"
        }), 500

@app.route('/api/chunk', methods=['POST'])
def chunk_file():
    """
    处理文件切分请求
    """
    try:
        # 获取请求参数
        data = request.json
        if not data:
            logger.warning("请求中没有JSON数据")
            return jsonify({"success": False, "error": "请求中没有JSON数据"}), 400
        
        file_id = data.get('fileId')
        method = data.get('method', 'llamaindex')
        chunk_size = int(data.get('chunkSize', 500))
        chunk_overlap = int(data.get('chunkOverlap', 50))
        separator = data.get('separator', '\n\n')
        
        # 验证必要参数
        if not file_id:
            logger.warning("未提供文件ID")
            return jsonify({"success": False, "error": "未提供文件ID"}), 400
        
        # 处理文件切分
        logger.info(f"开始处理文件切分: fileId={file_id}, method={method}, chunkSize={chunk_size}, chunkOverlap={chunk_overlap}")
        result = file_chunk_processor.process_chunk(file_id, method, chunk_size, chunk_overlap, separator)
        
        if result["success"]:
            logger.info(f"文件切分成功: fileId={file_id}, chunkCount={result['chunk_count']}")
            return jsonify(result), 200
        else:
            logger.warning(f"文件切分失败: {result['error']}")
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"处理文件切分请求时出错: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"处理文件切分请求时出错: {str(e)}"
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    健康检查端点，用于监控应用状态
    """
    return jsonify({
        "status": "ok",
        "timestamp": datetime.datetime.now().isoformat()
    }), 200

if __name__ == '__main__':
    logger.info("应用启动，监听端口: 5000")
    app.run(debug=True, port=5000)