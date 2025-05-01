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
                  :title="`嵌入统计信息 (${embeddingResult.originalFilename || '未知文件'})`" 
                  type="success"
                  :closable="false"
                  show-icon
                  style="margin-bottom: 20px"
                >
                  <template #default>
                    <p><strong>模型:</strong> {{ embeddingResult.model }}</p>
                    <p><strong>向量维度:</strong> {{ embeddingResult.dimensions }}</p>
                    <p><strong>块数量:</strong> {{ embeddingResult.processedChunkCount }} / {{ embeddingResult.chunkCount }} (已处理/总计)</p>
                    <p><strong>文件大小:</strong> {{ Math.round(embeddingResult.fileSize / 1024) }} KB</p>
                    <p><strong>处理用时:</strong> {{ embeddingResult.processingTime }} ms</p>
                    <p><strong>文件路径:</strong> {{ embeddingResult.filePath }}</p>
                  </template>
                </el-alert>

                <el-tabs type="border-card">
                  <el-tab-pane label="示例块内容与向量">
                    <el-row :gutter="20">
                      <el-col :span="12">
                        <h4>示例块内容 (第一个成功嵌入的块):</h4>
                        <el-input
                          type="textarea"
                          :rows="8"
                          :value="embeddingResult.text" 
                          readonly
                        ></el-input>
                      </el-col>
                      <el-col :span="12">
                        <h4>向量可视化 (前 {{ visibleVectorElements.length }} 维):</h4>
                         <div class="vector-visualization">
                           <div class="vector-preview">
                             <div 
                               v-for="(value, index) in visibleVectorElements" 
                               :key="index"
                               class="vector-element"
                               :style="{ height: `${Math.abs(value * 100)}px`, backgroundColor: value >= 0 ? '#67C23A' : '#F56C6C' }"
                               :title="`维度 ${index}: ${value.toFixed(4)}`" 
                             ></div>
                           </div>
                         </div>
                      </el-col>
                    </el-row>
                  </el-tab-pane>
                  <el-tab-pane label="原始向量数据 (示例块)">
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
                  <el-tab-pane label="所有文本块" name="all-chunks">
                    <div v-if="embeddingResult.fullData?.chunks && embeddingResult.fullData.chunks.length > 0" class="all-chunks-container">
                       <el-scrollbar height="400px">
                         <el-card v-for="(chunk, index) in embeddingResult.fullData.chunks" :key="index" shadow="never" class="chunk-card">
                           <template #header>
                             <div class="chunk-header">
                               <span>文本块 {{ index + 1 }} / {{ embeddingResult.fullData.chunks.length }}</span>
                               <el-tag v-if="chunk.embedding && chunk.embedding.length > 0" type="success" size="small">
                                 向量已生成 (维度: {{ chunk.embedding.length }})
                               </el-tag>
                               <el-tag v-else-if="chunk.embedding_error" type="danger" size="small">
                                 嵌入失败
                               </el-tag>
                               <el-tag v-else type="info" size="small">
                                 无向量
                               </el-tag>
                             </div>
                           </template>
                           <div>
                             <p><strong>内容:</strong></p>
                             <el-input
                               type="textarea"
                               :rows="4"
                               :value="chunk.content"
                               readonly
                               class="chunk-content-display"
                             ></el-input>
                             <div v-if="chunk.embedding_error" class="error-message">
                               <strong>错误信息:</strong> {{ chunk.embedding_error }}
                             </div>
                             <div v-if="chunk.embedding && chunk.embedding.length > 0" class="vector-actions-small">
                               <el-popover placement="right" :width="400" trigger="click">
                                 <template #reference>
                                   <el-button size="small">查看向量</el-button>
                                 </template>
                                 <el-input
                                     type="textarea"
                                     :rows="10"
                                     :value="JSON.stringify(chunk.embedding, null, 2)"
                                     readonly
                                   ></el-input>
                               </el-popover>
                             </div>
                           </div>
                         </el-card>
                       </el-scrollbar>
                     </div>
                     <el-empty v-else description="未找到文本块数据" />
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
                  <el-button type="primary" @click="generateEmbeddingForChunkFile" :loading="loading">开始生成嵌入向量</el-button>
                </div>
              </div>
              
              <el-empty v-else description="请先选择一个已分块文件，或输入测试文本，然后生成嵌入" />
            </template>
          </el-card>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import type { AxiosResponse } from 'axios'
import { ElMessage, ElMessageBox, ElCard, ElScrollbar, ElPopover, ElTag } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import axios from 'axios'
// Use 'import type' for type-only imports
// No need for AxiosResponse import if only using response.data and typing it via generics

