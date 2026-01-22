# 多模型协同的PPT智能优化与自动生成网页系统

## 项目简介

这是一个基于多个大模型协同工作的智能PPT优化系统,实现了从PPT上传、多模型并行分析、跨模型迭代修正到自动生成优化后PPT的完整流程。

### 核心功能

- **PPT智能解析**: 自动解析PPT内容、版式、样式等信息
- **多模型协同**: 集成讯飞星火、文心一言、通义千问、腾讯混元四大模型
- **迭代修正机制**: 模型间差异化分工,交叉修正,确保优化建议的准确性
- **冲突智能调和**: 自动检测并调和模型建议冲突,支持人工干预
- **自动生成PPT**: 基于最终优化方案自动生成新的PPT文件

### 技术架构

- **前端**: Vue3 + Element Plus
- **后端**: Python + FastAPI
- **PPT处理**: python-pptx
- **模型对接**: 异步并行调用多个大模型API

## 项目结构

```
ppt-ai-optimizer/
├── frontend/              # 前端代码
│   ├── src/
│   │   ├── components/   # Vue组件
│   │   ├── views/        # 页面视图
│   │   ├── api/          # API接口
│   │   └── utils/        # 工具函数
│   └── package.json
├── backend/              # 后端代码
│   ├── app/
│   │   ├── api/          # API路由
│   │   ├── core/         # 核心配置
│   │   ├── models/       # 数据模型
│   │   ├── services/     # 业务逻辑
│   │   │   ├── ppt_parser.py        # PPT解析器
│   │   │   ├── model_engine.py      # 模型调用引擎
│   │   │   ├── iteration_corrector.py # 迭代修正器
│   │   │   └── ppt_generator.py     # PPT生成器
│   │   └── utils/        # 工具函数
│   ├── config/           # 配置文件
│   ├── logs/             # 日志目录
│   ├── uploads/          # 上传文件目录
│   ├── requirements.txt  # Python依赖
│   └── main.py           # 应用入口
├── docs/                 # 文档
│   └── 需求文档.md
├── .gitignore
└── README.md
```

## 快速开始

### 环境要求

- Python 3.9+
- Node.js 16+
- 4个大模型的API Key

### 后端安装与启动

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置API Key (复制配置模板并填写)
cp config/config.example.yaml config/config.yaml
# 编辑 config/config.yaml 填写各模型的API Key

# 启动后端服务
python main.py
```

### 前端安装与启动

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### Docker 部署

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d
```

## API Key 申请指南

### 1. 讯飞星火PPT智能助手
- 官网: https://www.xfyun.cn
- 文档: https://www.xfyun.cn/doc/spark/ppt-assistant.html
- 申请流程: 注册账号 → 创建应用 → 获取 APPID、APIKey、APISecret

### 2. 百度文心一言PPT优化模块
- 官网: https://yiyan.baidu.com
- 文档: https://yiyan.baidu.com/developer/docs/ppt-optimize
- 申请流程: 登录百度账号 → 开通服务 → 获取 API Key 和 Secret Key

### 3. 阿里云通义千问PPT生成器
- 官网: https://www.aliyun.com/product/dashscope
- 文档: https://help.aliyun.com/document_detail/2511236.html
- 申请流程: 登录阿里云 → 开通服务 → 创建 API Key

### 4. 腾讯混元PPT智能分析模型
- 官网: https://cloud.tencent.com/product/hunyuan
- 文档: https://cloud.tencent.com/document/product/1729/95224
- 申请流程: 登录腾讯云 → 开通混元服务 → 获取 SecretId 和 SecretKey

## 核心功能说明

### 1. PPT解析
系统使用 `python-pptx` 库解析上传的PPT文件,提取:
- 每页幻灯片的版式类型
- 文本内容及样式
- 图片和图表信息
- 配色方案

### 2. 多模型并行调用
系统会同时调用4个大模型,各模型侧重点:
- **讯飞星火**: 场景化适配、行业定制
- **文心一言**: 排版设计、配色优化
- **通义千问**: 内容逻辑、图表可视化
- **腾讯混元**: 多建议融合、冲突调和

### 3. 迭代修正流程
```
讯飞星火(全维度建议)
  ↓
文心一言(修正layout/color)
  ↓
通义千问(修正logic/chart)
  ↓
腾讯混元(融合所有建议,调和冲突)
  ↓
最终优化方案
```

### 4. 冲突检测与调和
- 自动检测模型建议冲突(同一位置不同建议)
- 冲突率 < 5%: 自动调和
- 冲突率 5%-10%: 模型仲裁
- 冲突率 > 10%: 提示用户手动选择

