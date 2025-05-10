<template>
  <div class="vector-store-container">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>向量存储管理</span>
        </div>
      </template>
      
      <el-row :gutter="20">
        <!-- 左侧：向量文件选择与存储配置 -->
        <el-col :span="8">
          <el-card class="inner-card">
            <template #header>
              <div class="inner-card-header">
                <span>向量文件与存储配置</span>
              </div>
            </template>
            
            <div class="storage-config">
              <el-form label-position="top" :model="storageOptions">
                <el-form-item label="1. 选择已生成的向量文件">
                  <el-select 
                    v-model="selectedVectorFile" 
                    placeholder="选择一个向量文件" 
                    style="width: 100%"
                    filterable
                    @change="handleFileSelectionChange"
                    :loading="loadingAvailableFiles"
                  >
                    <el-option
                      v-for="file in availableVectorFiles"
                      :key="file.vector_file_name"
                      :label="file.original_file_id || file.vector_file_name"
                      :value="file.vector_file_name"
                    />
                  </el-select>
                </el-form-item>

                <div v-if="selectedVectorFileDetails" class="file-details">
                  <p><strong>模型:</strong> {{ selectedVectorFileDetails.model_name }} ({{ selectedVectorFileDetails.model_dim }}d)</p>
                  <p><strong>块数:</strong> {{ selectedVectorFileDetails.processed_chunks }} / {{ selectedVectorFileDetails.total_chunks }}</p>
                </div>
                
                <el-form-item label="2. 选择向量存储目标">
                  <el-radio-group v-model="storageOptions.type">
                    <el-radio label="milvus">Milvus</el-radio>
                    <el-radio label="chroma">Chroma</el-radio>
                  </el-radio-group>
                </el-form-item>

                <el-form-item label="3. 集合名称 (Collection Name)">
                  <el-input 
                    v-model="storageOptions.collectionName" 
                    placeholder="例如: my_document_vectors"
                  ></el-input>
                </el-form-item>
                
                <el-form-item>
                  <el-button 
                    type="primary" 
                    @click="loadSelectedFileData" 
                    :disabled="!selectedVectorFile"
                    :loading="loadingVectorFileData"
                  >
                    预览数据块
                  </el-button>
                  <el-button 
                    type="success"
                    @click="handleStoreVectors"
                    :disabled="!selectedVectorFile || !storageOptions.collectionName"
                    :loading="storingVectors"
                  >
                    存储至 {{ storageOptions.type === 'milvus' ? 'Milvus' : 'Chroma' }}
                  </el-button>
                </el-form-item>
              </el-form>
            </div>
          </el-card>
        </el-col>
        
        <!-- 右侧：向量数据块预览 -->
        <el-col :span="16">
          <el-card class="inner-card">
            <template #header>
              <div class="inner-card-header">
                <span>数据块预览 (来自: {{ selectedVectorFileDetails?.original_file_id || selectedVectorFile || '未选择文件' }})</span>
                <el-tag v-if="vectorData.length > 0" type="info">
                  共 {{ vectorData.length }} 个数据块
                </el-tag>
              </div>
            </template>
            
            <div v-if="loadingVectorFileData" class="loading-container">
              <el-skeleton :rows="6" animated />
            </div>
             <div v-else-if="!loadingVectorFileData && vectorData.length === 0 && selectedVectorFile" class="loading-container">
              <el-empty description="选中文件无数据块或未加载" />
            </div>
             <div v-else-if="!selectedVectorFile" class="loading-container">
              <el-empty description="请先选择并加载向量文件" />
            </div>
            
            <div v-else class="vector-data">
              <el-table v-if="vectorData.length > 0" :data="vectorData" height="500" style="width: 100%">
                <el-table-column type="index" label="序号" width="70" />
                <el-table-column prop="content" label="文本内容">
                  <template #default="scope">
                    <el-tooltip
                      class="box-item"
                      effect="dark"
                      :content="scope.row.content"
                      placement="top-start"
                      :hide-after="0" 
                    >
                      <div class="truncated-text">{{ scope.row.content }}</div>
                    </el-tooltip>
                  </template>
                </el-table-column>
                <el-table-column label="来源文件" width="200">
                   <template #default="scope">
                    {{ scope.row.metadata?.source_document?.file_name || scope.row.metadata?.file_name || 'N/A' }}
                  </template>
                </el-table-column>
                 <el-table-column label="页码" width="80">
                   <template #default="scope">
                    {{ scope.row.metadata?.source_document?.page_number || scope.row.metadata?.page || 'N/A' }}
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="120">
                  <template #default="scope">
                    <el-button size="small" @click="showVectorDetails(scope.row)">详情</el-button>
                  </template>
                </el-table-column>
              </el-table>
              
              <el-empty v-if="vectorData.length === 0 && selectedVectorFile && !loadingVectorFileData" description="无数据块可展示" />
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
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'; // Import axios

const API_BASE_URL = 'http://localhost:5000/api';

// --- State for Available Vector Files ---
const availableVectorFiles = ref<any[]>([]);
const selectedVectorFile = ref<string | null>(null); // Stores the vector_file_name
const loadingAvailableFiles = ref(false);

const selectedVectorFileDetails = computed(() => {
  if (!selectedVectorFile.value) return null;
  return availableVectorFiles.value.find(file => file.vector_file_name === selectedVectorFile.value) || null;
});

// --- State for Storing Vectors ---
const storageOptions = reactive({
  type: 'milvus', // Default
  collectionName: '',
});
const storingVectors = ref(false);

// --- State for Vector Data from Selected File (Preview) ---
const vectorData = ref<any[]>([]) // Stores chunks from the selected file
const loadingVectorFileData = ref(false)

// --- Dialog State ---
const dialogVisible = ref(false)
const currentVector = ref<any>(null) // Stores the selected chunk for detail view

