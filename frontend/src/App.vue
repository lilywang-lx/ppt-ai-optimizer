<template>
  <div id="app">
    <!-- 入口页面：全屏显示 -->
    <router-view v-if="isPortal" />

    <!-- PPT系统页面：带header -->
    <el-container v-else class="app-container">
      <el-header class="app-header">
        <div class="header-left">
          <el-button text @click="goBack" class="back-btn">
            <el-icon><ArrowLeft /></el-icon> 返回
          </el-button>
        </div>
        <div class="header-center">
          <h1><el-icon><Document /></el-icon> PPT智能优化系统</h1>
          <p>基于多模型协同的智能PPT优化平台</p>
        </div>
        <div class="header-right"></div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Document, ArrowLeft } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const isPortal = computed(() => route.meta?.isPortal === true)

const goBack = () => {
  router.push('/')
}
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
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  height: auto !important;
}

.header-left, .header-right {
  width: 100px;
}

.header-center {
  flex: 1;
  text-align: center;
}

.back-btn {
  font-size: 14px;
  color: #667eea;
}

.back-btn:hover {
  color: #764ba2;
}

.app-header h1 {
  font-size: 28px;
  color: #667eea;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.app-header p {
  color: #666;
  font-size: 13px;
}
</style>
