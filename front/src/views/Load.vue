<template>
  <div class="load-view-root">
    <!-- Left Column: Upload Controls -->
    <div class="control-panel-div">
      <h2>文件加载</h2>
      <el-form label-position="top">
        <el-form-item label="选择文件类型">
          <el-select v-model="selectedType" placeholder="请选择类型" style="width: 100%;">
            <el-option label="PDF" value="pdf"></el-option>
            <el-option label="Excel" value="xlsx"></el-option>
            <el-option label="Word" value="docx"></el-option>
            <el-option label="PowerPoint" value="pptx"></el-option>
            <el-option label="TXT" value="txt"></el-option>
            <el-option label="Markdown" value="md"></el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="选择文件">
          <el-upload
            ref="uploadRef"
            v-model:file-list="fileList"
            :auto-upload="false"
            :limit="1"
            :on-exceed="handleExceed"
            :on-change="handleChange"
            action="#"
            class="upload-demo"
          >
            <template #trigger>
              <el-button type="primary">选择文件</el-button>
            </template>
            <template #tip>
              <div class="el-upload__tip">
                请选择 {{ selectedType || '...' }} 类型的文件，仅限上传 1 个文件。
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item>
          <el-button type="success" @click="handleUpload" :disabled="!fileList.length || !selectedType || loading" :loading="loading">
            {{ loading ? '处理中...' : '上传并处理' }}
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- Right Column: Results Display -->
    <div class="result-panel-div">
      <h2>处理结果</h2>
      <!-- Wrapper div for result/loading/placeholder -->
      <div class="result-display-area">
        <el-skeleton :loading="loading" animated>
          <template #template>
            <div style="padding: 20px">
              <el-skeleton-item variant="p" style="height: 30px; width: 100%" />
              <div style="margin-top: 16px">
                <el-skeleton-item variant="text" style="width: 60%; margin-bottom: 10px" />
                <el-skeleton-item variant="text" style="width: 100%; margin-bottom: 10px" />
                <el-skeleton-item variant="text" style="width: 90%; margin-bottom: 10px" />
                <el-skeleton-item variant="text" style="width: 85%; margin-bottom: 10px" />
                <el-skeleton-item variant="text" style="width: 95%; margin-bottom: 10px" />
              </div>
            </div>
          </template>

          <template #default>
            <div v-if="processedData" class="result-content">
              <el-divider content-position="left">文件信息</el-divider>
              <div class="info-section">
                <p><strong>文件名:</strong> {{ processedData.original_filename }}</p>
                <p><strong>处理时间:</strong> {{ formatDate(processedData.timestamp) }}</p>
                <p><strong>原始文件路径:</strong> {{ processedData.upload_path }}</p>
                <p><strong>分析结果文件(JSON):</strong> {{ processedData.processed_file_path }}</p>
                <el-alert
                  title="文件处理说明"
                  type="info"
                  :closable="false"
                  style="margin-top: 10px"
                  description="系统会保存您上传的原始文件，并在文件名后添加时间戳。分析结果以JSON格式单独存储，包含提取的文本内容。"
                />
              </div>
              
              <el-divider content-position="left">内容预览</el-divider>
              <div class="preview-section">
                <el-alert
                  title="这是文件内容的前500个字符的预览"
                  type="info"
                  :closable="false"
                  style="margin-bottom: 10px"
                />
                <el-card shadow="never" class="content-preview">
                  <pre>{{ processedData.content_preview }}</pre>
                </el-card>
              </div>
            </div>
            <div v-else-if="errorMessage" class="error-message">
              <el-alert
                :title="errorMessage"
                type="error"
                show-icon
                :closable="false"
              />
            </div>
            <div v-else class="placeholder">
              <el-empty description="上传文件后，将在此处显示处理结果" />
            </div>
          </template>
        </el-skeleton>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { UploadInstance, UploadProps, UploadRawFile, UploadUserFile } from 'element-plus'
import { ElMessage, genFileId } from 'element-plus'

const selectedType = ref<string>('')
const fileList = ref<UploadUserFile[]>([])
const uploadResult = ref<any>(null)
const loading = ref<boolean>(false)
const uploadRef = ref<UploadInstance>()
const errorMessage = ref<string>('')

// 计算属性：解析上传结果
const processedData = computed(() => {
  if (!uploadResult.value) return null
  return typeof uploadResult.value === 'string' 
    ? null // 如果是字符串，说明是错误信息
    : uploadResult.value.data
})

