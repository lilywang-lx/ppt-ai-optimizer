<template>
  <div class="portal-container">
    <div class="portal-header">
      <h1>AI 工作平台</h1>
      <p>选择要进入的应用</p>
    </div>
    <div class="portal-cards">
      <div class="portal-card" @click="goToPPT">
        <div class="card-icon ppt-icon">
          <el-icon :size="48"><Document /></el-icon>
        </div>
        <h2>PPT智能优化系统</h2>
        <p>基于多模型协同的智能PPT优化平台，自动分析并优化演示文稿</p>
        <div class="card-tags">
          <el-tag size="small">AI优化</el-tag>
          <el-tag size="small" type="success">多模型</el-tag>
          <el-tag size="small" type="warning">PPT</el-tag>
        </div>
        <el-button type="primary" class="card-btn">进入系统</el-button>
      </div>

      <div class="portal-card" @click="goToPM">
        <div class="card-icon pm-icon">
          <el-icon :size="48"><Files /></el-icon>
        </div>
        <h2>AI产品经理工作台</h2>
        <p>一站式产品经理工作平台，覆盖需求梳理、UI设计、代码实现全流程</p>
        <div class="card-tags">
          <el-tag size="small">需求管理</el-tag>
          <el-tag size="small" type="success">PRD生成</el-tag>
          <el-tag size="small" type="warning">代码生成</el-tag>
        </div>
        <el-button type="primary" class="card-btn">进入系统</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Document, Files } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const goToPPT = () => {
  router.push('/ppt')
}

const goToPM = () => {
  window.location.href = '/AIplatform'
}
</script>

<style scoped>
.portal-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
}

.portal-header {
  text-align: center;
  margin-bottom: 50px;
}

.portal-header h1 {
  font-size: 42px;
  color: #fff;
  margin-bottom: 12px;
  text-shadow: 0 2px 10px rgba(0,0,0,0.2);
}

.portal-header p {
  color: rgba(255,255,255,0.85);
  font-size: 18px;
}

.portal-cards {
  display: flex;
  gap: 30px;
  flex-wrap: wrap;
  justify-content: center;
}

.portal-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 40px 30px;
  width: 340px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 10px 40px rgba(0,0,0,0.15);
}

.portal-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 60px rgba(0,0,0,0.25);
}

.card-icon {
  width: 90px;
  height: 90px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 24px;
}

.ppt-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.pm-icon {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  color: #fff;
}

.portal-card h2 {
  font-size: 22px;
  color: #333;
  margin-bottom: 12px;
}

.portal-card p {
  color: #666;
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 20px;
  min-height: 44px;
}

.card-tags {
  margin-bottom: 24px;
  display: flex;
  gap: 8px;
  justify-content: center;
  flex-wrap: wrap;
}

.card-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
}
</style>
