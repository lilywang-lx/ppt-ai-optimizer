<template>
  <div class="home-container">
    <el-card class="main-card" shadow="hover">
      <!-- 步骤指示器 -->
      <div class="steps-container">
        <el-steps :active="currentStepIndex" align-center finish-status="success">
          <el-step title="上传PPT" icon="Upload" />
          <el-step title="内容分析" icon="Search" />
          <el-step title="审查建议" icon="Edit" />
          <el-step title="执行优化" icon="Setting" />
          <el-step title="查看结果" icon="Check" />
        </el-steps>
      </div>

      <!-- Step 1: 上传区域 -->
      <div v-if="currentStep === 'upload'" class="upload-section">
        <el-upload
          ref="uploadRef"
          class="upload-demo"
          drag
          :auto-upload="false"
          :on-change="handleFileChange"
          :limit="1"
          accept=".pptx"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            拖拽PPT文件到此处或 <em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              仅支持 .pptx 格式，文件大小不超过 50MB
            </div>
          </template>
        </el-upload>

        <el-button
          type="primary"
          size="large"
          :loading="uploading"
          :disabled="!selectedFile"
          @click="handleUpload"
          class="upload-btn"
        >
          <el-icon><Upload /></el-icon>
          开始优化
        </el-button>
      </div>

      <!-- Step 2: 处理进度 -->
      <div v-if="currentStep === 'processing'" class="processing-section">
        <el-result icon="info" title="正在处理中">
          <template #sub-title>
            <div class="status-info">
              <p class="current-step">{{ progress.current_step }}</p>
              <p class="message">{{ progress.message }}</p>
            </div>
          </template>
          <template #extra>
            <el-progress
              :percentage="Math.round(progress.progress)"
              :status="progressStatus"
              :stroke-width="20"
            />
            <div class="status-tag">
              <el-tag :type="getStatusType(progress.status)">{{ getStatusText(progress.status) }}</el-tag>
            </div>
          </template>
        </el-result>
      </div>

      <!-- Step 3: 审查优化建议 ⭐ 新增 -->
      <div v-if="currentStep === 'review'" class="review-section">
        <div class="section-header">
          <h2>📋 审查AI分析结果</h2>
          <p class="section-subtitle">请审查以下分析结果和优化建议，您可以选择、编辑或跳过这些建议</p>
        </div>

        <!-- 整体分析卡片 -->
        <OverallAnalysisCard
          v-if="contentAnalysis?.overall_analysis"
          :analysis="contentAnalysis.overall_analysis"
        />

        <!-- 优化建议列表 -->
        <OptimizationOpportunityList
          v-if="editedOpportunities.length > 0"
          :opportunities="editedOpportunities"
          @update:opportunities="handleOpportunitiesUpdate"
        />

        <!-- 每页详细分析（可折叠） -->
        <SlideAnalysisList
          v-if="contentAnalysis?.slide_analyses"
          :slides="contentAnalysis.slide_analyses"
        />

        <!-- 优化偏好设置（可选） -->
        <el-card class="preferences-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="header-icon">⚙️</span>
              <span class="header-title">优化偏好设置（可选）</span>
            </div>
          </template>

          <el-form label-width="100px">
            <el-form-item label="演示风格">
              <el-radio-group v-model="userPreferences.style">
                <el-radio label="professional">专业商务</el-radio>
                <el-radio label="casual">轻松休闲</el-radio>
                <el-radio label="academic">学术严谨</el-radio>
                <el-radio label="creative">创意活泼</el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="配色方案">
              <el-select v-model="userPreferences.color_scheme" placeholder="选择配色方案">
                <el-option label="保持原有配色" value="keep" />
                <el-option label="商务蓝" value="business_blue" />
                <el-option label="活力橙" value="vibrant_orange" />
                <el-option label="简约灰" value="minimal_gray" />
                <el-option label="清新绿" value="fresh_green" />
              </el-select>
            </el-form-item>

            <el-form-item label="重点优化">
              <el-checkbox-group v-model="userPreferences.emphasis_areas">
                <el-checkbox label="content">内容质量</el-checkbox>
                <el-checkbox label="visual">视觉设计</el-checkbox>
                <el-checkbox label="logic">逻辑结构</el-checkbox>
                <el-checkbox label="animation">动画效果</el-checkbox>
              </el-checkbox-group>
            </el-form-item>

            <el-form-item label="约束条件">
              <el-checkbox-group v-model="userPreferences.constraints">
                <el-checkbox label="keep_structure">保持原有结构</el-checkbox>
                <el-checkbox label="limit_pages">限制页数</el-checkbox>
                <el-checkbox label="brand_colors">使用品牌色</el-checkbox>
              </el-checkbox-group>
            </el-form-item>

            <el-form-item label="额外说明">
              <el-input
                v-model="additionalInstructions"
                type="textarea"
                :rows="4"
                placeholder="请输入您的补充说明或特殊要求..."
              />
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 操作按钮 -->
        <div class="review-actions">
          <el-space size="large">
            <el-button size="large" @click="handleReset">
              <el-icon><Back /></el-icon>
              返回修改
            </el-button>
            <el-button size="large" @click="handleSkipReview" :loading="submitting">
              使用默认建议
            </el-button>
            <el-button type="primary" size="large" @click="handleSubmitEdits" :loading="submitting">
              应用选中的建议
              <el-icon><Right /></el-icon>
            </el-button>
          </el-space>
        </div>
      </div>

      <!-- Step 4: 执行优化中 -->
      <div v-if="currentStep === 'optimizing'" class="processing-section">
        <el-result icon="info" title="正在执行优化">
          <template #sub-title>
            <div class="status-info">
              <p class="current-step">{{ progress.current_step }}</p>
              <p class="message">{{ progress.message }}</p>
            </div>
          </template>
          <template #extra>
            <el-progress
              :percentage="Math.round(progress.progress)"
              :status="progressStatus"
              :stroke-width="20"
            />
            <div class="status-tag">
              <el-tag :type="getStatusType(progress.status)">{{ getStatusText(progress.status) }}</el-tag>
            </div>
          </template>
        </el-result>
      </div>

      <!-- Step 5: 结果展示 -->
      <div v-if="currentStep === 'result'" class="result-section">
        <el-result icon="success" title="优化完成！🎉">
          <template #sub-title>
            PPT已成功优化，您可以查看详细结果或下载文件
          </template>
          <template #extra>
            <el-space direction="vertical" size="large" style="width: 100%">
              <!-- 优化统计 -->
              <el-descriptions :column="4" border v-if="changeReport">
                <el-descriptions-item label="总修改数">
                  <el-tag type="primary" size="large">{{ changeReport.total_changes }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="影响页面">
                  <el-tag type="success" size="large">{{ changeReport.slides_modified?.length || 0 }} 页</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="处理时间">
                  {{ formatDate(changeReport.generation_timestamp) }}
                </el-descriptions-item>
                <el-descriptions-item label="文件大小">
                  {{ result?.file_size || '未知' }}
                </el-descriptions-item>
              </el-descriptions>

              <!-- 标签页 -->
              <el-tabs v-model="activeTab" type="border-card">
                <!-- 内容分析标签 -->
                <el-tab-pane label="📊 内容分析" name="analysis" v-if="result?.content_analysis">
                  <OverallAnalysisCard :analysis="result.content_analysis.overall_analysis" />
                  <div style="margin-top: 20px">
                    <SlideAnalysisList :slides="result.content_analysis.slide_analyses" />
                  </div>
                </el-tab-pane>

                <!-- 修改追踪标签 -->
                <el-tab-pane label="📋 修改追踪" name="changes" v-if="changeReport">
                  <ChangeReportDisplay :report="changeReport" />
                </el-tab-pane>

                <!-- 模型建议标签（兼容旧版） -->
                <el-tab-pane
                  v-for="(suggestion, index) in result?.model_suggestions"
                  :key="index"
                  :label="`${suggestion.model_name}`"
                  :name="`model-${index}`"
                >
                  <el-table :data="suggestion.optimization_suggestions" style="width: 100%" max-height="400">
                    <el-table-column prop="slide_index" label="页码" width="80" />
                    <el-table-column prop="optimization_dimension" label="维度" width="100">
                      <template #default="scope">
                        <el-tag size="small">{{ scope.row.optimization_dimension }}</el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column prop="suggestion" label="优化建议" show-overflow-tooltip />
                    <el-table-column prop="priority" label="优先级" width="100">
                      <template #default="scope">
                        <el-tag :type="getPriorityType(scope.row.priority)" size="small">
                          {{ scope.row.priority }}
                        </el-tag>
                      </template>
                    </el-table-column>
                  </el-table>
                </el-tab-pane>

                <!-- 最终方案标签 -->
                <el-tab-pane label="📝 最终方案" name="final" v-if="result?.final_plan">
                  <el-table :data="result.final_plan.suggestions" style="width: 100%" max-height="400">
                    <el-table-column prop="slide_index" label="页码" width="80" />
                    <el-table-column prop="optimization_dimension" label="维度" width="100" />
                    <el-table-column prop="suggestion" label="建议" show-overflow-tooltip />
                    <el-table-column prop="reason" label="理由" show-overflow-tooltip />
                  </el-table>
                </el-tab-pane>
              </el-tabs>

              <!-- 操作按钮 -->
              <el-space size="large">
                <el-button type="primary" size="large" @click="handleDownload">
                  <el-icon><Download /></el-icon>
                  下载优化后的PPT
                </el-button>
                <el-button size="large" @click="handleDownloadReport" v-if="changeReport">
                  <el-icon><Document /></el-icon>
                  下载修改报告
                </el-button>
                <el-button size="large" @click="handleReset">
                  <el-icon><RefreshLeft /></el-icon>
                  重新上传
                </el-button>
              </el-space>
            </el-space>
          </template>
        </el-result>
      </div>

      <!-- 失败提示 -->
      <div v-if="currentStep === 'failed'" class="failed-section">
        <el-result icon="error" title="处理失败">
          <template #sub-title>
            {{ progress.message }}
          </template>
          <template #extra>
            <el-button type="primary" @click="handleReset">重新上传</el-button>
          </template>
        </el-result>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  UploadFilled, Upload, Download, RefreshLeft,
  Back, Right, Document
} from '@element-plus/icons-vue'
import api from '@/api'

