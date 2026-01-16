<template>
  <div id="app">
    <el-container class="app-container">
      <el-header class="app-header">
        <h1><el-icon><Document /></el-icon> PPT智能优化系统</h1>
        <p>基于多模型协同的智能PPT优化平台</p>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { Document } from '@element-plus/icons-vue'
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.app-container {
  min-height: 100vh;
}

.app-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  text-align: center;
  padding: 30px 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.app-header h1 {
  font-size: 32px;
  color: #667eea;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.app-header p {
  color: #666;
  font-size: 14px;
}
</style>
