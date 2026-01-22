import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 300000 // 5分钟超时
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    ElMessage.error(error.response?.data?.detail || error.message || '请求失败')
    return Promise.reject(error)
  }
)

export default {
  // 上传PPT
  uploadPPT(file) {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 获取处理状态
  getStatus(pptId) {
    return api.get(`/status/${pptId}`)
  },

  // 获取处理结果
  getResult(pptId) {
    return api.get(`/result/${pptId}`)
  },

  // 下载优化后的PPT
  downloadPPT(pptId) {
    return `/api/download/${pptId}`
  },

  // 健康检查
  healthCheck() {
    return api.get('/health')
  },

  // ========== 新增API方法 ==========

  // 获取内容分析结果
  getContentAnalysis(pptId) {
    return api.get(`/content-analysis/${pptId}`)
  },

  // 提交用户编辑
  submitEdits(pptId, editRequest) {
    return api.post(`/submit-edits/${pptId}`, editRequest)
  },

  // 跳过审查（使用默认建议）
  skipReview(pptId) {
    return api.post(`/skip-review/${pptId}`)
  },

  // 获取修改追踪报告
  getChangeReport(pptId) {
    return api.get(`/change-report/${pptId}`)
  }
}