// 格式化日期
const formatDate = (dateString: string) => {
  try {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }).format(date)
  } catch (e) {
    return dateString
  }
}

// 文件选择变化时的处理，清空旧结果
const handleChange: UploadProps['onChange'] = (uploadFile, uploadFiles) => {
  if (uploadFiles.length > 0) {
    fileList.value = [uploadFiles[uploadFiles.length - 1]] // 仅保留最后一个文件
  } else {
    fileList.value = []
  }
  uploadResult.value = null // 清空上次结果
  errorMessage.value = ''
  loading.value = false
}

// 处理文件超出限制
const handleExceed: UploadProps['onExceed'] = (files) => {
  uploadRef.value!.clearFiles()
  const file = files[0] as UploadRawFile
  file.uid = genFileId()
  uploadRef.value!.handleStart(file)
  uploadResult.value = null // 清空上次结果
  errorMessage.value = ''
  loading.value = false
}

// 处理上传按钮点击
const handleUpload = async () => {
  if (!selectedType.value) {
    ElMessage.warning('请选择文件类型')
    return
  }
  if (!fileList.value.length || !fileList.value[0].raw) {
    ElMessage.warning('请选择要上传的文件')
    return
  }

  loading.value = true
  uploadResult.value = null
  errorMessage.value = ''
  const file = fileList.value[0].raw

  // --- 发送请求到后端 --- 
  console.log('准备上传:', { type: selectedType.value, fileName: file.name });
  const formData = new FormData();
  formData.append('file', file);
  formData.append('type', selectedType.value);

  try {
    const response = await fetch('http://localhost:5000/api/upload', {
      method: 'POST',
      body: formData 
    });

    const data = await response.json();

    if (!response.ok) {
      // 处理 HTTP 错误 (例如 400, 500)
      throw new Error(data.error || `HTTP error! status: ${response.status}`);
    }

    // 显示成功消息和后端返回的结果
    uploadResult.value = data;
    ElMessage.success(data.message || '文件处理成功！');

  } catch (error) {
    console.error('上传或处理失败:', error);
    // 显示来自后端的错误或一个通用消息
    errorMessage.value = error instanceof Error ? error.message : '未知错误';
    ElMessage.error(`文件处理失败: ${errorMessage.value}`);
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* Root container for Load.vue */
.load-view-root {
  display: flex;
  flex-grow: 1; /* Grow to fill parent (.main-content) */
  min-height: 0; /* Prevent overflow issues in flex */
  width: 100%; /* Ensure it takes available width */
}

/* Left column div */
.control-panel-div {
  width: 300px;
  padding: 20px;
  border-right: 1px solid #eee;
  background-color: #fdfdfd;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: width 0.3s;
  overflow-y: auto; /* Allow scrolling if controls overflow */
}

.control-panel-div h2 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #303133;
}

.upload-demo .el-upload__tip {
  margin-top: 5px;
  font-size: 12px;
  color: #909399;
}

/* Right column div */
.result-panel-div {
  padding: 20px;
  display: flex;
  flex-direction: column;
  flex-grow: 1;
  overflow: hidden; /* Contains the scrolling area */
  min-width: 0; /* Prevent overflow issues in flex */
  width: 0; /* Add this line to help flex-grow */
}

.result-panel-div h2 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #303133;
  flex-shrink: 0;
}

/* Area for results/loading/placeholder */
.result-display-area {
  flex-grow: 1;
  overflow-y: auto;
  border: 1px solid #eee;
  background-color: #f9f9f9;
  border-radius: 4px;
  padding: 15px;
  display: flex;
  flex-direction: column;
}

.info-section, .preview-section {
  margin-bottom: 20px;
  text-align: left;
}

.info-section p {
  margin: 8px 0;
  color: #606266;
}

.content-preview {
  background-color: #f5f7fa;
}

.content-preview pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
  font-family: 'Courier New', Courier, monospace;
  font-size: 13px;
  line-height: 1.5;
  color: #303133;
}

.error-message {
  margin: 20px 0;
}

.placeholder {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  min-height: 200px;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .load-view-root {
    flex-direction: column;
  }

  .control-panel-div {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #eee;
    height: auto;
    flex-shrink: 1;
    overflow-y: visible; /* Let content determine height */
  }

  .result-panel-div {
    flex-grow: 1;
    padding-top: 10px;
    /* overflow: hidden; remains */
  }
}
</style> 