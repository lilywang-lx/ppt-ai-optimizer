<template>
  <el-card class="slide-analysis-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <span class="header-icon">📄</span>
        <span class="header-title">每页详细分析</span>
        <el-button size="small" @click="toggleAll">
          {{ allExpanded ? '折叠全部' : '展开全部' }}
        </el-button>
      </div>
    </template>

    <el-collapse v-model="activeNames" accordion>
      <el-collapse-item
        v-for="(slide, index) in slides"
        :key="index"
        :name="index"
        :title="`第 ${slide.slide_index + 1} 页：${slide.slide_title || '无标题'}`"
      >
        <div class="slide-content">
          <!-- 主要内容点 -->
          <div class="content-section">
            <h5>📌 主要内容：</h5>
            <ul class="points-list">
              <li v-for="(point, idx) in slide.main_points" :key="idx">{{ point }}</li>
            </ul>
          </div>

          <!-- 评分 -->
          <div class="content-section">
            <h5>📊 质量评分：</h5>
            <el-row :gutter="20">
              <el-col :span="8">
                <div class="score-item">
                  <span class="score-label">清晰度</span>
                  <el-rate
                    v-model="slide.clarity"
                    :max="10"
                    disabled
                    :colors="rateColors"
                    show-score
                  />
                </div>
              </el-col>
              <el-col :span="8">
                <div class="score-item">
                  <span class="score-label">相关性</span>
                  <el-rate
                    v-model="slide.relevance"
                    :max="10"
                    disabled
                    :colors="rateColors"
                    show-score
                  />
                </div>
              </el-col>
              <el-col :span="8">
                <div class="score-item">
                  <span class="score-label">信息密度</span>
                  <el-tag :type="getDensityType(slide.information_density)">
                    {{ getDensityText(slide.information_density) }}
                  </el-tag>
                </div>
              </el-col>
            </el-row>
          </div>

          <!-- 问题识别 -->
          <div v-if="slide.issues && slide.issues.length > 0" class="content-section">
            <h5>⚠️ 识别的问题：</h5>
            <div class="issues-list">
              <div v-for="(issue, idx) in slide.issues" :key="idx" class="issue-item">
                <el-tag :type="getSeverityType(issue.severity)" size="small">
                  {{ getSeverityText(issue.severity) }}
                </el-tag>
                <span class="issue-type">{{ getIssueTypeText(issue.issue_type) }}</span>
                <span class="issue-desc">{{ issue.description }}</span>
                <span v-if="issue.location" class="issue-location">位置：{{ issue.location }}</span>
              </div>
            </div>
          </div>

          <!-- 优化方向 -->
          <div v-if="slide.optimization_directions && slide.optimization_directions.length > 0" class="content-section">
            <h5>💡 优化方向：</h5>
            <div class="directions-list">
              <el-tag
                v-for="(direction, idx) in slide.optimization_directions"
                :key="idx"
                type="success"
                effect="plain"
              >
                {{ direction }}
              </el-tag>
            </div>
          </div>
        </div>
      </el-collapse-item>
    </el-collapse>
  </el-card>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  slides: {
    type: Array,
    required: true
  }
})

const activeNames = ref([])
const allExpanded = ref(false)

const rateColors = ref(['#F56C6C', '#E6A23C', '#67C23A'])

// 切换展开/折叠
const toggleAll = () => {
  if (allExpanded.value) {
    activeNames.value = []
    allExpanded.value = false
  } else {
    activeNames.value = props.slides.map((_, idx) => idx)
    allExpanded.value = true
  }
}

// 获取信息密度类型
const getDensityType = (density) => {
  const typeMap = {
    'too_dense': 'danger',
    'appropriate': 'success',
    'too_sparse': 'warning'
  }
  return typeMap[density] || ''
}

// 获取信息密度文本
const getDensityText = (density) => {
  const textMap = {
    'too_dense': '过于密集',
    'appropriate': '适中',
    'too_sparse': '过于稀疏'
  }
  return textMap[density] || density
}

// 获取严重程度类型
const getSeverityType = (severity) => {
  const typeMap = {
    'critical': 'danger',
    'major': 'warning',
    'minor': 'info'
  }
  return typeMap[severity] || ''
}

// 获取严重程度文本
const getSeverityText = (severity) => {
  const textMap = {
    'critical': '严重',
    'major': '一般',
    'minor': '轻微'
  }
  return textMap[severity] || severity
}

// 获取问题类型文本
const getIssueTypeText = (type) => {
  const textMap = {
    'redundant': '冗余',
    'unclear': '不清晰',
    'missing': '缺失',
    'misplaced': '错位',
    'inconsistent': '不一致'
  }
  return textMap[type] || type
}
</script>

<style scoped>
.slide-analysis-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.header-icon {
  font-size: 24px;
  margin-right: 8px;
}

.header-title {
  font-size: 18px;
  font-weight: bold;
  flex: 1;
}

.slide-content {
  padding: 16px;
}

.content-section {
  margin-bottom: 20px;
}

.content-section:last-child {
  margin-bottom: 0;
}

.content-section h5 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.points-list {
  margin: 0;
  padding-left: 20px;
  color: #606266;
  line-height: 1.8;
}

.score-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.score-label {
  font-size: 13px;
  color: #909399;
}

.issues-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.issue-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #fef0f0;
  border-radius: 6px;
  flex-wrap: wrap;
}

.issue-type {
  font-weight: 600;
  color: #303133;
}

.issue-desc {
  flex: 1;
  color: #606266;
}

.issue-location {
  font-size: 12px;
  color: #909399;
}

.directions-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* 响应式 */
@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }

  .issue-item {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