## 配置说明

配置文件位于 `backend/config/config.yaml`:

```yaml
# 模型配置
models:
  xunfei:
    enabled: true
    api_key: "your_api_key"
    timeout: 30

  wenxin:
    enabled: true
    api_key: "your_api_key"
    secret_key: "your_secret_key"
    timeout: 30

  qianwen:
    enabled: true
    api_key: "your_api_key"
    timeout: 30

  hunyuan:
    enabled: true
    secret_id: "your_secret_id"
    secret_key: "your_secret_key"
    timeout: 30

# 迭代修正配置
iteration:
  max_rounds: 2              # 最大迭代轮次
  conflict_threshold: 0.05   # 冲突率阈值(5%)
  manual_threshold: 0.10     # 人工干预阈值(10%)

# 上传配置
upload:
  max_size: 50  # MB
  allowed_extensions: [".pptx"]
```

## 扩展指南

### 新增模型

1. 在 `backend/app/services/model_engine.py` 中新增模型接口类
2. 实现标准化输入输出转换
3. 在配置文件中添加模型配置
4. 更新迭代修正流程中的模型角色分配

详见: `docs/扩展指南.md`

## 测试

```bash
# 后端单元测试
cd backend
pytest tests/

# 前端测试
cd frontend
npm run test

# 端到端测试
npm run test:e2e
```

## 日志说明

系统日志存储在 `backend/logs/` 目录:
- `app.log`: 应用主日志
- `model_calls.log`: 模型调用日志
- `iteration.log`: 迭代修正日志
- `conflicts.log`: 冲突检测与调和日志

每个日志都关联 `ppt_id`,便于追溯完整处理流程。

## 常见问题

### Q: 某个模型调用失败怎么办?
A: 系统有自动降级机制,会跳过失败的模型继续使用其他模型完成分析。

### Q: 如何调整迭代轮次?
A: 修改 `config/config.yaml` 中的 `iteration.max_rounds` 参数。

### Q: 支持哪些PPT格式?
A: 目前仅支持 .pptx 格式(Office 2007及以上版本)。

## 许可证

MIT License

## 联系方式

- 项目作者: lilywang
- 邮箱: lilywang@lexin.com
- GitHub: https://github.com/lilywang-lx

## 致谢

感谢讯飞星火、文心一言、通义千问、腾讯混元提供的大模型API支持。

---

# 🆕 新功能：两阶段智能优化 (2026-01-22)

## 功能概述

系统已升级为**两阶段智能优化流程**，让用户深度参与优化过程：

### ✨ 第一阶段：智能内容分析
- 🧠 大模型深度解析PPT内容
- 📊 提取核心要点（3-5条）
- 📑 分析整体大纲结构
- 📈 评估内容质量（连贯性、逻辑性、完整性）
- 🎯 智能识别优化机会并分优先级

### ✏️ 第二阶段：交互式优化
- ☑️ 用户审查并选择优化建议
- ✍️ 用户可编辑建议内容
- 💬 用户可添加备注
- ⚙️ 用户可设置优化偏好
- 📋 生成详细的修改追踪报告

## 新增组件

### 后端服务 (backend/app/services/)

1. **ContentAnalyzer** (420行)
   - 使用大模型进行深度内容分析
   - 提取整体分析、每页分析、优化机会
   - 支持多种大模型（默认使用通义千问）

2. **ChangeTracker** (240行)
   - 追踪所有修改记录
   - 生成详细的修改报告
   - 支持导出JSON/Markdown格式

3. **OptimizationOrchestrator** (260行)
   - 协调两阶段优化流程
   - 管理用户编辑和模型优化
   - 智能转换优化机会为建议

### 前端组件 (frontend/src/components/)

1. **OverallAnalysisCard.vue** (320行)
   - 展示整体分析摘要
   - 核心要点、质量评分、大纲结构
   - 美观的可视化展示

2. **OptimizationOpportunityList.vue** (470行) ⭐
   - 优化建议列表展示和编辑
   - 多维度筛选（优先级、类别、范围）
   - 完整的CRUD操作
   - 实时统计

3. **SlideAnalysisList.vue** (240行)
   - 每页详细分析展示
   - 质量评分、问题识别
   - 折叠/展开功能

4. **ChangeReportDisplay.vue** (530行)
   - 修改追踪报告展示
   - 丰富的统计图表
   - 按页面分组展示
   - 支持导出报告

