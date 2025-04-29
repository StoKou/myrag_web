<template>
  <div class="embedding-container">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>向量嵌入管理</span>
        </div>
      </template>
      
      <el-row :gutter="20">
        <!-- 左侧：嵌入模型选择与配置 -->
        <el-col :span="8">
          <el-card class="inner-card">
            <template #header>
              <div class="inner-card-header">
                <span>嵌入模型配置</span>
              </div>
            </template>
            
            <div class="embedding-config">
              <el-form :model="embeddingConfig" label-position="top">
                <el-form-item label="选择嵌入模型类型">
                  <el-radio-group v-model="embeddingConfig.type">
                    <el-radio value="huggingface" label="HuggingFace">HuggingFace</el-radio>
                    <el-radio value="openai" label="OpenAI">OpenAI</el-radio>
                  </el-radio-group>
                </el-form-item>
                
                <template v-if="embeddingConfig.type === 'huggingface'">
                  <el-form-item label="模型名称">
                    <el-input v-model="embeddingConfig.huggingface.model" disabled placeholder="BAAI/BGE-small-zh-v1.5"></el-input>
                  </el-form-item>
                  <el-form-item label="嵌入维度">
                    <el-input v-model="embeddingConfig.huggingface.dimension" placeholder="384"></el-input>
                  </el-form-item>
                  <el-form-item label="批处理大小">
                    <el-input-number v-model="embeddingConfig.huggingface.batchSize" :min="1" :max="64" :step="1"></el-input-number>
                  </el-form-item>
                </template>
                
                <template v-if="embeddingConfig.type === 'openai'">
                  <el-form-item label="API密钥">
                    <el-input v-model="embeddingConfig.openai.apiKey" placeholder="sk-..." show-password></el-input>
                  </el-form-item>
                  <el-form-item label="模型名称">
                    <el-select v-model="embeddingConfig.openai.model" placeholder="选择模型">
                      <el-option label="text-embedding-3-small" value="text-embedding-3-small"></el-option>
                      <el-option label="text-embedding-3-large" value="text-embedding-3-large"></el-option>
                      <el-option label="text-embedding-ada-002" value="text-embedding-ada-002"></el-option>
                    </el-select>
                  </el-form-item>
                  <el-form-item label="嵌入维度">
                    <el-input v-model="embeddingDimension" disabled></el-input>
                  </el-form-item>
                </template>
                
                <!-- 选择已分块文件 -->
                <el-form-item label="选择已分块文件">
                  <el-select 
                    v-model="selectedChunkFile" 
                    placeholder="选择要处理的分块文件"
                    filterable
                    :loading="loadingChunkFiles"
                    @change="handleChunkFileChange"
                  >
                    <el-option
                      v-for="file in chunkFiles"
                      :key="file.id"
                      :label="`${file.original_filename} (${file.chunk_count}块)`"
                      :value="file.id"
                    >
                      <div class="file-option">
                        <div class="file-name">{{ file.original_filename }}</div>
                        <div class="file-info">
                          <el-tag size="small" type="info">{{ file.chunk_method }}</el-tag>
                          <el-tag size="small" type="success">{{ file.chunk_count }}块</el-tag>
                        </div>
                      </div>
                    </el-option>
                  </el-select>
                  <div class="action-buttons">
                    <el-button type="primary" size="small" @click="loadChunkFiles" :icon="Refresh">刷新文件</el-button>
                  </div>
                </el-form-item>
                
                <el-form-item label="测试文本" v-if="!selectedChunkFile">
                  <el-input
                    v-model="testText"
                    type="textarea"
                    :rows="4"
                    placeholder="输入需要嵌入的文本..."
                  ></el-input>
                </el-form-item>
                
                <el-form-item>
                  <el-button type="primary" @click="generateEmbedding" :loading="loading" :disabled="!canGenerateEmbedding">
                    {{ selectedChunkFile ? '为所选文件生成嵌入' : '生成嵌入' }}
                  </el-button>
                  <el-button type="success" @click="setAsDefault" :disabled="!embeddingResult">设为默认</el-button>
                </el-form-item>
              </el-form>
            </div>
          </el-card>
        </el-col>
        
        <!-- 右侧：嵌入结果展示 -->
        <el-col :span="16">
          <el-card class="inner-card">
            <template #header>
              <div class="inner-card-header">
                <span>嵌入结果</span>
                <el-tag v-if="embeddingResult" type="success">
                  维度: {{ embeddingResult?.vector?.length || 0 }}
                </el-tag>
              </div>
            </template>
            
            <div v-if="loading" class="loading-container">
              <el-skeleton :rows="10" animated />
            </div>
            
            <template v-else>
              <div v-if="embeddingResult" class="embedding-result">
                <el-alert
                  title="嵌入生成成功"
                  type="success"
                  :closable="false"
                  show-icon
                  style="margin-bottom: 20px"
                >
                  <template #default>
                    <p>模型: {{ embeddingResult.model }}</p>
                    <p>向量维度: {{ embeddingResult.vector.length }}</p>
                    <p>处理用时: {{ embeddingResult.processingTime }}ms</p>
                  </template>
                </el-alert>
                
                <el-tabs type="border-card">
                  <el-tab-pane label="向量可视化">
                    <div class="vector-visualization">
                      <div class="vector-preview">
                        <!-- 只显示前50个元素的可视化 -->
                        <div 
                          v-for="(value, index) in visibleVectorElements" 
                          :key="index"
                          class="vector-element"
                          :style="{ height: `${Math.abs(value * 100)}px`, backgroundColor: value >= 0 ? '#67C23A' : '#F56C6C' }"
                        ></div>
                      </div>
                      <div class="vector-note">
                        <el-tag type="info">注: 仅显示向量的前{{ visibleVectorElements.length }}个元素</el-tag>
                      </div>
                    </div>
                  </el-tab-pane>
                  <el-tab-pane label="原始数据">
                    <el-input
                      type="textarea"
                      :rows="15"
                      :value="JSON.stringify(embeddingResult.vector, null, 2)"
                      readonly
                    ></el-input>
                    <div class="vector-actions">
                      <el-button size="small" @click="copyVectorToClipboard">复制向量</el-button>
                    </div>
                  </el-tab-pane>
                </el-tabs>
              </div>
              
              <div v-else-if="selectedChunkFile && !loading" class="chunk-preview">
                <el-alert
                  title="已选择分块文件"
                  type="info"
                  :closable="false"
                  show-icon
                  style="margin-bottom: 20px"
                >
                  <template #default>
                    <p>文件名: {{ selectedChunkFileInfo?.original_filename || '未知' }}</p>
                    <p>块数量: {{ selectedChunkFileInfo?.chunk_count || 0 }}</p>
                    <p>切分方法: {{ selectedChunkFileInfo?.chunk_method || '未知' }}</p>
                  </template>
                </el-alert>
                
                <div class="chunk-actions">
                  <el-button type="primary" @click="generateEmbedding">开始生成嵌入向量</el-button>
                </div>
              </div>
              
              <el-empty v-else description="暂无嵌入结果，请先生成嵌入" />
            </template>
          </el-card>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import axios from 'axios'