// 导入新组件
import OverallAnalysisCard from '@/components/OverallAnalysisCard.vue'
import OptimizationOpportunityList from '@/components/OptimizationOpportunityList.vue'
import SlideAnalysisList from '@/components/SlideAnalysisList.vue'
import ChangeReportDisplay from '@/components/ChangeReportDisplay.vue'

// ============================================================================
// 状态管理
// ============================================================================

const currentStep = ref('upload') // upload, processing, review, optimizing, result, failed
const selectedFile = ref(null)
const uploading = ref(false)
const submitting = ref(false)
const pptId = ref(null)
const progress = ref({
  status: 'pending',
  progress: 0,
  current_step: '',
  message: '',
  requires_user_action: false,
  action_url: null
})
const result = ref(null)
const activeTab = ref('analysis')
let pollTimer = null

// 新增：内容分析相关状态
const contentAnalysis = ref(null)
const editedOpportunities = ref([])
const changeReport = ref(null)

// 新增：用户偏好设置
const userPreferences = ref({
  style: null,
  color_scheme: 'keep',
  emphasis_areas: ['content', 'visual'],
  constraints: ['keep_structure']
})
const additionalInstructions = ref('')

// ============================================================================
// 计算属性
// ============================================================================

const currentStepIndex = computed(() => {
  const stepMap = {
    'upload': 0,
    'processing': 1,
    'review': 2,
    'optimizing': 3,
    'result': 4,
    'failed': 4
  }
  return stepMap[currentStep.value] || 0
})

