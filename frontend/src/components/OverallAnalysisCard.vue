<template>
  <el-card class="overall-analysis-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <span class="header-icon">📊</span>
        <span class="header-title">整体分析摘要</span>
      </div>
    </template>

    <div class="analysis-content">
      <!-- 核心要点 -->
      <div class="section">
        <h4 class="section-title">🎯 核心要点</h4>
        <ul class="key-points-list">
          <li v-for="(point, index) in analysis.key_points" :key="index" class="key-point-item">
            {{ point }}
          </li>
        </ul>
      </div>

      <!-- 主题和目标 -->
      <div class="section">
        <el-row :gutter="20">
          <el-col :span="8">
            <div class="info-item">
              <div class="info-label">主题</div>
              <div class="info-value">{{ analysis.theme }}</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="info-item">
              <div class="info-label">目标受众</div>
              <div class="info-value">{{ analysis.target_audience }}</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="info-item">
              <div class="info-label">演示目标</div>
              <div class="info-value">{{ analysis.presentation_goal }}</div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 质量评分 -->
      <div class="section">
        <h4 class="section-title">📈 质量评分</h4>
        <el-row :gutter="20">
          <el-col :span="8">
            <div class="score-item">
              <div class="score-label">内容连贯性</div>
              <el-progress
                :percentage="analysis.content_coherence * 10"
                :format="() => analysis.content_coherence.toFixed(1)"
                :color="getScoreColor(analysis.content_coherence)"
              />
            </div>
          </el-col>
          <el-col :span="8">
            <div class="score-item">
              <div class="score-label">逻辑流畅度</div>
              <el-progress
                :percentage="analysis.logic_flow * 10"
                :format="() => analysis.logic_flow.toFixed(1)"
                :color="getScoreColor(analysis.logic_flow)"
              />
            </div>
          </el-col>
          <el-col :span="8">
            <div class="score-item">
              <div class="score-label">内容完整性</div>
              <el-progress
                :percentage="analysis.completeness * 10"
                :format="() => analysis.completeness.toFixed(1)"
                :color="getScoreColor(analysis.completeness)"
              />
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 大纲结构 -->
      <div class="section">
        <h4 class="section-title">📑 大纲结构</h4>
        <div class="structure-info">
          <el-tag type="info" size="large">
            结构类型：{{ getStructureTypeText(analysis.outline_structure.structure_type) }}
          </el-tag>
          <el-tag :type="getQualityTagType(analysis.outline_structure.structure_quality)" size="large">
            结构质量：{{ getQualityText(analysis.outline_structure.structure_quality) }}
          </el-tag>
        </div>

        <!-- 章节列表 -->
        <div class="sections-list">
          <div
            v-for="(section, index) in analysis.outline_structure.sections"
            :key="index"
            class="section-item"
          >
            <div class="section-header">
              <span class="section-name">{{ index + 1 }}. {{ section.section_name }}</span>
              <el-tag v-if="section.is_necessary" type="success" size="small">必要</el-tag>
              <el-tag v-else type="warning" size="small">可选</el-tag>
            </div>
            <div class="section-details">
              <span class="section-slides">第 {{ section.slide_indices.join(', ') }} 页</span>
              <span class="section-purpose">目的：{{ section.purpose }}</span>
            </div>
            <div v-if="section.improvement_suggestion" class="section-suggestion">
              <el-alert type="warning" :closable="false" :title="`💡 ${section.improvement_suggestion}`" />
            </div>
          </div>
        </div>

        <!-- 结构问题 -->
        <div v-if="analysis.outline_structure.structure_issues.length > 0" class="structure-issues">
          <h5>⚠️ 结构问题：</h5>
          <ul>
            <li v-for="(issue, index) in analysis.outline_structure.structure_issues" :key="index">
              {{ issue }}
            </li>
          </ul>
        </div>
      </div>

      <!-- 整体建议 -->
      <div class="section">
        <h4 class="section-title">💡 整体优化建议</h4>
        <ul class="suggestions-list">
          <li v-for="(suggestion, index) in analysis.overall_suggestions" :key="index" class="suggestion-item">
            {{ suggestion }}
          </li>
        </ul>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  analysis: {
    type: Object,
    required: true
  }
})

// 获取评分颜色
const getScoreColor = (score) => {
  if (score >= 8) return '#67C23A'
  if (score >= 6) return '#E6A23C'
  return '#F56C6C'
}

// 获取结构类型文本
const getStructureTypeText = (type) => {
  const typeMap = {
    linear: '线性结构',
    parallel: '并列结构',
    circular: '循环结构',
    'problem-solution': '问题-解决方案结构'
  }
  return typeMap[type] || type
}

// 获取质量文本
const getQualityText = (quality) => {
  const qualityMap = {
    excellent: '优秀',
    good: '良好',
    fair: '尚可',
    poor: '较差'
  }
  return qualityMap[quality] || quality
}

// 获取质量标签类型
const getQualityTagType = (quality) => {
  const typeMap = {
    excellent: 'success',
    good: '',
    fair: 'warning',
    poor: 'danger'
  }
  return typeMap[quality] || ''
}
</script>

<style scoped>
.overall-analysis-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: bold;
}

.header-icon {
  font-size: 24px;
}

.analysis-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.section {
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.section-title {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.key-points-list {
  margin: 0;
  padding-left: 20px;
  list-style: disc;
}

.key-point-item {
  margin-bottom: 8px;
  line-height: 1.6;
  color: #606266;
}

.info-item {
  text-align: center;
  padding: 12px;
  background: white;
  border-radius: 6px;
}

.info-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.info-value {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.score-item {
  padding: 12px;
  background: white;
  border-radius: 6px;
}

.score-label {
  font-size: 13px;
  color: #606266;
  margin-bottom: 12px;
  text-align: center;
}

.structure-info {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.sections-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-item {
  padding: 16px;
  background: white;
  border-radius: 6px;
  border-left: 4px solid #409eff;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.section-name {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.section-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 13px;
  color: #606266;
}

.section-slides {
  color: #909399;
}

.section-suggestion {
  margin-top: 12px;
}

.structure-issues {
  margin-top: 16px;
  padding: 12px;
  background: #fef0f0;
  border-radius: 6px;
}

.structure-issues h5 {
  margin: 0 0 8px 0;
  color: #f56c6c;
  font-size: 14px;
}

.structure-issues ul {
  margin: 0;
  padding-left: 20px;
  color: #606266;
}

.structure-issues li {
  margin-bottom: 4px;
  line-height: 1.5;
}

.suggestions-list {
  margin: 0;
  padding-left: 20px;
  list-style: decimal;
}

.suggestion-item {
  margin-bottom: 12px;
  line-height: 1.6;
  color: #606266;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .structure-info {
    flex-direction: column;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