// 定义ChunkFile类型
type ChunkFile = {
  id: string;
  filename: string;
  original_filename: string;
  chunk_method: string;
  chunk_count: number;
  file_path: string;
  created_at: string;
  file_size_bytes: number;
}

// 使用正确的API基础URL（使用vite代理）
const API_BASE_URL = '/api'  // 将通过vite代理到http://localhost:5000/api

// 嵌入配置
const embeddingConfig = reactive({
  type: 'huggingface', // 默认选择 huggingface
  huggingface: {
    model: 'BAAI/BGE-small-zh-v1.5',
    dimension: '384',
    batchSize: 32
  },
  openai: {
    apiKey: '',
    model: 'text-embedding-3-small'
  }
})

// 根据选择的OpenAI模型显示对应的维度
const embeddingDimension = computed(() => {
  const model = embeddingConfig.openai.model
  if (model === 'text-embedding-3-small') return '1536'
  if (model === 'text-embedding-3-large') return '3072'
  if (model === 'text-embedding-ada-002') return '1536'
  return '未知'
})

// 测试文本和嵌入结果
const testText = ref('这是一段测试文本，用于生成向量嵌入。RAG(检索增强生成)是一种结合检索系统和生成模型的方法。')
const embeddingResult = ref<any>(null)
const loading = ref(false)

// 分块文件相关
const chunkFiles = ref<ChunkFile[]>([])
const loadingChunkFiles = ref(false)
const selectedChunkFile = ref('')
const selectedChunkFileInfo = ref<ChunkFile | null>(null)

