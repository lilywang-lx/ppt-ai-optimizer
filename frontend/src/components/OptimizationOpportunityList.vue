<template>
  <el-card class="opportunity-list-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <div class="header-left">
          <span class="header-icon">🎯</span>
          <span class="header-title">优化建议清单</span>
          <el-tag type="info" size="large">{{ opportunities.length }} 项</el-tag>
        </div>
        <div class="header-right">
          <el-button size="small" @click="selectAll">全选</el-button>
          <el-button size="small" @click="unselectAll">全不选</el-button>
        </div>
      </div>
    </template>

    <!-- 筛选器 -->
    <div class="filters">
      <div class="filter-group">
        <span class="filter-label">优先级：</span>
        <el-radio-group v-model="priorityFilter" size="small">
          <el-radio-button label="all">全部</el-radio-button>
          <el-radio-button label="high">🔴 高</el-radio-button>
          <el-radio-button label="medium">🟡 中</el-radio-button>
          <el-radio-button label="low">🟢 低</el-radio-button>
        </el-radio-group>
      </div>

      <div class="filter-group">
        <span class="filter-label">类别：</span>
        <el-radio-group v-model="categoryFilter" size="small">
          <el-radio-button label="all">全部</el-radio-button>
          <el-radio-button label="content">内容</el-radio-button>
          <el-radio-button label="structure">结构</el-radio-button>
          <el-radio-button label="logic">逻辑</el-radio-button>
          <el-radio-button label="presentation">呈现</el-radio-button>
        </el-radio-group>
      </div>

      <div class="filter-group">
        <span class="filter-label">范围：</span>
        <el-radio-group v-model="scopeFilter" size="small">
          <el-radio-button label="all">全部</el-radio-button>
          <el-radio-button label="overall">整体</el-radio-button>
          <el-radio-button label="section">章节</el-radio-button>
          <el-radio-button label="slide">单页</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <!-- 建议列表 -->
    <div class="opportunities-list">
      <div
        v-for="(opp, index) in filteredOpportunities"
        :key="opp.opportunity_id"
        class="opportunity-item"
        :class="{ 'opportunity-item-selected': opp.user_approved }"
      >
        <!-- 选择框和优先级 -->
        <div class="item-header">
          <el-checkbox
            v-model="opp.user_approved"
            size="large"
            @change="handleApprovalChange(opp)"
          />
          <el-tag :type="getPriorityType(opp.priority)" size="large">
            {{ getPriorityIcon(opp.priority) }} {{ getPriorityText(opp.priority) }}
          </el-tag>
          <el-tag type="info" size="small">{{ getScopeText(opp.scope) }}</el-tag>
          <span class="item-impact">影响力: {{ opp.impact_score.toFixed(1) }}/10</span>
          <el-tag size="small">{{ getCategoryText(opp.category) }}</el-tag>
        </div>

        <!-- 标题 -->
        <h4 class="item-title">{{ opp.title }}</h4>

        <!-- 详细信息 -->
        <div class="item-details">
          <div class="detail-row">
            <span class="detail-label">涉及页面：</span>
            <span class="detail-value">
              {{ opp.scope === 'overall' ? '整体' : `第 ${opp.slide_indices.join(', ')} 页` }}
            </span>
          </div>

          <div class="detail-row">
            <span class="detail-label">当前状态：</span>
            <span class="detail-value">{{ opp.current_state }}</span>
          </div>

          <div class="detail-row">
            <span class="detail-label">建议操作：</span>
            <span class="detail-value suggestion-text">{{ opp.suggested_action }}</span>
          </div>

          <div class="detail-row">
            <span class="detail-label">预期收益：</span>
            <span class="detail-value benefit-text">{{ opp.expected_benefit }}</span>
          </div>

          <div v-if="opp.description" class="detail-row">
            <span class="detail-label">详细描述：</span>
            <span class="detail-value">{{ opp.description }}</span>
          </div>

          <!-- 用户备注 -->
          <div v-if="opp.user_comment" class="user-comment">
            <el-alert type="info" :closable="false">
              <template #title>
                <span>👤 您的备注：{{ opp.user_comment }}</span>
              </template>
            </el-alert>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="item-actions">
          <el-button size="small" @click="editOpportunity(opp)">
            <el-icon><Edit /></el-icon>
            修改建议
          </el-button>
          <el-button size="small" @click="addComment(opp)">
            <el-icon><ChatDotRound /></el-icon>
            添加备注
          </el-button>
        </div>
      </div>

      <!-- 空状态 -->
      <el-empty v-if="filteredOpportunities.length === 0" description="没有符合条件的优化建议" />
    </div>

    <!-- 统计信息 -->
    <div class="statistics">
      <el-divider />
      <div class="stats-content">
        <span>已选 <strong>{{ approvedCount }}</strong> / {{ opportunities.length }} 项建议</span>
        <span>预计影响 <strong>{{ affectedSlidesCount }}</strong> 页</span>
      </div>
    </div>

    <!-- 编辑弹窗 -->
    <el-dialog
      v-model="editDialogVisible"
      title="修改优化建议"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form v-if="editingOpp" :model="editingOpp" label-width="100px">
        <el-form-item label="建议标题">
          <el-input v-model="editingOpp.title" />
        </el-form-item>

        <el-form-item label="建议操作">
          <el-input
            v-model="editingOpp.suggested_action"
            type="textarea"
            :rows="3"
            placeholder="描述具体的优化操作..."
          />
        </el-form-item>

        <el-form-item label="预期收益">
          <el-input
            v-model="editingOpp.expected_benefit"
            type="textarea"
            :rows="2"
            placeholder="描述优化后的预期效果..."
          />
        </el-form-item>

        <el-form-item label="优先级">
          <el-radio-group v-model="editingOpp.priority">
            <el-radio label="high">高</el-radio>
            <el-radio label="medium">中</el-radio>
            <el-radio label="low">低</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="影响力评分">
          <el-slider v-model="editingOpp.impact_score" :min="0" :max="10" :step="0.5" show-stops />
        </el-form-item>

        <el-form-item label="用户备注">
          <el-input
            v-model="editingOpp.user_comment"
            type="textarea"
            :rows="3"
            placeholder="添加您的备注或补充说明..."
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">保存修改</el-button>
      </template>
    </el-dialog>

    <!-- 备注弹窗 -->
    <el-dialog
      v-model="commentDialogVisible"
      title="添加备注"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-input
        v-model="commentText"
        type="textarea"
        :rows="5"
        placeholder="添加您对这条建议的备注或想法..."
      />
      <template #footer>
        <el-button @click="commentDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveComment">保存备注</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Edit, ChatDotRound } from '@element-plus/icons-vue'