const progressStatus = computed(() => {
  if (progress.value.progress === 100) return 'success'
  if (progress.value.status === 'failed') return 'exception'
  return undefined
})

// ============================================================================
// 方法
// ============================================================================

const handleFileChange = (file) => {
  selectedFile.value = file.raw
}

const handleUpload = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }

  uploading.value = true
  try {
    const response = await api.uploadPPT(selectedFile.value)
    pptId.value = response.ppt_id
    ElMessage.success('文件上传成功，开始处理')
    currentStep.value = 'processing'
    startPolling()
  } catch (error) {
    ElMessage.error('上传失败：' + (error.message || '未知错误'))
  } finally {
    uploading.value = false
  }
}

const startPolling = () => {
  pollTimer = setInterval(async () => {
    try {
      const status = await api.getStatus(pptId.value)
      progress.value = status

      // 处理不同状态
      if (status.status === 'waiting_user_review') {
        // 等待用户审查 - 停止轮询，加载分析结果
        stopPolling()
        await loadContentAnalysis()
        currentStep.value = 'review'
      } else if (status.status === 'completed') {
        // 已完成 - 停止轮询，加载结果
        stopPolling()
        await loadResult()
      } else if (status.status === 'failed') {
        // 失败
        stopPolling()
        currentStep.value = 'failed'
        ElMessage.error('处理失败：' + status.message)
      } else {
        // 继续轮询（processing, content_analyzing, user_editing, optimizing等）
        if (['user_editing', 'optimizing', 'analyzing', 'generating'].includes(status.status)) {
          currentStep.value = 'optimizing'
        }
      }
    } catch (error) {
      console.error('获取状态失败:', error)
    }
  }, 2000)
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

// 加载内容分析结果
const loadContentAnalysis = async () => {
  try {
    const response = await api.getContentAnalysis(pptId.value)
    contentAnalysis.value = response.analysis
    // 深拷贝优化机会列表供用户编辑
    editedOpportunities.value = JSON.parse(
      JSON.stringify(response.analysis.optimization_opportunities)
    )
    ElMessage.success('内容分析完成，请审查优化建议')
  } catch (error) {
    ElMessage.error('获取分析结果失败：' + (error.message || '未知错误'))
    currentStep.value = 'failed'
  }
}

// 处理优化机会更新
const handleOpportunitiesUpdate = (newOpportunities) => {
  editedOpportunities.value = newOpportunities
}

// 提交用户编辑
const handleSubmitEdits = async () => {
  const approvedCount = editedOpportunities.value.filter(o => o.user_approved).length

  if (approvedCount === 0) {
    ElMessage.warning('您还没有选择任何优化建议，是否跳过审查使用默认建议？')
    return
  }

  submitting.value = true
  try {
    const editRequest = {
      ppt_id: pptId.value,
      modified_opportunities: editedOpportunities.value,
      additional_instructions: additionalInstructions.value || null,
      preferences: userPreferences.value.style ? userPreferences.value : null
    }

    await api.submitEdits(pptId.value, editRequest)
    ElMessage.success(`已提交 ${approvedCount} 条优化建议，开始执行优化...`)
    currentStep.value = 'optimizing'
    startPolling()
  } catch (error) {
    ElMessage.error('提交失败：' + (error.message || '未知错误'))
  } finally {
    submitting.value = false
  }
}

// 跳过审查
const handleSkipReview = async () => {
  submitting.value = true
  try {
    await api.skipReview(pptId.value)
    ElMessage.success('使用默认优化建议，开始执行优化...')
    currentStep.value = 'optimizing'
    startPolling()
  } catch (error) {
    ElMessage.error('操作失败：' + (error.message || '未知错误'))
  } finally {
    submitting.value = false
  }
}

// 加载最终结果
const loadResult = async () => {
  try {
    const res = await api.getResult(pptId.value)
    result.value = res

    // 加载修改追踪报告
    if (res.change_report) {
      changeReport.value = res.change_report
    } else {
      // 尝试单独获取
      try {
        const reportRes = await api.getChangeReport(pptId.value)
        changeReport.value = reportRes.report
      } catch (error) {
        console.warn('获取修改报告失败:', error)
      }
    }

    currentStep.value = 'result'
    ElMessage.success('处理完成!')
  } catch (error) {
    ElMessage.error('获取结果失败：' + (error.message || '未知错误'))
    currentStep.value = 'failed'
  }
}

const handleDownload = () => {
  const url = api.downloadPPT(pptId.value)
  window.open(url, '_blank')
  ElMessage.success('开始下载PPT')
}

const handleDownloadReport = () => {
  if (!changeReport.value) return

  // 导出为JSON
  const json = JSON.stringify(changeReport.value, null, 2)
  const blob = new Blob([json], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `change-report-${pptId.value}.json`
  a.click()
  URL.revokeObjectURL(url)

  ElMessage.success('修改报告已下载')
}

const handleReset = () => {
  currentStep.value = 'upload'
  selectedFile.value = null
  pptId.value = null
  progress.value = {
    status: 'pending',
    progress: 0,
    current_step: '',
    message: '',
    requires_user_action: false,
    action_url: null
  }
  result.value = null
  contentAnalysis.value = null
  editedOpportunities.value = []
  changeReport.value = null
  userPreferences.value = {
    style: null,
    color_scheme: 'keep',
    emphasis_areas: ['content', 'visual'],
    constraints: ['keep_structure']
  }
  additionalInstructions.value = ''
  activeTab.value = 'analysis'
  stopPolling()
}

// 辅助函数
const getStatusType = (status) => {
  const map = {
    'pending': 'info',
    'parsing': 'warning',
    'content_analyzing': 'warning',
    'waiting_user_review': 'success',
    'user_editing': 'warning',
    'optimizing': 'warning',
    'analyzing': 'warning',
    'correcting': 'warning',
    'generating': 'warning',
    'completed': 'success',
    'failed': 'danger'
  }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = {
    'pending': '等待中',
    'parsing': '解析中',
    'content_analyzing': '内容分析中',
    'waiting_user_review': '等待审查',
    'user_editing': '处理编辑中',
    'optimizing': '执行优化中',
    'analyzing': '模型分析中',
    'correcting': '迭代修正中',
    'generating': '生成PPT中',
    'completed': '已完成',
    'failed': '失败'
  }
  return map[status] || status
}

const getPriorityType = (priority) => {
  const map = {
    'must': 'danger',
    'recommend': 'warning',
    'optional': 'info'
  }
  return map[priority] || ''
}

const formatDate = (dateStr) => {
  if (!dateStr) return '未知'
  return new Date(dateStr).toLocaleString('zh-CN')
}

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.home-container {
  max-width: 1400px;
  margin: 40px auto;
  padding: 0 20px;
}

.main-card {
  min-height: 500px;
  border-radius: 20px;
}

.steps-container {
  padding: 30px 40px 20px;
  background: linear-gradient(to right, #f5f7fa, #ffffff);
  border-radius: 20px 20px 0 0;
}

.upload-section {
  padding: 60px 20px;
  text-align: center;
}

.upload-demo {
  margin-bottom: 30px;
}

.upload-btn {
  width: 200px;
  height: 50px;
  font-size: 16px;
}

.processing-section,
.result-section,
.failed-section {
  padding: 40px 20px;
}

.status-info {
  margin: 20px 0;
}

.current-step {
  font-size: 18px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 10px;
}

.message {
  font-size: 14px;
  color: #666;
}

.status-tag {
  margin-top: 20px;
}

/* 审查步骤样式 */
.review-section {
  padding: 30px;
  max-width: 1200px;
  margin: 0 auto;
}

.section-header {
  text-align: center;
  margin-bottom: 30px;
}

.section-header h2 {
  margin: 0 0 10px 0;
  font-size: 28px;
  color: #303133;
}

.section-subtitle {
  margin: 0;
  font-size: 14px;
  color: #909399;
}

.preferences-card {
  margin: 20px 0;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: bold;
}

.header-icon {
  font-size: 20px;
}

.review-actions {
  margin-top: 30px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
  display: flex;
  justify-content: center;
}

:deep(.el-upload-dragger) {
  padding: 60px;
}

:deep(.el-icon--upload) {
  font-size: 80px;
  margin: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .steps-container {
    padding: 20px 10px;
  }

  .review-section {
    padding: 20px 10px;
  }

  .section-header h2 {
    font-size: 22px;
  }

  .review-actions {
    padding: 15px;
  }

  :deep(.el-space) {
    flex-direction: column;
    width: 100%;
  }

  :deep(.el-space .el-button) {
    width: 100%;
  }
}
</style>