// --- Type Definitions ---
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

// Type for the individual chunk within the embedded data
type EmbeddedChunk = {
  content: string;
  metadata?: Record<string, any>; // Optional metadata from chunking
  embedding?: number[]; // Embedding vector (might be null if failed)
  embedding_error?: string; // Error message if embedding failed
}

// Type for the top-level metadata in the embedded data
type EmbeddingMetadata = {
  chunk_file_id: string;
  embedding_model_type: string;
  embedding_model_name: string;
  processed_chunk_count: number;
  total_chunk_count: number;
  embedding_time_seconds: number;
  embedding_timestamp: string;
  // Include potential original chunking metadata keys if known
  "文件名称"?: string; // Example from backend metadata
  original_filename?: string;
  [key: string]: any; // Allow other top-level metadata fields
}

// Type for the full data structure within the EmbeddingApiResponse and EmbeddingStatsApiResponse
// This represents the structure of the embedded JSON file content
type EmbeddedFileData = {
  chunks: EmbeddedChunk[];
  embedding_metadata: EmbeddingMetadata;
  // Include known original metadata keys and allow others
  "文件名称"?: string;
  original_filename?: string;
  [key: string]: any;
}

// Type for the successful response from /api/files/chunk
type ChunkFilesApiResponse = {
  success: true;
  files: ChunkFile[];
} | {
  success: false;
  error: string;
}

// Type for the successful response from /api/embedding (POST)
type EmbeddingApiResponse = {
  success: true;
  message: string;
  embedding_file: string;
  data: EmbeddedFileData; // Use the refined type here
} | {
  success: false;
  error: string;
}

// Type for the successful response from /api/embedding/stats (GET)
type EmbeddingStatsApiResponse = {
  success: true;
  filepath: string;
  data: EmbeddedFileData; // Use the refined type here
  stats: {
    total_chunk_count: number;
    processed_chunk_count: number;
    embedding_dimensions: number;
    file_size_bytes: number;
    created_at: string; // ISO timestamp string
    model_used: string;
  };
  example_chunk_content: string; // Content of the first successfully embedded chunk
  example_vector: number[]; // Vector of the first successfully embedded chunk
} | {
  success: false;
  message?: string; // Optional message on failure
  error?: string;   // Optional error on failure
  exists?: boolean; // Indicator if file doesn't exist
}

// Type for the state stored in embeddingResult ref
type EmbeddingResultState = {
  text: string; // Example chunk content
  model: string;
  vector: number[]; // Example chunk vector
  processingTime: number; // Overall embedding time in ms
  chunkCount: number; // Total chunks
  processedChunkCount: number; // Successfully processed chunks
  dimensions: number;
  fileSize: number; // File size in bytes
  filePath: string;
  originalFilename: string;
  // Store the full data for potential future use (e.g., browsing all chunks)
  fullData?: EmbeddedFileData; 
} | null;


// --- Component Script ---

