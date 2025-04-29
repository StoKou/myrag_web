<template>
  <div class="about-container">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>关于我 / 联系方式</span>
        </div>
      </template>
      <div class="contact-info">
        <p>您可以通过以下方式联系我或了解更多信息：</p>
        <el-row :gutter="20" justify="center" class="link-row">
          <el-col :span="6">
            <el-link type="primary" href="YOUR_GITHUB_LINK_HERE" target="_blank" :icon="LinkIcon">GitHub</el-link>
          </el-col>
          <el-col :span="6">
            <el-link type="primary" href="YOUR_ZHIHU_LINK_HERE" target="_blank" :icon="LinkIcon">知乎</el-link>
          </el-col>
          <!-- Add more links as needed -->
           <el-col :span="6">
             <el-link type="info" href="#" target="_blank" :icon="LinkIcon">其他平台</el-link>
           </el-col>
        </el-row>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
// Import ElLink icon if needed, using a generic Link icon for now
import { Link as LinkIcon } from '@element-plus/icons-vue' 
// No specific script logic needed for this simple page yet
</script>

<style scoped>
.about-container {
  display: flex;
  justify-content: center; /* Center the card horizontally */
  align-items: flex-start; /* Align card to the top */
  padding-top: 40px; /* Add some padding at the top */
  height: 100%; /* Ensure container takes full height */
  box-sizing: border-box;
}

.box-card {
  width: 600px; /* Set a max-width for the card */
  max-width: 90%;
}

.card-header {
  text-align: center;
  font-size: 1.2em;
  font-weight: bold;
}

.contact-info {
  text-align: center;
}

.contact-info p {
  margin-bottom: 25px;
  color: #606266;
}

.link-row .el-col {
  text-align: center; /* Center link within column */
}

.el-link {
  font-size: 1.1em;
}
</style> 