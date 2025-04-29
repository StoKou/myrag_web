<!-- chunkView.vue - 文档切分功能 -->
<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

// 切分方法选项
const chunkMethods = [
  {
    value: 'langchain',
    label: 'LangChain'
  },
  {
    value: 'llamaindex',
    label: 'LlamaIndex'
  },
  {
    value: 'custom',
    label: '自定义切分'
  }
]

// 表单数据
const formData = reactive({
  chunkMethod: 'langchain',
  chunkSize: 500,
  chunkOverlap: 50,
  separator: '\n\n',
})

// 已加载的文件列表
const loadedFiles = ref<Array<{id: string, name: string, path: string}>>([])
// 上传的文件列表
const fileList = ref([])
// 选中的文件
const selectedFile = ref('')
// 切分后的内容
const chunkResult = ref<Array<{id: number, content: string}>>([])
// 加载状态
const loading = ref(false)

// 上传配置
const uploadConfig = {
  action: '/api/upload',
  headers: {
    'Content-Type': 'multipart/form-data'
  }
}

// 上传成功处理
const handleUploadSuccess = (response: any) => {
  ElMessage.success('文件上传成功')
  // 添加到已加载列表并选中
  if (response && response.data) {
    const file = {
      id: response.data.id || Date.now().toString(),
      name: response.data.filename,
      path: response.data.path
    }
    loadedFiles.value.push(file)
    selectedFile.value = file.id
  }
}

// 上传失败处理
const handleUploadError = () => {
  ElMessage.error('文件上传失败')
}

// 获取已加载文件列表
const fetchLoadedFiles = async () => {
  try {
    loading.value = true
    // 调用后端API获取load文件夹下的文件列表
    const response = await fetch('/api/files/load')
    if (!response.ok) {
      throw new Error(`请求失败: ${response.status}`)
    }
    const data = await response.json()
    
    // 处理后端返回的数据
    if (data.success && Array.isArray(data.files)) {
      loadedFiles.value = data.files.map((file: any) => ({
        id: file.id || file.filename || Date.now().toString(),
        name: file.filename || file.name,
        path: file.path || `/files/load/${file.filename || file.name}`
      }))
    } else {
      ElMessage.warning('未获取到文件列表或格式不正确')
      loadedFiles.value = []
    }
  } catch (error) {
    console.error('获取文件列表失败', error)
    ElMessage.warning('使用本地模拟数据')
    
    // 在API调用失败时使用备用数据
    loadedFiles.value = [
      { id: '1', name: '黑悟空设定.txt', path: '/files/load/黑悟空设定.json' },
      { id: '2', name: '黑神话悟空.pdf', path: '/files/load/黑神话悟空.json' }
    ]
  } finally {
    loading.value = false
  }
}

// 执行文档切分
const processChunking = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择一个文件')
    return
  }
  
  loading.value = true
  
  try {
    // 调用后端API执行文档切分
    const response = await fetch('/api/chunk', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        fileId: selectedFile.value,
        method: formData.chunkMethod,
        chunkSize: formData.chunkSize,
        chunkOverlap: formData.chunkOverlap,
        separator: formData.separator
      })
    })
    
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`请求失败: ${response.status}, ${errorText}`)
    }
    
    const data = await response.json()
    
    if (data.success && data.chunks) {
      chunkResult.value = data.chunks
      ElMessage.success(`文档切分成功，共生成 ${data.chunk_count} 个切块`)
    } else {
      throw new Error(data.error || '切分处理失败，未返回切块数据')
    }
  } catch (error: any) {
    console.error('文档切分失败', error)
    ElMessage.error(`文档切分失败: ${error.message}`)
    
    // 如果API请求失败，使用模拟数据进行展示
    setTimeout(() => {
      chunkResult.value = Array.from({ length: 10 }, (_, i) => ({
        id: i + 1,
        content: `这是使用 ${formData.chunkMethod} 方法切分的第 ${i + 1} 个块，切分大小为 ${formData.chunkSize}，重叠大小为 ${formData.chunkOverlap}。这里是一些示例内容...`
      }))
      ElMessage.warning('使用模拟数据展示')
    }, 1000)
  } finally {
    loading.value = false
  }
}

// 复制切块内容
const copyChunkContent = (content: string) => {
  navigator.clipboard.writeText(content)
    .then(() => {
      ElMessage.success('已复制到剪贴板')
    })
    .catch(() => {
      ElMessage.error('复制失败')
    })
}

