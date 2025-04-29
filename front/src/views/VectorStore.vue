<template>
  <div class="vector-store-container">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>向量存储管理</span>
        </div>
      </template>
      
      <el-row :gutter="20">
        <!-- 左侧：向量存储选择与配置 -->
        <el-col :span="8">
          <el-card class="inner-card">
            <template #header>
              <div class="inner-card-header">
                <span>向量存储配置</span>
              </div>
            </template>
            
            <div class="storage-config">
              <el-form :model="storageConfig" label-position="top">
                <el-form-item label="选择向量存储类型">
                  <el-radio-group v-model="storageConfig.type">
                    <el-radio label="milvus">Milvus</el-radio>
                    <el-radio label="chroma">Chroma</el-radio>
                  </el-radio-group>
                </el-form-item>
                
                <template v-if="storageConfig.type === 'milvus'">
                  <el-form-item label="Milvus 主机地址">
                    <el-input v-model="storageConfig.milvus.host" placeholder="localhost"></el-input>
                  </el-form-item>
                  <el-form-item label="Milvus 端口">
                    <el-input v-model="storageConfig.milvus.port" placeholder="19530"></el-input>
                  </el-form-item>
                  <el-form-item label="集合名称">
                    <el-input v-model="storageConfig.milvus.collection" placeholder="documents"></el-input>
                  </el-form-item>
                </template>
                
                <template v-if="storageConfig.type === 'chroma'">
                  <el-form-item label="Chroma 服务地址">
                    <el-input v-model="storageConfig.chroma.url" placeholder="http://localhost:8000"></el-input>
                  </el-form-item>
                  <el-form-item label="集合名称">
                    <el-input v-model="storageConfig.chroma.collection" placeholder="documents"></el-input>
                  </el-form-item>
                </template>
                
                <el-form-item>
                  <el-button type="primary" @click="getVectorData">获取向量数据</el-button>
                  <el-button type="success" @click="testConnection">测试连接</el-button>
                </el-form-item>
              </el-form>
            </div>
          </el-card>
        </el-col>
        
        <!-- 右侧：向量数据展示 -->
        <el-col :span="16">
          <el-card class="inner-card">
            <template #header>
              <div class="inner-card-header">
                <span>向量数据展示</span>
                <el-tag v-if="vectorData.length > 0" type="success">
                  共 {{ vectorData.length }} 条数据
                </el-tag>
              </div>
            </template>
            
            <div v-if="loading" class="loading-container">
              <el-empty v-if="!loading && vectorData.length === 0" description="暂无数据" />
              <el-skeleton v-else :rows="6" animated />
            </div>
            
            <div v-else class="vector-data">
              <el-table v-if="vectorData.length > 0" :data="vectorData" height="500" style="width: 100%">
                <el-table-column prop="id" label="ID" width="180" />
                <el-table-column prop="text" label="文本内容">
                  <template #default="scope">
                    <el-tooltip
                      class="box-item"
                      effect="dark"
                      :content="scope.row.text"
                      placement="top-start"
                      :hide-after="2000"
                    >
                      <div class="truncated-text">{{ scope.row.text }}</div>
                    </el-tooltip>
                  </template>
                </el-table-column>
                <el-table-column prop="metadata.source" label="来源" width="180" />
                <el-table-column label="操作" width="120">
                  <template #default="scope">
                    <el-button size="small" @click="showVectorDetails(scope.row)">详情</el-button>
                  </template>
                </el-table-column>
              </el-table>
              
              <el-empty v-else description="暂无向量数据" />
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>
    
    <!-- 向量详情对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="向量详情"
      width="60%"
    >
      <pre class="vector-details">{{ JSON.stringify(currentVector, null, 2) }}</pre>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'

// 向量存储配置
const storageConfig = reactive({
  type: 'milvus', // 默认选择 milvus
  milvus: {
    host: 'localhost',
    port: '19530',
    collection: 'documents'
  },
  chroma: {
    url: 'http://localhost:8000',
    collection: 'documents'
  }
})

// 向量数据状态
const vectorData = ref<any[]>([])
const loading = ref(false)

// 向量详情对话框
const dialogVisible = ref(false)
const currentVector = ref<any>(null)

// 获取向量数据
const getVectorData = async () => {
  loading.value = true
  
  try {
    // 这里模拟从后端获取数据
    // 实际项目中应该调用后端API
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 模拟数据响应
    vectorData.value = [
      {
        id: '1',
        text: '这是第一条向量数据，包含了一些关于人工智能的基本信息...',
        metadata: {
          source: 'AI教程.pdf',
          page: 10
        },
        vector: new Array(5).fill(0).map(() => Math.random())
      },
      {
        id: '2',
        text: '向量数据库是专门为嵌入向量设计的数据库，提供高效的相似性搜索功能...',
        metadata: {
          source: '向量数据库指南.md',
          page: 3
        },
        vector: new Array(5).fill(0).map(() => Math.random())
      },
      {
        id: '3',
        text: 'RAG(检索增强生成)是一种结合检索系统和生成模型的方法，可以提高大语言模型的知识获取能力...',
        metadata: {
          source: 'RAG论文.pdf',
          page: 1
        },
        vector: new Array(5).fill(0).map(() => Math.random())
      }
    ]
    
    ElMessage.success('成功获取向量数据')
  } catch (error) {
    console.error('获取向量数据失败:', error)
    ElMessage.error('获取向量数据失败')
  } finally {
    loading.value = false
  }
}

// 测试连接
const testConnection = () => {
  loading.value = true
  
  setTimeout(() => {
    loading.value = false
    ElMessage.success(`成功连接到${storageConfig.type === 'milvus' ? 'Milvus' : 'Chroma'}服务`)
  }, 1000)
}

// 显示向量详情
const showVectorDetails = (row: any) => {
  currentVector.value = row
  dialogVisible.value = true
}
</script>

<style scoped>
.vector-store-container {
  padding: 20px;
}

.box-card {
  width: 100%;
  margin-bottom: 20px;
}

.card-header {
  text-align: center;
  font-size: 1.5em;
  font-weight: bold;
}

.inner-card {
  height: 100%;
  box-sizing: border-box;
}

.inner-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.storage-config {
  padding: 10px 0;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.vector-data {
  min-height: 300px;
}

.truncated-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 300px;
}

.vector-details {
  white-space: pre-wrap;
  word-break: break-word;
  font-family: monospace;
  background-color: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  max-height: 400px;
  overflow-y: auto;
}
</style> 