const props = defineProps({
  opportunities: {
    type: Array,
    required: true
  }
})

const emit = defineEmits(['update:opportunities'])

// 筛选条件
const priorityFilter = ref('all')
const categoryFilter = ref('all')
const scopeFilter = ref('all')

// 编辑对话框
const editDialogVisible = ref(false)
const editingOpp = ref(null)
const editingIndex = ref(-1)

// 备注对话框
const commentDialogVisible = ref(false)
const commentText = ref('')
const commentingOpp = ref(null)

// 筛选后的建议列表
const filteredOpportunities = computed(() => {
  return props.opportunities.filter(opp => {
    if (priorityFilter.value !== 'all' && opp.priority !== priorityFilter.value) return false
    if (categoryFilter.value !== 'all' && opp.category !== categoryFilter.value) return false
    if (scopeFilter.value !== 'all' && opp.scope !== scopeFilter.value) return false
    return true
  })
})

// 已批准数量
const approvedCount = computed(() => {
  return props.opportunities.filter(opp => opp.user_approved).length
})

// 影响的页面数量
const affectedSlidesCount = computed(() => {
  const slides = new Set()
  props.opportunities.forEach(opp => {
    if (opp.user_approved) {
      opp.slide_indices.forEach(idx => slides.add(idx))
    }
  })
  return slides.size
})

// 全选
const selectAll = () => {
  filteredOpportunities.value.forEach(opp => {
    opp.user_approved = true
  })
  emit('update:opportunities', props.opportunities)
}