// 导出切块内容为文本文件
const exportChunkContent = (id: number, content: string) => {
  const blob = new Blob([content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `切块_${id}.txt`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  ElMessage.success('导出成功')
}

// 页面加载时获取文件列表
onMounted(() => {
  fetchLoadedFiles()
})
</script>

<template>
  <div class="chunk-view">
    <el-container class="main-container">
      <!-- 左侧控制面板 -->
      <el-aside width="400px" class="left-panel">
        <el-card class="control-panel">
          <template #header>
            <div class="card-header">
              <h3>文档切分配置</h3>
            </div>
          </template>
          
          <el-form label-position="top">
            <!-- 切分方法选择 -->
            <el-form-item label="切分方法">
              <el-radio-group v-model="formData.chunkMethod">
                <el-radio 
                  v-for="method in chunkMethods" 
                  :key="method.value" 
                  :label="method.value"
                >
                  {{ method.label }}
                </el-radio>
              </el-radio-group>
            </el-form-item>
            
            <!-- 切分参数配置 -->
            <el-form-item label="切分大小">
              <el-input-number v-model="formData.chunkSize" :min="100" :step="50" />
            </el-form-item>
            
            <el-form-item label="重叠大小">
              <el-input-number v-model="formData.chunkOverlap" :min="0" :max="formData.chunkSize" :step="10" />
            </el-form-item>
            
            <el-form-item label="分隔符" v-if="formData.chunkMethod === 'custom'">
              <el-input v-model="formData.separator" placeholder="请输入分隔符" />
            </el-form-item>
            
            <el-divider content-position="center">文件选择</el-divider>
            
            <!-- 文件上传 -->
            <el-form-item label="上传新文件">
              <el-upload
                v-model:file-list="fileList"
                :action="uploadConfig.action"
                :headers="uploadConfig.headers"
                :on-success="handleUploadSuccess"
                :on-error="handleUploadError"
                accept=".txt,.pdf,.docx,.md,.json"
                :limit="1"
              >
                <el-button type="primary">上传文件</el-button>
                <template #tip>
                  <div class="el-upload__tip">
                    支持 .txt、.pdf、.docx、.md 和 .json 格式
                  </div>
                </template>
              </el-upload>
            </el-form-item>
            
            <!-- 已加载文件选择 -->
            <el-form-item label="选择已加载文件">
              <el-select v-model="selectedFile" placeholder="请选择文件" style="width: 100%;">
                <el-option
                  v-for="file in loadedFiles"
                  :key="file.id"
                  :label="file.name"
                  :value="file.id"
                />
              </el-select>
            </el-form-item>
            
            <!-- 执行切分按钮 -->
            <el-form-item>
              <el-button 
                type="primary" 
                @click="processChunking" 
                :loading="loading"
                style="width: 100%;"
              >
                执行文档切分
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-aside>
      
      <!-- 右侧结果展示区域 -->
      <el-main class="right-panel">
        <el-card class="result-panel">
          <template #header>
            <div class="card-header">
              <h3>切分结果</h3>
              <span>共 {{ chunkResult.length }} 个切块</span>
            </div>
          </template>
          
          <div v-if="loading" class="loading-container">
            <el-skeleton :rows="10" animated />
          </div>
          
          <div v-else-if="chunkResult.length === 0" class="empty-result">
            <el-empty description="暂无切分结果，请选择文件并执行切分" />
          </div>
          
          <div v-else class="chunk-list">
            <el-collapse>
              <el-collapse-item
                v-for="chunk in chunkResult"
                :key="chunk.id"
                :title="`切块 #${chunk.id}`"
                :name="chunk.id"
              >
                <div class="chunk-content">
                  <pre>{{ chunk.content }}</pre>
                </div>
                <div class="chunk-actions">
                  <el-button size="small" type="primary" plain @click="copyChunkContent(chunk.content)">复制</el-button>
                  <el-button size="small" type="success" plain @click="exportChunkContent(chunk.id, chunk.content)">导出</el-button>
                </div>
              </el-collapse-item>
            </el-collapse>
          </div>
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<style scoped>
.chunk-view {
  height: 100%;
  padding: 20px;
}

.main-container {
  height: calc(100vh - 120px);
  border: 1px solid #ebeef5;
  border-radius: 4px;
  overflow: hidden;
}

.left-panel {
  border-right: 1px solid #ebeef5;
  background-color: #f9fafc;
}

.right-panel {
  padding: 20px;
  background-color: #ffffff;
  overflow-y: auto;
}

.control-panel, .result-panel {
  height: 100%;
  overflow-y: auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 18px;
}

.chunk-content {
  background-color: #f8f9fa;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 10px;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 300px;
  overflow-y: auto;
}

.chunk-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.loading-container, .empty-result {
  padding: 40px 0;
  display: flex;
  justify-content: center;
  align-items: center;
}

.empty-result {
  min-height: 300px;
}
</style> 