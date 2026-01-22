<template>
  <el-card class="change-report-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <span class="header-icon">📋</span>
        <span class="header-title">修改追踪报告</span>
        <div class="header-actions">
          <el-button size="small" @click="exportReport('json')">
            <el-icon><Download /></el-icon>
            导出JSON
          </el-button>
          <el-button size="small" @click="exportReport('markdown')">
            <el-icon><Document /></el-icon>
            导出Markdown
          </el-button>
        </div>
      </div>
    </template>

    <!-- 统计摘要 -->
    <div class="summary-section">
      <el-descriptions title="修改统计" :column="4" border>
        <el-descriptions-item label="总修改数">
          <el-tag type="primary" size="large">{{ report.total_changes }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="影响页面">
          <el-tag type="success" size="large">{{ report.slides_modified.length }} 页</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="生成时间">
          {{ formatDate(report.generation_timestamp) }}
        </el-descriptions-item>
        <el-descriptions-item label="文件ID">
          {{ report.ppt_id }}
        </el-descriptions-item>
      </el-descriptions>
    </div>

    <!-- 分类统计 -->
    <div class="charts-section">
      <el-row :gutter="20">
        <el-col :span="12">
          <div class="chart-item">
            <h4>按类型统计</h4>
            <div class="stat-bars">
              <div
                v-for="(count, type) in report.change_summary.by_type"
                :key="type"
                class="stat-bar"
              >
                <span class="stat-label">{{ getTypeText(type) }}</span>
                <el-progress
                  :percentage="(count / report.total_changes) * 100"
                  :format="() => count"
                />
              </div>
            </div>
          </div>
        </el-col>

        <el-col :span="12">
          <div class="chart-item">
            <h4>按来源统计</h4>
            <div class="stat-bars">
              <div
                v-for="(count, source) in report.change_summary.by_source"
                :key="source"
                class="stat-bar"
              >
                <span class="stat-label">{{ getSourceText(source) }}</span>
                <el-progress
                  :percentage="(count / report.total_changes) * 100"
                  :format="() => count"
                  :color="getSourceColor(source)"
                />
              </div>
            </div>
          </div>
        </el-col>
      </el-row>

      <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="12">
          <div class="chart-item">
            <h4>按维度统计</h4>
            <div class="stat-bars">
              <div
                v-for="(count, dimension) in report.change_summary.by_dimension"
                :key="dimension"
                class="stat-bar"
              >
                <span class="stat-label">{{ getDimensionText(dimension) }}</span>
                <el-progress
                  :percentage="(count / report.total_changes) * 100"
                  :format="() => count"
                />
              </div>
            </div>
          </div>
        </el-col>

        <el-col :span="12">
          <div class="chart-item">
            <h4>按影响程度统计</h4>
            <div class="stat-bars">
              <div
                v-for="(count, impact) in report.change_summary.by_impact"
                :key="impact"
                class="stat-bar"
              >
                <span class="stat-label">{{ getImpactText(impact) }}</span>
                <el-progress
                  :percentage="(count / report.total_changes) * 100"
                  :format="() => count"
                  :color="getImpactColor(impact)"
                />
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 详细修改记录 -->
    <div class="changes-section">
      <h3 class="section-title">详细修改记录</h3>

      <!-- 筛选 -->
      <div class="filters">
        <el-select v-model="filterSlide" placeholder="筛选页面" clearable size="small">
          <el-option
            v-for="slideIdx in report.slides_modified"
            :key="slideIdx"
            :label="`第 ${slideIdx + 1} 页`"
            :value="slideIdx"
          />
        </el-select>

        <el-select v-model="filterType" placeholder="筛选类型" clearable size="small">
          <el-option label="内容修改" value="content" />
          <el-option label="布局修改" value="layout" />
          <el-option label="样式修改" value="style" />
          <el-option label="结构修改" value="structure" />
        </el-select>

        <el-select v-model="filterSource" placeholder="筛选来源" clearable size="small">
          <el-option label="内容分析" value="content_analysis" />
          <el-option label="模型建议" value="model_suggestion" />
          <el-option label="用户请求" value="user_request" />
        </el-select>
      </div>

      <!-- 按页面分组的修改记录 -->
      <div class="changes-by-slide">
        <div
          v-for="(changes, slideIdx) in groupedChanges"
          :key="slideIdx"
          class="slide-changes"
        >
          <h4 class="slide-title">
            📄 第 {{ parseInt(slideIdx) + 1 }} 页
            <el-tag size="small">{{ changes.length }} 处修改</el-tag>
          </h4>

          <div class="change-list">
            <div
              v-for="(change, idx) in changes"
              :key="change.change_id"
              class="change-item"
            >
              <div class="change-header">
                <span class="change-number">{{ idx + 1 }}.</span>
                <el-tag :type="getTypeTagType(change.change_type)" size="small">
                  {{ getTypeText(change.change_type) }}
                </el-tag>
                <el-tag type="info" size="small">{{ getDimensionText(change.dimension) }}</el-tag>
                <el-tag size="small">{{ getElementText(change.element) }}</el-tag>
                <el-tag :type="getImpactTagType(change.impact_level)" size="small">
                  {{ getImpactText(change.impact_level) }}
                </el-tag>
                <el-tag :type="getSourceTagType(change.source)" size="small">
                  {{ getSourceText(change.source) }}
                </el-tag>
              </div>

              <div class="change-content">
                <div class="change-row">
                  <span class="change-label">修改前：</span>
                  <span class="change-value before-value">{{ change.before }}</span>
                </div>
                <div class="change-arrow">↓</div>
                <div class="change-row">
                  <span class="change-label">修改后：</span>
                  <span class="change-value after-value">{{ change.after }}</span>
                </div>
                <div class="change-row reason-row">
                  <span class="change-label">理由：</span>
                  <span class="change-value">{{ change.reason }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <el-empty v-if="Object.keys(groupedChanges).length === 0" description="没有符合条件的修改记录" />
    </div>
  </el-card>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Download, Document } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  report: {
    type: Object,
    required: true
  }
})