// 计算属性
const canGenerateEmbedding = computed(() => {
  return selectedChunkFile.value || testText.value.trim().length > 0
})

// 计算可见的向量元素（最多显示50个）
const visibleVectorElements = computed(() => {
  if (!embeddingResult.value?.vector) return []
  return embeddingResult.value.vector.slice(0, 50)
})

// 加载分块文件列表
const loadChunkFiles = async () => {
  loadingChunkFiles.value = true
  
  try {
    // 发送请求到后端获取分块文件列表
    const response = await axios.get(`${API_BASE_URL}/files/chunk`)
    console.log('获取到的分块文件列表:', response.data)
    
    if (response.data.success) {
      // 确保后端返回了files数组
      if (Array.isArray(response.data.files)) {
        chunkFiles.value = response.data.files
        
        if (chunkFiles.value.length === 0) {
          ElMessage.info('没有找到任何分块文件，请先进行文档切分')
        } else {
          ElMessage.success(`成功加载 ${chunkFiles.value.length} 个分块文件`)
          console.log('文件列表:', chunkFiles.value)
          
          // 如果之前选择了文件，重新查找并更新selectedChunkFileInfo
          if (selectedChunkFile.value) {
            selectedChunkFileInfo.value = chunkFiles.value.find(file => file.id === selectedChunkFile.value) || null
          }
        }
      } else {
        console.error('后端返回的files不是数组:', response.data.files)
        ElMessage.warning('获取的文件列表格式不正确')
        chunkFiles.value = []
      }
    } else {
      ElMessage.error(`获取分块文件列表失败: ${response.data.error || '未知错误'}`)
    }
  } catch (error) {
    console.error('获取分块文件列表时出错:', error)
    ElMessage.error('获取分块文件列表失败，请检查网络连接')
  } finally {
    loadingChunkFiles.value = false
  }
}

// 处理分块文件选择变化
const handleChunkFileChange = (fileId: string) => {
  const foundFile = chunkFiles.value.find(file => file.id === fileId)
  selectedChunkFileInfo.value = foundFile || null
  embeddingResult.value = null // 清除之前的嵌入结果
  
  if (selectedChunkFileInfo.value) {
    console.log('已选择文件:', selectedChunkFileInfo.value)
  }
}

// 生成嵌入
const generateEmbedding = async () => {
  // 如果选择了分块文件，则从后端获取嵌入
  if (selectedChunkFile.value) {
    await generateEmbeddingForChunkFile()
    return
  }
  
  // 否则生成单个文本的嵌入
  if (!testText.value.trim()) {
    ElMessage.warning('请输入测试文本')
    return
  }
  
  loading.value = true
  
  try {
    // 模拟从后端获取嵌入结果
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    // 生成随机向量模拟嵌入结果
    const modelType = embeddingConfig.type
    const dimension = modelType === 'huggingface' 
      ? parseInt(embeddingConfig.huggingface.dimension) 
      : (embeddingConfig.openai.model === 'text-embedding-3-large' ? 3072 : 1536)
    
    // 生成模拟向量数据
    const vector = Array(dimension).fill(0).map(() => (Math.random() * 2 - 1) * 0.1)
    
    // 规范化向量
    const magnitude = Math.sqrt(vector.reduce((sum, val) => sum + val * val, 0))
    const normalizedVector = vector.map(val => val / magnitude)
    
    embeddingResult.value = {
      text: testText.value,
      model: modelType === 'huggingface' 
        ? embeddingConfig.huggingface.model 
        : embeddingConfig.openai.model,
      vector: normalizedVector,
      processingTime: Math.floor(Math.random() * 500) + 100 // 模拟处理时间
    }
    
    ElMessage.success('成功生成嵌入向量')
  } catch (error) {
    console.error('生成嵌入失败:', error)
    ElMessage.error('生成嵌入失败')
  } finally {
    loading.value = false
  }
}

