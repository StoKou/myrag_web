# RAG 检索系统后端

这是 RAG（检索增强生成）系统的后端部分，基于 Flask 框架构建。

## 目录结构

```
back/
├── files/           # 文件存储目录
│   ├── upload/      # 上传的原始文件
│   └── load/        # 处理后的文本文件
├── log/             # 日志文件目录
├── services/        # 服务模块目录
│   ├── __init__.py
│   ├── file_processor.py  # 文件处理服务
│   └── logger.py    # 日志配置服务
├── app.py           # 主应用入口
├── requirements.txt # 依赖列表
├── setup.py         # 初始化脚本
└── README.md        # 本文件
```

## 功能

- 接收前端上传的文件
- 使用 unstructured 库解析不同类型的文档
- 将解析结果保存为文本文件
- 返回处理结果给前端

## 安装和设置

1. 创建虚拟环境（推荐）:
   ```
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

2. 安装依赖:
   ```
   pip install -r requirements.txt
   ```

3. 运行初始化脚本:
   ```
   python setup.py
   ```

4. 启动应用:
   ```
   python app.py
   ```

服务器将在 http://localhost:5000 上运行。

## API 端点

### 文件上传

- **URL**: `/api/upload`
- **方法**: `POST`
- **参数**:
  - `file`: 文件对象
  - `type`: 文件类型 (pdf, txt, md, xlsx, xls, docx, pptx)
- **响应**:
  ```json
  {
    "message": "文件 'example.pdf' (类型: pdf) 上传成功并处理完毕。",
    "data": {
      "processed": true,
      "timestamp": "2023-11-01T12:34:56.789Z",
      "original_filename": "example.pdf",
      "processed_file_path": "files/load/example.txt",
      "content_preview": "文件内容预览..."
    }
  }
  ```

### 健康检查

- **URL**: `/api/health`
- **方法**: `GET`
- **响应**:
  ```json
  {
    "status": "ok",
    "timestamp": "2023-11-01T12:34:56.789Z"
  }
  ```

## 日志

日志文件存储在 `log` 目录中:
- `app.log`: 所有级别的日志
- `error.log`: 仅错误级别的日志 