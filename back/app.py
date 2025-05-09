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
from services.file_vector import VectorFileProcessor
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
vector_file_processor = VectorFileProcessor()

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
        # Get the embedding file ID from query parameters
        embedding_file_id = request.args.get('embedding_file_id')
        if not embedding_file_id:
            logger.warning("Missing 'embedding_file_id' query parameter")
            return jsonify({
                "success": False,
                "error": "Missing required query parameter: embedding_file_id"
            }), 400

        # 使用默认的huggingface模型查询统计信息
        # Note: The model_type might not matter for just getting stats if the file exists.
        embedding_processor = EmbeddingClass(model_type="huggingface") 
        stats = embedding_processor.get_embedding_stats(embedding_file_id)

        if stats.get("exists"):
            logger.info(f"成功获取嵌入向量统计信息 for {embedding_file_id}")
            return jsonify({
                "success": True,
                "stats": stats
            }), 200
        else:
            message = stats.get("message", f"未找到嵌入向量文件 for {embedding_file_id}")
            error_detail = stats.get("error")
            if error_detail:
                logger.error(f"Error getting embedding stats for {embedding_file_id}: {error_detail}")
                return jsonify({
                    "success": False,
                    "error": f"获取统计信息时出错: {error_detail}"
                }), 500
            else:
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

@app.route('/api/vector/stats', methods=['GET'])
def get_vector_files_stats():
    """
    获取 files/embedding 文件夹下所有向量文件的统计信息
    """
    try:
        logger.info("请求获取所有向量文件统计信息")
        result = vector_file_processor.get_all_vector_file_stats()
        
        if result["success"]:
            logger.info(f"成功返回 {len(result['files'])} 个向量文件的统计信息")
            return jsonify(result), 200
        else:
            logger.error(f"获取向量文件统计信息失败: {result.get('error', '未知错误')}")
            # Determine status code based on error type if possible, otherwise 500
            status_code = 404 if "not found" in result.get("error", "").lower() else 500
            return jsonify(result), status_code
    
    except Exception as e:
        logger.error(f"处理 /api/vector/stats 请求时发生意外错误: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"处理请求时发生意外错误: {str(e)}",
            "files": []
        }), 500

@app.route('/api/vector/store', methods=['POST'])
def store_vectors_to_db():
    """
    Stores vectors from a specified embedding file into a vector database.
    """
    try:
        data = request.get_json()
        if not data:
            logger.warning("No JSON data provided in /api/vector/store request")
            return jsonify({"success": False, "error": "Missing JSON payload"}), 400

        embedding_file_id = data.get('embedding_file_id')
        vector_store_type = data.get('vector_store_type')
        collection_name = data.get('collection_name')
        dimension = data.get('dimension') # Dimension should be sent by frontend

        if not all([embedding_file_id, vector_store_type, collection_name]):
            logger.warning(f"Missing required parameters in /api/vector/store: file_id, type, or collection_name. Received: {data}")
            return jsonify({"success": False, "error": "Missing required parameters: embedding_file_id, vector_store_type, collection_name"}), 400
        
        # Dimension is critical for Milvus schema
        if vector_store_type == "milvus" and (not isinstance(dimension, int) or dimension <= 0):
             logger.warning(f"Invalid or missing dimension for Milvus: {dimension}")
             return jsonify({"success": False, "error": "Valid 'dimension' (integer > 0) is required for Milvus store type."}), 400


        logger.info(f"Request to store vectors: file='{embedding_file_id}', type='{vector_store_type}', collection='{collection_name}', dim='{dimension}'")

        if vector_store_type == "milvus":
            result = vector_file_processor.store_vectors_to_milvus_lite(
                embedding_file_id=embedding_file_id,
                collection_name=collection_name,
                dimension=dimension
            )
        # elif vector_store_type == "chroma":
            # result = vector_file_processor.store_vectors_to_chroma(...) # Placeholder for Chroma
            # pass
        else:
            logger.warning(f"Unsupported vector_store_type: {vector_store_type}")
            return jsonify({"success": False, "error": f"Unsupported vector_store_type: {vector_store_type}"}), 400

        if result.get("success"):
            logger.info(f"Successfully processed /api/vector/store: {result.get('message')}")
            return jsonify(result), 200
        else:
            logger.error(f"Error processing /api/vector/store: {result.get('error')}")
            return jsonify(result), 500 # Or 400 if client-side error like file not found

    except Exception as e:
        logger.error(f"Unexpected error in /api/vector/store: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"An unexpected server error occurred: {str(e)}"
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