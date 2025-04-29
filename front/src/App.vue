<script setup lang="ts">
import { RouterView, useRoute } from 'vue-router'
import { House, Document, InfoFilled, ScaleToOriginal, DataAnalysis, Connection } from '@element-plus/icons-vue'

const route = useRoute()
</script>

<template>
  <el-container class="app-container">
    <el-aside width="200px" class="sidebar">
      <div class="logo">项目导航</div>
      <el-menu
        router
        :default-active="route.path"
        class="el-menu-vertical"
        background-color="#545c64"
        text-color="#fff"
        active-text-color="#ffd04b"
      >
        <el-menu-item index="/home">
          <el-icon><House /></el-icon>
          <span>首页</span>
        </el-menu-item>
        <el-menu-item index="/load">
          <el-icon><Document /></el-icon>
          <span>加载</span>
        </el-menu-item>
        <el-menu-item index="/chunk">
          <el-icon><ScaleToOriginal /></el-icon>
          <span>文档切分</span>
        </el-menu-item>
        <el-menu-item index="/embedding">
          <el-icon><Connection /></el-icon>
          <span>向量嵌入</span>
        </el-menu-item>
        <el-menu-item index="/vectorstore">
          <el-icon><DataAnalysis /></el-icon>
          <span>向量存储</span>
        </el-menu-item>
        <el-menu-item index="/about">
          <el-icon><InfoFilled /></el-icon>
          <span>关于</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-main class="main-content">
      <RouterView />
    </el-main>
  </el-container>
</template>

<style>
html, body, #app {
  margin: 0;
  padding: 0;
  height: 100%;
  width: 100%;
}

/* 全局样式优化 */
.el-card {
  --el-card-padding: 15px;
  overflow: visible;
}

.el-card__header {
  padding: 12px 15px;
}
</style>

<style scoped>
.app-container {
  height: 100vh;
  width: 100%;
  display: flex;
}

.sidebar {
  background-color: #545c64;
  height: 100%;
  box-shadow: 2px 0 6px rgba(0, 21, 41, 0.35);
  flex-shrink: 0;
}

.logo {
  height: 60px;
  line-height: 60px;
  text-align: center;
  font-size: 20px;
  font-weight: bold;
  color: white;
  background-color: #4a4f56;
}

.el-menu-vertical {
  border-right: none;
  height: calc(100% - 60px);
  overflow-y: auto;
}

.main-content {
  padding: 20px;
  flex-grow: 1;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}
</style>
