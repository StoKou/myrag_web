# myrag_web

## 项目介绍

MyRAG Web 是一个基于 RAG（检索增强生成）技术的文档处理和检索系统。该系统由前端和后端两部分组成，可以接收用户上传的各种文档，进行处理、分块并支持检索功能。

### 主要功能

- 支持多种文件格式的上传（PDF、TXT、MD、XLSX、XLS、DOCX、PPTX等）
- 文档内容提取与处理
- 文档分块处理（支持多种分块方法）
- 文档内容检索服务

### 技术栈

#### 前端
- Vue 3 + TypeScript
- Element Plus UI组件库
- Vite 构建工具
- Pinia 状态管理
- Vue Router 路由管理

#### 后端
- Flask Web框架
- Unstructured 文档处理库
- LlamaIndex 文档分块和向量化处理

## 项目结构

```
myrag_web/
├── back/               # 后端部分
│   ├── files/          # 文件存储目录
│   ├── log/            # 日志文件目录
│   ├── services/       # 服务模块目录
│   ├── app.py          # 主应用入口
│   ├── requirements.txt # 后端依赖
│   └── setup.py        # 初始化脚本
│
└── front/              # 前端部分
    ├── public/         # 静态资源
    ├── src/            # 源代码
    ├── package.json    # 前端依赖
    └── vite.config.ts  # Vite配置
```

## 运行方式

### 后端服务

1. 进入后端目录：
   ```bash
   cd back
   ```

2. 创建虚拟环境（推荐）：
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

4. 运行初始化脚本：
   ```bash
   python setup.py
   ```

5. 启动后端服务：
   ```bash
   python app.py
   ```

后端服务将在 http://localhost:5000 上运行。

### 前端应用

1. 进入前端目录：
   ```bash
   cd front
   ```

2. 安装依赖：
   ```bash
   npm install
   ```

3. 启动开发服务器：
   ```bash
   npm run dev
   ```

4. 构建生产版本：
   ```bash
   npm run build
   ```

前端开发服务器将在 http://localhost:5173 上运行。

## 项目完成时间线

| 时间                 | 已完成                                                            | 下一阶段计划                               | 待解决问题                                                                 |
| :------------------- | :---------------------------------------------------------------- | :----------------------------------------- | :------------------------------------------------------------------------- |
| 2025年4月29日 上午   | - 文件读取功能实现<br>- 文件读取测试用例编写<br>- 文档分块功能开发 | - 文档分块测试用例编写<br>- 数据向量库开发与实现 |                                                                            |
| 2025年4月29日 晚上21:00 | - 后端测试代码编写<br>- 前端 embedding、vectorstore 开发<br>- 后端 embedding 开发 |                                            | - Ubuntu 网络配置问题导致后端无法下载 embedding 模型<br>- 后端向量数据集初始化等系列工作未完成 |
| 今天2025年4月30日                 | - 完成git创建分支和提交学习<br>- 学习PR请求                       |                                            |                                                                            |
| 2025年5月1日         | - embedding 的编码和前端显示<br>- 后端代理的配置<br>- 后端的 embedding 接口<br>- 调整前端界面 | - 后端测试文件的编写<br>- 前端支持 embedding 可视化显示 (含切换)<br>- 后端向量数据库的配置<br>- 完成向量数据库部分 (至少一个)<br>- 完成整体项目环境测试 |                                                                            |
| 2025年5月10日        | - 完成milvus list向量数据库的存储和前端更新<br>- 完成两个测试流程 | - 需要完成向量的相似度匹配功能<br>- 完成大模型输入和输出功能 | - 向量数据库存储完成和<br>- 前端显示只有弹窗，没有静态显示git              |