// Use correct API base URL (using vite proxy)
const API_BASE_URL = '/api'

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
const embeddingResult = ref<EmbeddingResultState>(null)
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
    // Make the request - explicitly type the expected response
    const response: AxiosResponse<ChunkFilesApiResponse> = await axios.get(`${API_BASE_URL}/files/chunk`)
    console.log('获取到的分块文件列表:', response.data)
    
    if (response.data.success) {
      // Type assertion is safe here due to the 'success' check
      const data = response.data as Extract<ChunkFilesApiResponse, { success: true }>
      
      if (Array.isArray(data.files)) {
        chunkFiles.value = data.files
        
        if (chunkFiles.value.length === 0) {
          ElMessage.info('没有找到任何分块文件，请先进行文档切分')
        } else {
          ElMessage.success(`成功加载 ${chunkFiles.value.length} 个分块文件`)
          console.log('文件列表:', chunkFiles.value)
          
          if (selectedChunkFile.value) {
            selectedChunkFileInfo.value = chunkFiles.value.find(file => file.id === selectedChunkFile.value) || null
          }
        }
      } else {
        // This case might indicate an unexpected backend issue if success is true but files aren't an array
        console.error('后端返回成功但files不是数组:', data.files)
        ElMessage.warning('获取的文件列表格式不正确')
        chunkFiles.value = []
      }
    } else {
      // Type assertion is safe here
      const errorData = response.data as Extract<ChunkFilesApiResponse, { success: false }>
      ElMessage.error(`获取分块文件列表失败: ${errorData.error || '未知错误'}`)
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
  if (!testText.value.trim()) {
    ElMessage.warning('请输入测试文本')
    return
  }
  
  loading.value = true
  embeddingResult.value = null // Clear previous result
  
  try {
    await new Promise(resolve => setTimeout(resolve, 1500)) // Simulate network delay
    
    const modelType = embeddingConfig.type
    const dimension = modelType === 'huggingface' 
      ? parseInt(embeddingConfig.huggingface.dimension) 
      : (embeddingConfig.openai.model === 'text-embedding-3-large' ? 3072 : 1536)
    
    const vector = Array(dimension).fill(0).map(() => (Math.random() * 2 - 1) * 0.1)
    const magnitude = Math.sqrt(vector.reduce((sum, val) => sum + val * val, 0))
    const normalizedVector = magnitude > 0 ? vector.map(val => val / magnitude) : vector
    
    // Populate all required fields for EmbeddingResultState
    embeddingResult.value = {
      text: testText.value,
      model: modelType === 'huggingface' 
        ? embeddingConfig.huggingface.model 
        : embeddingConfig.openai.model,
      vector: normalizedVector,
      processingTime: Math.floor(Math.random() * 500) + 100,
      // Add dummy values for other required fields for the test text case
      chunkCount: 1, 
      processedChunkCount: 1,
      dimensions: dimension,
      fileSize: testText.value.length, // Use text length as dummy size
      filePath: "(测试文本)",
      originalFilename: "(测试文本)",
      fullData: undefined // No full data for test text
    }
    
    ElMessage.success('成功生成测试嵌入向量')
  } catch (error) {
    console.error('生成测试嵌入失败:', error)
    ElMessage.error('生成测试嵌入失败')
    embeddingResult.value = null // Clear on error
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
  embeddingResult.value = null // Clear previous result
  
  try {
    const requestData = {
      chunkFileId: selectedChunkFile.value,
      modelType: embeddingConfig.type
    }

    console.log('发送嵌入请求:', requestData)
    
    // Call backend API, explicitly type expected data structure using generics
    const response = await axios.post<EmbeddingApiResponse>(`${API_BASE_URL}/embedding`, requestData)
    // Log the raw backend response data
    console.log('POST /api/embedding Response Data:', response.data)
    
    // response.data is now correctly typed as EmbeddingApiResponse
    const responseData = response.data; 

    if (responseData.success) {
      // --- Success Path (Using direct response from POST /api/embedding) ---
      const fullData = responseData.data;
      const metadata = fullData.embedding_metadata;
      const chunks = fullData.chunks || [];
      
      const totalChunks = metadata.total_chunk_count || chunks.length;
      const processedChunks = metadata.processed_chunk_count || 0; // Use value from metadata
      const embeddingFile = responseData.embedding_file;
      const returnedChunkFileId = metadata.chunk_file_id || selectedChunkFile.value; // Prefer ID from metadata
      const originalFilename = metadata["文件名称"] || metadata.original_filename || fullData.original_filename || returnedChunkFileId;

      ElMessage.success(`成功为 ${processedChunks}/${totalChunks} 个文本块生成嵌入向量 (文件: ${embeddingFile})`)
      
      // --- Populate embeddingResult directly from the responseData ---
      // Fix: Explicitly type the parameter for .find()
      const firstSuccessfulChunk = chunks.find((chunk: EmbeddedChunk) => chunk.embedding && chunk.embedding.length > 0);
      const exampleContent = firstSuccessfulChunk?.content || (chunks.length > 0 ? chunks[0]?.content : '(无有效块内容)');
      const exampleVector = firstSuccessfulChunk?.embedding || [];
      const dimensions = exampleVector.length > 0 ? exampleVector.length : 0; // Calculate dimension from first vector
      const fileSize = 0; // File size is not directly available in this response, maybe fetch separately or ignore? Or get from stats later if needed.
      
      embeddingResult.value = {
        text: exampleContent || "(无示例内容)",
        model: metadata.embedding_model_name || metadata.embedding_model_type || "未知模型",
        vector: exampleVector,
        processingTime: (metadata.embedding_time_seconds || 0) * 1000,
        chunkCount: totalChunks,
        processedChunkCount: processedChunks,
        dimensions: dimensions,
        fileSize: fileSize, // Set to 0 or fetch separately if required
        filePath: embeddingFile, // Use the path returned by the API
        originalFilename: originalFilename,
        fullData: fullData // Store the full data
      }
      console.log('更新后的嵌入结果 (来自直接响应):', embeddingResult.value)
      
      // Optional: Call getEmbeddingStats if you need data only available there (like precise file size)
      // await getEmbeddingStats(returnedChunkFileId) // We can skip this now as we populate from the direct response

    } else {
      // responseData is narrowed to the error type
      ElMessage.error(`生成嵌入失败: ${responseData.error || '未知错误'}`)
      embeddingResult.value = null
    }
  } catch (error) {
    console.error('调用嵌入API时出错:', error)
    ElMessage.error('生成嵌入失败，请检查网络连接或服务器状态')
    embeddingResult.value = null // Clear on error
  } finally {
    loading.value = false
  }
}

// 获取嵌入统计信息
const getEmbeddingStats = async (embeddingFileId: string) => {
  if (!embeddingFileId) {
    console.error("getEmbeddingStats called without an embeddingFileId")
    ElMessage.error("无法获取统计信息：未提供文件ID")
    return;
  }
  
  embeddingResult.value = null;
  loading.value = true;

  try {
    // Call backend API, explicitly type expected data structure using generics
    const response = await axios.get<EmbeddingStatsApiResponse>(`${API_BASE_URL}/embedding/stats`, {
      params: { embedding_file_id: embeddingFileId }
    })
    // Log the raw backend response data
    console.log(`GET /api/embedding/stats Response Data for ${embeddingFileId}:`, response.data)

    // response.data is now correctly typed as EmbeddingStatsApiResponse
    const responseData = response.data;

    if (responseData.success) {
      // --- Success Path (Using response from GET /api/embedding/stats) --- 
      // Properties are correctly accessed here from the narrowed 'success' type
      const fullData = responseData.data;
      const metadata = fullData.embedding_metadata;
      const chunks = fullData.chunks || []; // Ensure chunks is an array
      const detailedStats = responseData.stats;
      // Use example_vector/content provided by the stats endpoint if available, otherwise find first successful
      const exampleVector = responseData.example_vector && responseData.example_vector.length > 0 
                            ? responseData.example_vector 
                            // Fix: Explicitly type the parameter for .find()
                            : (chunks.find((c: EmbeddedChunk) => c.embedding && c.embedding.length > 0)?.embedding || []);
      const exampleContent = responseData.example_chunk_content 
                             ? responseData.example_chunk_content 
                             // Fix: Explicitly type the parameter for .find()
                             : (chunks.find((c: EmbeddedChunk) => c.embedding && c.embedding.length > 0)?.content || (chunks.length > 0 ? chunks[0]?.content : '(无有效块内容)'));
      const dimensions = detailedStats.embedding_dimensions || exampleVector.length || 0; // Prefer stats dim, fallback to example
      const originalFilename = metadata["文件名称"] || metadata.original_filename || fullData.original_filename || embeddingFileId;

      embeddingResult.value = {
        text: exampleContent || "(无示例内容)",
        model: metadata.embedding_model_name || metadata.embedding_model_type || "未知模型",
        vector: exampleVector,
        processingTime: (metadata.embedding_time_seconds || 0) * 1000,
        chunkCount: detailedStats.total_chunk_count || 0,
        processedChunkCount: detailedStats.processed_chunk_count,
        dimensions: dimensions,
        fileSize: detailedStats.file_size_bytes || 0,
        filePath: responseData.filepath, // Access filepath directly from success response
        originalFilename: originalFilename,
        fullData: fullData
      }
      console.log('更新后的嵌入结果 (来自统计信息):', embeddingResult.value)
      
    } else {
      // --- Error Path --- 
      // responseData is narrowed to the error type ({success: false, message?, error?, exists?})
      console.error(`获取嵌入统计信息失败 for ${embeddingFileId}:`, responseData)
      // Access error/message properties which exist on the error type union member
      ElMessage.error(`获取嵌入统计信息失败: ${responseData.message || responseData.error || '未知错误'}`)
      embeddingResult.value = null
    }
  } catch (error) {
    console.error(`获取嵌入统计信息时出错 for ${embeddingFileId}:`, error)
    ElMessage.error('获取嵌入统计信息失败，请检查网络连接')
    embeddingResult.value = null
  } finally {
    loading.value = false;
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

.all-chunks-container {
  padding: 5px;
}

.chunk-card {
  margin-bottom: 15px;
  border: 1px solid #e4e7ed;
}

.chunk-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.9em;
}

.chunk-content-display {
  margin-top: 5px;
  margin-bottom: 10px;
}

.error-message {
  color: var(--el-color-danger);
  font-size: 0.85em;
  margin-top: 5px;
}

.vector-actions-small {
  margin-top: 10px;
  text-align: right;
}

.all-chunks-container .el-scrollbar__wrap {
  overflow-x: hidden;
}
</style> 