// 筛选条件
const filterSlide = ref(null)
const filterType = ref(null)
const filterSource = ref(null)

// 筛选后的修改记录（按页面分组）
const groupedChanges = computed(() => {
  let filtered = props.report.changes

  if (filterSlide.value !== null) {
    filtered = filtered.filter(c => c.slide_index === filterSlide.value)
  }
  if (filterType.value) {
    filtered = filtered.filter(c => c.change_type === filterType.value)
  }
  if (filterSource.value) {
    filtered = filtered.filter(c => c.source === filterSource.value)
  }

  // 按页面分组
  const grouped = {}
  filtered.forEach(change => {
    const key = change.slide_index
    if (!grouped[key]) {
      grouped[key] = []
    }
    grouped[key].push(change)
  })

  return grouped
})

// 格式化日期
const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

// 导出报告
const exportReport = (format) => {
  if (format === 'json') {
    const json = JSON.stringify(props.report, null, 2)
    const blob = new Blob([json], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `change-report-${props.report.ppt_id}.json`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('JSON报告已下载')
  } else if (format === 'markdown') {
    // 生成Markdown格式
    let md = `# PPT修改追踪报告\n\n`
    md += `**文件ID**: ${props.report.ppt_id}\n`
    md += `**生成时间**: ${formatDate(props.report.generation_timestamp)}\n`
    md += `**总修改数**: ${props.report.total_changes}\n`
    md += `**影响页面**: ${props.report.slides_modified.length}页\n\n`

    md += `## 修改统计\n\n`
    md += `### 按类型\n\n`
    Object.entries(props.report.change_summary.by_type).forEach(([type, count]) => {
      md += `- ${getTypeText(type)}: ${count}\n`
    })

    md += `\n### 按来源\n\n`
    Object.entries(props.report.change_summary.by_source).forEach(([source, count]) => {
      md += `- ${getSourceText(source)}: ${count}\n`
    })

    md += `\n## 详细修改记录\n\n`
    Object.entries(groupedChanges.value).forEach(([slideIdx, changes]) => {
      md += `### 第 ${parseInt(slideIdx) + 1} 页\n\n`
      changes.forEach((change, idx) => {
        md += `${idx + 1}. **${getTypeText(change.change_type)}** (${getDimensionText(change.dimension)})\n`
        md += `   - 修改前: ${change.before}\n`
        md += `   - 修改后: ${change.after}\n`
        md += `   - 理由: ${change.reason}\n`
        md += `   - 影响: ${getImpactText(change.impact_level)}\n\n`
      })
    })

    const blob = new Blob([md], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `change-report-${props.report.ppt_id}.md`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('Markdown报告已下载')
  }
}

// 辅助函数
const getTypeText = (type) => {
  const map = {
    content: '内容修改',
    layout: '布局修改',
    style: '样式修改',
    structure: '结构修改'
  }
  return map[type] || type
}

const getSourceText = (source) => {
  const map = {
    content_analysis: '内容分析',
    model_suggestion: '模型建议',
    user_request: '用户请求'
  }
  return map[source] || source
}

const getDimensionText = (dimension) => {
  const map = {
    content: '内容',
    logic: '逻辑',
    layout: '布局',
    color: '配色',
    font: '字体',
    chart: '图表'
  }
  return map[dimension] || dimension
}

const getElementText = (element) => {
  const map = {
    title: '标题',
    body: '正文',
    image: '图片',
    chart: '图表',
    background: '背景',
    layout: '版式'
  }
  return map[element] || element
}

const getImpactText = (impact) => {
  const map = {
    major: '重大',
    moderate: '中等',
    minor: '轻微'
  }
  return map[impact] || impact
}

const getTypeTagType = (type) => {
  const map = {
    content: 'primary',
    layout: 'success',
    style: 'warning',
    structure: 'info'
  }
  return map[type] || ''
}

const getSourceTagType = (source) => {
  const map = {
    content_analysis: 'info',
    model_suggestion: 'primary',
    user_request: 'warning'
  }
  return map[source] || ''
}

const getImpactTagType = (impact) => {
  const map = {
    major: 'danger',
    moderate: 'warning',
    minor: 'success'
  }
  return map[impact] || ''
}

const getSourceColor = (source) => {
  const map = {
    content_analysis: '#909399',
    model_suggestion: '#409eff',
    user_request: '#e6a23c'
  }
  return map[source] || '#909399'
}

const getImpactColor = (impact) => {
  const map = {
    major: '#f56c6c',
    moderate: '#e6a23c',
    minor: '#67c23a'
  }
  return map[impact] || '#909399'
}
</script>

<style scoped>
.change-report-card {
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

.header-actions {
  display: flex;
  gap: 8px;
}

.summary-section {
  margin-bottom: 24px;
}

.charts-section {
  margin-bottom: 24px;
}

.chart-item {
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.chart-item h4 {
  margin: 0 0 16px 0;
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.stat-bars {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stat-bar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-label {
  min-width: 80px;
  font-size: 13px;
  color: #606266;
}

.changes-section {
  margin-top: 24px;
}

.section-title {
  margin: 0 0 20px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.filters {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.changes-by-slide {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.slide-changes {
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.slide-title {
  margin: 0 0 16px 0;
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 12px;
}

.change-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.change-item {
  padding: 16px;
  background: white;
  border-radius: 6px;
  border-left: 4px solid #409eff;
}

.change-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.change-number {
  font-weight: 600;
  color: #303133;
  margin-right: 4px;
}

.change-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.change-row {
  display: flex;
  gap: 8px;
  font-size: 14px;
  line-height: 1.6;
}

.change-label {
  color: #909399;
  min-width: 60px;
  flex-shrink: 0;
}

.change-value {
  color: #606266;
  flex: 1;
}

.before-value {
  color: #f56c6c;
  text-decoration: line-through;
}

.after-value {
  color: #67c23a;
  font-weight: 500;
}

.change-arrow {
  text-align: center;
  color: #409eff;
  font-size: 16px;
}

.reason-row {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #dcdfe6;
}

/* 响应式 */
@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }

  .filters {
    flex-direction: column;
  }

  .change-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .change-row {
    flex-direction: column;
    gap: 4px;
  }
}
</style>