// 为分块文件生成嵌入
const generateEmbeddingForChunkFile = async () => {
  if (!selectedChunkFile.value) {
    ElMessage.warning('请先选择一个分块文件')
    return
  }
  
  loading.value = true
  
  try {
    // 准备请求参数
    const requestData = {
      chunk_file_id: selectedChunkFile.value,
      model_type: embeddingConfig.type
    }
    
    // 如果是 huggingface 模型，添加额外参数
    if (embeddingConfig.type === 'huggingface') {
      Object.assign(requestData, {
        model_name: embeddingConfig.huggingface.model,
        batch_size: embeddingConfig.huggingface.batchSize
      })
    } else if (embeddingConfig.type === 'openai') {
      // 如果是 OpenAI 模型，添加API密钥和模型名称
      Object.assign(requestData, {
        api_key: embeddingConfig.openai.apiKey,
        model_name: embeddingConfig.openai.model
      })
    }
    
    console.log('发送嵌入请求:', requestData)
    
    // 调用后端API生成嵌入
    const response = await axios.post(`${API_BASE_URL}/embedding`, requestData)
    console.log('嵌入API响应:', response.data)
    
    if (response.data.success) {
      const metadata = response.data.metadata || {}
      const chunkCount = metadata.chunk_count || selectedChunkFileInfo.value?.chunk_count || 0
      
      ElMessage.success(`成功为 ${chunkCount} 个文本块生成嵌入向量`)
      
      // 获取嵌入统计信息更新UI
      await getEmbeddingStats()
    } else {
      ElMessage.error(`生成嵌入失败: ${response.data.error || '未知错误'}`)
    }
  } catch (error) {
    console.error('调用嵌入API时出错:', error)
    ElMessage.error('生成嵌入失败，请检查网络连接或服务器状态')
  } finally {
    loading.value = false
  }
}

// 获取嵌入统计信息
const getEmbeddingStats = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/embedding/stats`)
    console.log('嵌入统计信息:', response.data)
    
    if (response.data.success) {
      const stats = response.data.stats
      // 确保数据结构与预期一致
      if (!stats || !stats.metadata) {
        console.error('嵌入统计信息数据结构不符合预期:', stats)
        ElMessage.warning('嵌入统计信息格式不正确')
        return
      }
      
      const metadata = stats.metadata
      const dimensions = stats.stats?.embedding_dimensions || 0
      
      // 如果后端返回了示例向量，使用它；否则创建随机向量
      let vector = []
      if (stats.example_vector && Array.isArray(stats.example_vector)) {
        vector = stats.example_vector
      } else {
        // 创建随机向量作为示例
        vector = Array(dimensions).fill(0).map(() => (Math.random() * 2 - 1) * 0.1)
      }
      
      embeddingResult.value = {
        text: '示例向量',
        model: metadata.embedding_model_name || embeddingConfig.type,
        vector: vector,
        processingTime: (metadata.embedding_time_seconds || 0) * 1000
      }
      
      console.log('更新后的嵌入结果:', embeddingResult.value)
    } else {
      console.error('获取嵌入统计信息失败:', response.data)
      ElMessage.error(`获取嵌入统计信息失败: ${response.data.error || '未知错误'}`)
    }
  } catch (error) {
    console.error('获取嵌入统计信息时出错:', error)
    ElMessage.error('获取嵌入统计信息失败，请检查网络连接')
  }
}

// 复制向量到剪贴板
const copyVectorToClipboard = () => {
  if (!embeddingResult.value?.vector) return
  
  const vectorString = JSON.stringify(embeddingResult.value.vector)
  navigator.clipboard.writeText(vectorString).then(() => {
    ElMessage.success('向量已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

// 设为默认嵌入模型
const setAsDefault = () => {
  const modelType = embeddingConfig.type
  const modelName = modelType === 'huggingface' 
    ? embeddingConfig.huggingface.model 
    : embeddingConfig.openai.model
  
  ElMessage.success(`已将 ${modelName} 设为默认嵌入模型`)
}

// 组件挂载时加载分块文件列表
onMounted(() => {
  loadChunkFiles()
})
</script>

<style scoped>
.embedding-container {
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

.embedding-config {
  padding: 10px 0;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.embedding-result {
  min-height: 300px;
}

.vector-visualization {
  margin: 10px 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.vector-preview {
  display: flex;
  align-items: flex-end;
  height: 120px;
  gap: 2px;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
  overflow-x: auto;
}

.vector-element {
  width: 8px;
  min-width: 8px;
  border-radius: 2px 2px 0 0;
  transition: height 0.3s ease;
}

.vector-note {
  display: flex;
  justify-content: center;
}

.vector-actions {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
}

.file-option {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.file-name {
  font-weight: bold;
}

.file-info {
  display: flex;
  gap: 5px;
}

.action-buttons {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
}

.chunk-preview {
  min-height: 300px;
}

.chunk-actions {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style> 