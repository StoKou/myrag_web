<template>
  <div class="home-container">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>RAG 智能文档检索系统</span>
        </div>
      </template>
      <div class="project-description">
        <p>
          欢迎使用 RAG (Retrieval-Augmented Generation) 智能文档检索系统。
          本项目旨在构建一个高效、智能的本地文档问答与检索解决方案。
        </p>
        <h3>核心功能：</h3>
        <el-timeline style="max-width: 600px; margin-left: 20px; margin-top: 20px;">
          <el-timeline-item timestamp="文档处理" placement="top">
            <el-card>
              <h4>文档加载与解析</h4>
              <p>支持多种格式文档（如 PDF, TXT, Markdown 等）的加载与内容解析。</p>
            </el-card>
          </el-timeline-item>
          <el-timeline-item timestamp="数据准备" placement="top">
            <el-card>
              <h4>文档切分与向量化</h4>
              <p>将加载的文档智能切分成合适的块，并使用先进的 embedding 模型将其转换为向量表示。</p>
            </el-card>
          </el-timeline-item>
          <el-timeline-item timestamp="数据存储" placement="top">
            <el-card>
              <h4>向量存储</h4>
              <p>将文档向量存储在高效的向量数据库中，以便快速检索。</p>
            </el-card>
          </el-timeline-item>
          <el-timeline-item timestamp="智能检索" placement="top">
            <el-card>
              <h4>语义检索与问答</h4>
              <p>根据用户输入的问题或关键词，在向量数据库中进行语义相似度检索，找到最相关的文档片段。</p>
              <p>（可选）结合大型语言模型 (LLM) 对检索到的内容进行整合、摘要或生成更自然的回答。</p>
            </el-card>
          </el-timeline-item>
        </el-timeline>

        <p style="margin-top: 30px;">
          您可以通过侧边栏的 <strong>Load</strong> 页面上传和处理您的文档。
        </p>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
// No specific script logic needed for this static page
</script>

<style scoped>
.home-container {
  padding: 20px;
}

.box-card {
  width: 100%;
}

.card-header {
  text-align: center;
  font-size: 1.5em;
  font-weight: bold;
}

.project-description h3 {
  margin-top: 25px;
  margin-bottom: 15px;
  color: #303133;
}

.project-description p {
  line-height: 1.6;
  color: #606266;
}

.el-timeline-item h4 {
  margin-top: 0;
  margin-bottom: 10px;
}
</style> 