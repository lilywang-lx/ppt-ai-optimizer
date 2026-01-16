<template>
  <div class="home-container">
    <el-card class="main-card" shadow="hover">
      <!-- 上传区域 -->
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

      <!-- 处理进度 -->
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

      <!-- 结果展示 -->
      <div v-if="currentStep === 'result'" class="result-section">
        <el-result icon="success" title="优化完成！">
          <template #sub-title>
            PPT已成功优化，点击下方按钮查看结果或下载文件
          </template>
          <template #extra>
            <el-space direction="vertical" size="large" style="width: 100%">
              <!-- 优化统计 -->
              <el-descriptions :column="2" border>
                <el-descriptions-item label="模型数量">
                  {{ result?.model_suggestions?.length || 0 }} 个
                </el-descriptions-item>
                <el-descriptions-item label="优化建议">
                  {{ result?.final_plan?.suggestions?.length || 0 }} 条
                </el-descriptions-item>
                <el-descriptions-item label="冲突率">
                  {{ (result?.final_plan?.conflict_rate * 100).toFixed(2) }}%
                </el-descriptions-item>
                <el-descriptions-item label="迭代轮次">
                  {{ result?.final_plan?.iteration_history?.length || 0 }} 轮
                </el-descriptions-item>
              </el-descriptions>

              <!-- 模型建议标签页 -->
              <el-tabs v-model="activeTab" type="border-card">
                <el-tab-pane
                  v-for="(suggestion, index) in result?.model_suggestions"
                  :key="index"
                  :label="suggestion.model_name"
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

                <el-tab-pane label="最终方案" name="final">
                  <el-table :data="result?.final_plan?.suggestions" style="width: 100%" max-height="400">
                    <el-table-column prop="slide_index" label="页码" width="80" />
                    <el-table-column prop="optimization_dimension" label="维度" width="100" />
                    <el-table-column prop="suggestion" label="建议" show-overflow-tooltip />
                    <el-table-column prop="reason" label="理由" show-overflow-tooltip />
                  </el-table>
                </el-tab-pane>
              </el-tabs>

              <!-- 操作按钮 -->
              <el-space>
                <el-button type="primary" size="large" @click="handleDownload">
                  <el-icon><Download /></el-icon>
                  下载优化后的PPT
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
import { UploadFilled, Upload, Download, RefreshLeft } from '@element-plus/icons-vue'
import api from '@/api'

const currentStep = ref('upload') // upload, processing, result, failed
const selectedFile = ref(null)
const uploading = ref(false)
const pptId = ref(null)
const progress = ref({
  status: 'pending',
  progress: 0,
  current_step: '',
  message: ''
})
const result = ref(null)
const activeTab = ref('model-0')
let pollTimer = null

const progressStatus = computed(() => {
  if (progress.value.progress === 100) return 'success'
  if (progress.value.status === 'failed') return 'exception'
  return undefined
})

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
    ElMessage.error('上传失败：' + error.message)
  } finally {
    uploading.value = false
  }
}

const startPolling = () => {
  pollTimer = setInterval(async () => {
    try {
      const status = await api.getStatus(pptId.value)
      progress.value = status

      if (status.status === 'completed') {
        stopPolling()
        await loadResult()
      } else if (status.status === 'failed') {
        stopPolling()
        currentStep.value = 'failed'
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

const loadResult = async () => {
  try {
    const res = await api.getResult(pptId.value)
    result.value = res
    currentStep.value = 'result'
    ElMessage.success('处理完成!')
  } catch (error) {
    ElMessage.error('获取结果失败')
    currentStep.value = 'failed'
  }
}

const handleDownload = () => {
  const url = api.downloadPPT(pptId.value)
  window.open(url, '_blank')
  ElMessage.success('开始下载')
}

const handleReset = () => {
  currentStep.value = 'upload'
  selectedFile.value = null
  pptId.value = null
  progress.value = { status: 'pending', progress: 0, current_step: '', message: '' }
  result.value = null
  stopPolling()
}

const getStatusType = (status) => {
  const map = {
    'pending': 'info',
    'parsing': 'warning',
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
    'analyzing': '分析中',
    'correcting': '修正中',
    'generating': '生成中',
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

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.home-container {
  max-width: 1200px;
  margin: 40px auto;
  padding: 0 20px;
}

.main-card {
  min-height: 500px;
  border-radius: 20px;
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

:deep(.el-upload-dragger) {
  padding: 60px;
}

:deep(.el-icon--upload) {
  font-size: 80px;
  margin: 0;
}
</style>