// --- Fetch Available Vector Files ---
const fetchAvailableVectorFiles = async () => {
  loadingAvailableFiles.value = true;
  try {
    const response = await axios.get(`${API_BASE_URL}/vector/stats`);
    if (response.data.success) {
      availableVectorFiles.value = response.data.files || [];
      if (availableVectorFiles.value.length > 0) {
        // ElMessage.success(`成功获取 ${availableVectorFiles.value.length} 个向量文件列表`);
      } else {
        ElMessage.info('未找到可用的向量文件，请先生成 Embedding 文件');
      }
    } else {
      ElMessage.error(response.data.error || '获取可用向量文件列表失败');
      availableVectorFiles.value = [];
    }
  } catch (error: any) {
    console.error('获取可用向量文件列表失败:', error);
    ElMessage.error(`获取可用向量文件列表失败: ${error.message}`);
    availableVectorFiles.value = [];
  } finally {
    loadingAvailableFiles.value = false;
  }
};

// --- Load Data for Selected File (for preview) ---
const loadSelectedFileData = async () => {
  if (!selectedVectorFile.value) {
    ElMessage.warning('请先选择一个向量文件进行预览');
    return;
  }
  loadingVectorFileData.value = true;
  vectorData.value = []; 
  
  try {
    const response = await axios.get(`${API_BASE_URL}/embedding/stats`, {
      params: { embedding_file_id: selectedVectorFile.value }
    });
    
    if (response.data.success && response.data.stats?.exists) {
      const fullData = response.data.stats.data;
      if (fullData && fullData.chunks && fullData.chunks.length > 0) {
        vectorData.value = fullData.chunks.map((chunk: any, index: number) => ({
          id: chunk.id || `chunk-${index}`, 
          ...chunk
        }));
        ElMessage.success(`成功加载 ${vectorData.value.length} 个数据块用于预览 from ${selectedVectorFileDetails.value?.original_file_id || selectedVectorFile.value}`);
      } else {
        ElMessage.info(`文件 ${selectedVectorFileDetails.value?.original_file_id || selectedVectorFile.value} 中没有数据块可供预览`);
        vectorData.value = [];
      }
    } else {
      ElMessage.error(response.data.error || response.data.message || `预览文件 ${selectedVectorFileDetails.value?.original_file_id || selectedVectorFile.value} 数据失败`);
      vectorData.value = [];
    }
  } catch (error: any) {
    console.error(`预览文件 ${selectedVectorFileDetails.value?.original_file_id || selectedVectorFile.value} 数据失败:`, error);
    ElMessage.error(`预览文件数据失败: ${error.message}`);
    vectorData.value = [];
  } finally {
    loadingVectorFileData.value = false;
  }
}

// --- Handle Storing Vectors ---
const handleStoreVectors = async () => {
  if (!selectedVectorFile.value) {
    ElMessage.warning('请先选择一个向量文件');
    return;
  }
  if (!storageOptions.collectionName.trim()) {
    ElMessage.warning('请输入集合名称 (Collection Name)');
    return;
  }

  storingVectors.value = true;
  try {
    const payload = {
      embedding_file_id: selectedVectorFile.value,
      vector_store_type: storageOptions.type,
      collection_name: storageOptions.collectionName.trim(),
      // Potentially add dimension if needed by backend, can get from selectedVectorFileDetails.value.model_dim
      dimension: selectedVectorFileDetails.value?.model_dim 
    };
    
    // Log payload for debugging
    console.log("Storing vectors with payload:", payload);

    const response = await axios.post(`${API_BASE_URL}/vector/store`, payload); // Assuming POST to /api/vector/store

    if (response.data.success) {
      ElMessage.success(response.data.message || '向量存储成功!');
      // Optionally, display more details from response.data.details
      if(response.data.details){
         ElMessageBox.alert(
          `<pre>${JSON.stringify(response.data.details, null, 2)}</pre>`, 
          '存储详情', 
          { dangerouslyUseHTMLString: true }
        );
      }
    } else {
      ElMessage.error(response.data.error || '向量存储失败');
    }
  } catch (error: any) {
    console.error('向量存储操作失败:', error);
    ElMessage.error(`向量存储操作失败: ${error.response?.data?.error || error.message}`);
  } finally {
    storingVectors.value = false;
  }
};

// --- Handle File Selection Change ---
const handleFileSelectionChange = (fileName: string) => {
  selectedVectorFile.value = fileName;
  vectorData.value = []; // Clear previous table data on new file selection
  if (availableVectorFiles.value.length > 0 && fileName) {
    const foundFile = availableVectorFiles.value.find(f => f.vector_file_name === fileName);
    if (foundFile && !storageOptions.collectionName) { // Auto-fill collection name if empty
        storageOptions.collectionName = foundFile.original_file_id || '';
    }
  }
};

// --- Show Vector Details ---
const showVectorDetails = (chunk: any) => {
  currentVector.value = chunk; // chunk is an item from vectorData
  dialogVisible.value = true;
}

// --- Lifecycle Hooks ---
onMounted(() => {
  fetchAvailableVectorFiles();
});

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

.file-details {
  margin-top: 5px; /* Reduced margin-top */
  margin-bottom: 15px; /* Added margin-bottom */
  padding: 8px; /* Slightly reduced padding */
  background-color: #f9f9f9;
  border: 1px solid #eee;
  border-radius: 4px;
  font-size: 0.85em; /* Slightly reduced font-size */
}
.file-details p {
  margin: 4px 0; /* Reduced margin */
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
  /* max-width: 300px; Consider adjusting based on your layout */
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

/* Ensure buttons in the same form item are spaced a bit */
.el-form-item .el-button + .el-button {
  margin-left: 10px;
}
</style> 