## 新增API端点

```
GET  /api/content-analysis/{ppt_id}  # 获取内容分析结果
POST /api/submit-edits/{ppt_id}      # 提交用户编辑
POST /api/skip-review/{ppt_id}       # 跳过审查（使用默认建议）
GET  /api/change-report/{ppt_id}     # 获取修改追踪报告
```

## 新增配置选项

```yaml
# 内容分析配置
content_analysis:
  enabled: true
  analyzer_model: "qianwen"      # 分析模型
  timeout: 60
  analysis_depth: "comprehensive"

# 优化流程配置
optimization_flow:
  require_user_review: true      # 是否强制用户审查
  auto_approve_timeout: -1       # 自动批准超时（-1表示永不）

# 修改追踪配置
change_tracking:
  enabled: true
  detail_level: "detailed"
  export_formats: ["json", "markdown"]
```

## 工作流程对比

### 原有流程
```
上传 → 解析 → 多模型分析 → 迭代修正 → 生成PPT → 完成
```

### 新流程 ⭐
```
上传 → 解析 → 内容分析 → 【用户审查编辑】→ 执行优化 → 生成PPT + 修改报告 → 完成
                            ↑
                        用户可控点
```

## 使用示例

### 前端集成

```vue
<template>
  <!-- 审查步骤 -->
  <div v-if="currentStep === 'review'">
    <!-- 整体分析 -->
    <OverallAnalysisCard :analysis="contentAnalysis.overall_analysis" />

    <!-- 优化建议列表 -->
    <OptimizationOpportunityList
      :opportunities="editedOpportunities"
      @update:opportunities="editedOpportunities = $event"
    />

    <!-- 操作按钮 -->
    <el-button @click="skipReview">使用默认建议</el-button>
    <el-button type="primary" @click="submitEdits">应用选中建议</el-button>
  </div>

  <!-- 结果展示 -->
  <div v-if="currentStep === 'result'">
    <el-tabs>
      <el-tab-pane label="内容分析">
        <OverallAnalysisCard :analysis="result.content_analysis" />
      </el-tab-pane>
      <el-tab-pane label="修改追踪">
        <ChangeReportDisplay :report="changeReport" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import api from '@/api'
import OverallAnalysisCard from '@/components/OverallAnalysisCard.vue'
import OptimizationOpportunityList from '@/components/OptimizationOpportunityList.vue'
import ChangeReportDisplay from '@/components/ChangeReportDisplay.vue'

// 加载内容分析
const loadContentAnalysis = async () => {
  const response = await api.getContentAnalysis(pptId)
  contentAnalysis.value = response.analysis
}

// 提交编辑
const submitEdits = async () => {
  const editRequest = {
    ppt_id: pptId.value,
    modified_opportunities: editedOpportunities.value,
    additional_instructions: "...",
    preferences: { style: "professional" }
  }
  await api.submitEdits(pptId.value, editRequest)
}

// 跳过审查
const skipReview = async () => {
  await api.skipReview(pptId.value)
}
</script>
```

## 文档

详细文档位于 `docs/` 目录：

- **content-analyzer-design.md** - 系统设计文档（400行）
- **implementation-summary.md** - 后端实现总结（600行）
- **frontend-ui-design.md** - 前端UI设计方案（500行）
- **frontend-implementation-summary.md** - 前端组件文档（500行）

## 升级说明

### 从旧版本升级

1. **后端**：
   ```bash
   cd backend
   pip install -r requirements.txt  # 更新依赖
   # 配置文件会自动向后兼容
   ```

2. **前端**：
   ```bash
   cd frontend
   npm install  # 更新依赖
   ```

3. **配置**：
   - 在 `config/config.yaml` 中添加新的配置项（可选）
   - 系统会使用默认值如果配置项不存在

### 向后兼容

- ✅ 旧的API端点完全兼容
- ✅ 可通过配置关闭新功能
- ✅ 前端可渐进式升级

## 技术亮点

- 🎯 **用户为中心**：完全可控的优化过程
- 🧠 **智能分析**：多维度内容评估
- 📊 **可视化**：美观的统计图表
- ♿ **可访问性**：响应式设计，键盘导航
- 🚀 **高性能**：异步并行，虚拟滚动

## 开发进度

- ✅ 后端核心服务（100%）
- ✅ 前端核心组件（100%）
- 🔄 前端主页面集成（待完成）
- 🔄 端到端测试（待完成）

---

**🎉 新功能已完成开发，欢迎体验和反馈！**