// 全不选
const unselectAll = () => {
  filteredOpportunities.value.forEach(opp => {
    opp.user_approved = false
  })
  emit('update:opportunities', props.opportunities)
}

// 批准状态变化
const handleApprovalChange = (opp) => {
  emit('update:opportunities', props.opportunities)
}

// 编辑建议
const editOpportunity = (opp) => {
  editingOpp.value = { ...opp }
  editingIndex.value = props.opportunities.findIndex(o => o.opportunity_id === opp.opportunity_id)
  editDialogVisible.value = true
}

// 保存编辑
const saveEdit = () => {
  if (editingIndex.value !== -1) {
    editingOpp.value.user_modified = true
    Object.assign(props.opportunities[editingIndex.value], editingOpp.value)
    emit('update:opportunities', props.opportunities)
  }
  editDialogVisible.value = false
}

// 添加备注
const addComment = (opp) => {
  commentingOpp.value = opp
  commentText.value = opp.user_comment || ''
  commentDialogVisible.value = true
}

// 保存备注
const saveComment = () => {
  if (commentingOpp.value) {
    commentingOpp.value.user_comment = commentText.value
    commentingOpp.value.user_modified = true
    emit('update:opportunities', props.opportunities)
  }
  commentDialogVisible.value = false
}

// 辅助函数
const getPriorityIcon = (priority) => {
  const icons = { high: '🔴', medium: '🟡', low: '🟢' }
  return icons[priority] || ''
}

const getPriorityText = (priority) => {
  const texts = { high: '高', medium: '中', low: '低' }
  return texts[priority] || priority
}

const getPriorityType = (priority) => {
  const types = { high: 'danger', medium: 'warning', low: 'success' }
  return types[priority] || ''
}

const getScopeText = (scope) => {
  const texts = { overall: '整体', section: '章节', slide: '单页' }
  return texts[scope] || scope
}

const getCategoryText = (category) => {
  const texts = {
    content: '内容',
    structure: '结构',
    logic: '逻辑',
    presentation: '呈现'
  }
  return texts[category] || category
}
</script>

<style scoped>
.opportunity-list-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 18px;
  font-weight: bold;
}

.header-icon {
  font-size: 24px;
}

.header-right {
  display: flex;
  gap: 8px;
}

.filters {
  margin-bottom: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.filter-label {
  font-size: 14px;
  color: #606266;
  min-width: 60px;
}

.opportunities-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.opportunity-item {
  padding: 20px;
  border: 2px solid #dcdfe6;
  border-radius: 8px;
  background: white;
  transition: all 0.3s;
}

.opportunity-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.opportunity-item-selected {
  border-color: #67c23a;
  background: #f0f9ff;
}

.item-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.item-impact {
  font-size: 13px;
  color: #606266;
}

.item-title {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.item-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.detail-row {
  display: flex;
  gap: 8px;
  font-size: 14px;
  line-height: 1.6;
}

.detail-label {
  color: #909399;
  min-width: 80px;
  flex-shrink: 0;
}

.detail-value {
  color: #606266;
  flex: 1;
}

.suggestion-text {
  color: #409eff;
  font-weight: 500;
}

.benefit-text {
  color: #67c23a;
  font-weight: 500;
}

.user-comment {
  margin-top: 8px;
}

.item-actions {
  display: flex;
  gap: 8px;
}

.statistics {
  margin-top: 16px;
}

.stats-content {
  display: flex;
  justify-content: space-around;
  align-items: center;
  font-size: 14px;
  color: #606266;
}

.stats-content strong {
  color: #409eff;
  font-size: 18px;
  margin: 0 4px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }

  .header-left {
    flex-wrap: wrap;
  }

  .filters {
    gap: 16px;
  }

  .filter-group {
    flex-direction: column;
    align-items: flex-start;
  }

  .item-header {
    flex-wrap: wrap;
  }

  .detail-row {
    flex-direction: column;
    gap: 4px;
  }

  .stats-content {
    flex-direction: column;
    gap: 12px;
  }
}
</style>
