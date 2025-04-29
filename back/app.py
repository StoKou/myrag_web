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
from services.file_embedding import EmbeddingClass
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
    
    # 获取参数
    file = request.files['file']
    file_type = request.form.get('type')
    
    # 委托给FileProcessor处理所有上传和处理逻辑
    result, status_code = file_processor.handle_upload_request(
        file=file,
        file_type=file_type,
        allowed_extensions=ALLOWED_EXTENSIONS,
        logger=logger
    )
    
    return jsonify(result), status_code

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

@app.route('/api/embedding', methods=['POST'])
def generate_embeddings():
    """
    为切分后的文档生成嵌入向量
    """
    try:
        # 获取请求参数
        data = request.json
        if not data:
            logger.warning("请求中没有JSON数据")
            return jsonify({"success": False, "error": "请求中没有JSON数据"}), 400
        
        chunk_file_id = data.get('chunkFileId')
        model_type = data.get('modelType', 'huggingface')  # 默认使用huggingface
        
        # 验证必要参数
        if not chunk_file_id:
            logger.warning("未提供chunk文件ID")
            return jsonify({"success": False, "error": "未提供chunk文件ID"}), 400
        
        # 验证模型类型
        if model_type not in ['huggingface', 'openai']:
            logger.warning(f"不支持的模型类型: {model_type}")
            return jsonify({"success": False, "error": f"不支持的模型类型: {model_type}"}), 400
        
        # 处理向量嵌入
        logger.info(f"开始生成嵌入向量: chunkFileId={chunk_file_id}, modelType={model_type}")
        embedding_processor = EmbeddingClass(model_type=model_type)
        result = embedding_processor.process_embeddings(chunk_file_id)
        
        if result["success"]:
            logger.info(f"嵌入向量生成成功: chunkFileId={chunk_file_id}")
            return jsonify(result), 200
        else:
            logger.warning(f"嵌入向量生成失败: {result.get('error', '未知错误')}")
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"处理嵌入向量请求时出错: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"处理嵌入向量请求时出错: {str(e)}"
        }), 500

@app.route('/api/embedding/stats', methods=['GET'])
def get_embedding_stats():
    """
    获取嵌入向量的统计信息
    """
    try:
        # 使用默认的huggingface模型查询统计信息
        embedding_processor = EmbeddingClass(model_type="huggingface")
        stats = embedding_processor.get_embedding_stats()
        
        if stats.get("exists"):
            logger.info("成功获取嵌入向量统计信息")
            return jsonify({
                "success": True,
                "stats": stats
            }), 200
        else:
            message = stats.get("message", "未找到嵌入向量文件")
            logger.warning(message)
            return jsonify({
                "success": False,
                "message": message
            }), 404
    
    except Exception as e:
        logger.error(f"获取嵌入向量统计信息时出错: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"获取嵌入向量统计信息时出错: {str(e)}"
        }), 500

@app.route('/api/files/chunk', methods=['GET'])
def get_chunk_files():
    """
    获取chunk文件夹下的文件列表
    """
    try:
        chunked_files = file_chunk_processor.get_chunked_files()
        logger.info(f"获取到 {len(chunked_files)} 个已切分文件")
        
        return jsonify({
            "success": True,
            "files": chunked_files,
            "timestamp": datetime.datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"获取切分文件列表时出错: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"获取切分文件列表失败: {str(e)}"
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