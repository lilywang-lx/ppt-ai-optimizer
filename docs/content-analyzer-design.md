# PPT AI优化器 - 内容分析与交互式优化设计文档

## 1. 功能概述

在现有的多模型优化系统基础上，添加**大模型内容深度分析**和**交互式编辑**功能。

### 1.1 新增功能

1. **内容深度分析**
   - 提取PPT核心要点
   - 分析整体大纲结构
   - 识别每页内容优化点
   - 评估逻辑连贯性

2. **交互式优化流程**
   - 用户查看分析结果
   - 用户可编辑优化建议
   - 基于修改后的建议执行优化
   - 生成详细修改记录

## 2. 系统架构设计

### 2.1 新增工作流程

```
原有流程:
上传PPT → PPT解析 → 多模型分析 → 迭代修正 → 生成PPT

新增流程:
上传PPT → PPT解析 → 【内容深度分析】→ 【用户审查编辑】→ 多模型分析 → 迭代修正 → 生成PPT → 【修改点追踪】
```

### 2.2 两阶段处理模式

#### 阶段一：内容分析阶段 (CONTENT_ANALYZING)
```
1. PPT解析 (10%)
2. 大模型内容分析 (30%)
   - 提取核心要点
   - 分析大纲结构
   - 识别优化机会
3. 生成分析报告 (40%)
4. 等待用户审查 (WAITING_USER_REVIEW)
```

#### 阶段二：优化执行阶段 (OPTIMIZING)
```
5. 接收用户修改 (50%)
6. 多模型优化分析 (70%)
7. 迭代修正 (80%)
8. 生成优化PPT (90%)
9. 生成修改追踪报告 (100%)
10. 完成 (COMPLETED)
```

### 2.3 新增状态

```python
# 处理状态扩展
class ProcessStatus:
    PENDING = "pending"
    PARSING = "parsing"
    CONTENT_ANALYZING = "content_analyzing"      # 新增：内容分析中
    WAITING_USER_REVIEW = "waiting_user_review"  # 新增：等待用户审查
    USER_EDITING = "user_editing"                # 新增：用户编辑中
    OPTIMIZING = "optimizing"                    # 新增：优化执行中
    ANALYZING = "analyzing"                      # 原有：模型分析
    CORRECTING = "correcting"                    # 原有：迭代修正
    GENERATING = "generating"                    # 原有：生成PPT
    COMPLETED = "completed"
    FAILED = "failed"
```

## 3. 数据模型设计

### 3.1 内容分析结果 (ContentAnalysisResult)

```python
class ContentAnalysisResult(BaseModel):
    """大模型内容分析结果"""
    ppt_id: str
    analysis_timestamp: datetime

    # 整体分析
    overall_analysis: OverallAnalysis

    # 每页分析
    slide_analyses: List[SlideAnalysis]

    # 优化建议
    optimization_opportunities: List[OptimizationOpportunity]

    # 元数据
    metadata: Dict = Field(default_factory=dict)


class OverallAnalysis(BaseModel):
    """整体PPT分析"""
    # 核心要点
    key_points: List[str] = Field(description="PPT的核心要点（3-5条）")

    # 主题和目标
    theme: str = Field(description="PPT主题")
    target_audience: str = Field(description="目标受众")
    presentation_goal: str = Field(description="演示目标")

    # 大纲结构分析
    outline_structure: OutlineStructure

    # 整体评估
    content_coherence: float = Field(ge=0, le=10, description="内容连贯性评分(0-10)")
    logic_flow: float = Field(ge=0, le=10, description="逻辑流畅度评分(0-10)")
    completeness: float = Field(ge=0, le=10, description="内容完整性评分(0-10)")

    # 整体优化建议
    overall_suggestions: List[str] = Field(description="整体层面的优化建议")


class OutlineStructure(BaseModel):
    """大纲结构分析"""
    sections: List[Section]
    structure_type: str = Field(description="结构类型：linear/parallel/circular/problem-solution")
    structure_quality: str = Field(description="结构质量：excellent/good/fair/poor")
    structure_issues: List[str] = Field(description="结构问题列表")


class Section(BaseModel):
    """章节信息"""
    section_name: str
    slide_indices: List[int]
    purpose: str
    is_necessary: bool
    improvement_suggestion: Optional[str] = None


class SlideAnalysis(BaseModel):
    """单页内容分析"""
    slide_index: int
    slide_title: str

    # 内容要点
    main_points: List[str] = Field(description="本页主要内容点")

    # 内容质量评估
    clarity: float = Field(ge=0, le=10, description="清晰度(0-10)")
    relevance: float = Field(ge=0, le=10, description="相关性(0-10)")
    information_density: str = Field(description="信息密度：too_dense/appropriate/too_sparse")

    # 问题识别
    issues: List[ContentIssue]

    # 优化方向
    optimization_directions: List[str]


class ContentIssue(BaseModel):
    """内容问题"""
    issue_type: str = Field(description="问题类型：redundant/unclear/missing/misplaced/inconsistent")
    description: str
    severity: str = Field(description="严重程度：critical/major/minor")
    location: Optional[str] = None


class OptimizationOpportunity(BaseModel):
    """优化机会点"""
    opportunity_id: str = Field(default_factory=lambda: f"opp_{uuid.uuid4().hex[:8]}")

    # 位置信息
    scope: str = Field(description="范围：overall/section/slide")
    slide_indices: List[int] = Field(description="涉及的页码（overall时为空）")

    # 优化内容
    category: str = Field(description="类别：content/structure/logic/presentation")
    title: str = Field(description="优化标题")
    description: str = Field(description="详细描述")
    current_state: str = Field(description="当前状态")
    suggested_action: str = Field(description="建议操作")
    expected_benefit: str = Field(description="预期收益")

    # 优先级
    priority: str = Field(description="优先级：high/medium/low")
    impact_score: float = Field(ge=0, le=10, description="影响力评分(0-10)")

    # 用户交互
    user_approved: bool = Field(default=True, description="用户是否批准")
    user_modified: bool = Field(default=False, description="用户是否修改")
    user_comment: Optional[str] = None
```

### 3.2 用户编辑请求 (UserEditRequest)

```python
class UserEditRequest(BaseModel):
    """用户编辑请求"""
    ppt_id: str

    # 用户修改的优化机会
    modified_opportunities: List[OptimizationOpportunity]

    # 用户添加的额外指令
    additional_instructions: Optional[str] = None

    # 用户偏好设置
    preferences: Optional[UserPreferences] = None


class UserPreferences(BaseModel):
    """用户偏好设置"""
    style: Optional[str] = Field(None, description="风格偏好：professional/casual/academic/creative")
    color_scheme: Optional[str] = Field(None, description="配色偏好")
    emphasis_areas: List[str] = Field(default_factory=list, description="需要重点优化的方面")
    constraints: List[str] = Field(default_factory=list, description="约束条件")
```

### 3.3 修改追踪记录 (ChangeTrackingReport)

```python
class ChangeTrackingReport(BaseModel):
    """修改追踪报告"""
    ppt_id: str
    generation_timestamp: datetime

    # 总体统计
    total_changes: int
    slides_modified: List[int]

    # 详细修改记录
    changes: List[ChangeRecord]

    # 修改分类统计
    change_summary: ChangeSummary


class ChangeRecord(BaseModel):
    """单个修改记录"""
    change_id: str = Field(default_factory=lambda: f"chg_{uuid.uuid4().hex[:8]}")
    slide_index: int
    change_type: str = Field(description="修改类型：content/layout/style/structure")
    dimension: str = Field(description="维度：content/logic/layout/color/font/chart")

    # 修改内容
    element: str = Field(description="修改元素：title/body/image/chart/background")
    before: str = Field(description="修改前")
    after: str = Field(description="修改后")

    # 修改原因
    reason: str = Field(description="修改原因")
    source: str = Field(description="来源：content_analysis/model_suggestion/user_request")

    # 影响评估
    impact_level: str = Field(description="影响程度：major/moderate/minor")


class ChangeSummary(BaseModel):
    """修改汇总统计"""
    by_type: Dict[str, int] = Field(default_factory=dict)
    by_dimension: Dict[str, int] = Field(default_factory=dict)
    by_source: Dict[str, int] = Field(default_factory=dict)
    by_impact: Dict[str, int] = Field(default_factory=dict)
```

## 4. API接口设计

### 4.1 新增API端点

#### 4.1.1 获取内容分析结果
```
GET /api/content-analysis/{ppt_id}

Response:
{
  "ppt_id": "ppt_xxx",
  "status": "waiting_user_review",
  "analysis": ContentAnalysisResult,
  "message": "内容分析已完成，请审查优化建议"
}
```

#### 4.1.2 提交用户编辑
```
POST /api/submit-edits/{ppt_id}

Request Body:
{
  "modified_opportunities": [...],
  "additional_instructions": "...",
  "preferences": {...}
}

Response:
{
  "ppt_id": "ppt_xxx",
  "status": "optimizing",
  "message": "已接收您的修改，开始执行优化..."
}
```

#### 4.1.3 获取修改追踪报告
```
GET /api/change-report/{ppt_id}

Response:
{
  "ppt_id": "ppt_xxx",
  "report": ChangeTrackingReport
}
```

#### 4.1.4 跳过审查（使用默认建议）
```
POST /api/skip-review/{ppt_id}

Response:
{
  "ppt_id": "ppt_xxx",
  "status": "optimizing",
  "message": "使用默认优化建议，开始执行优化..."
}
```

### 4.2 修改现有API

#### 4.2.1 状态查询API扩展
```
GET /api/status/{ppt_id}

Response（新增字段）:
{
  "ppt_id": "ppt_xxx",
  "status": "waiting_user_review",  # 新增状态
  "progress": 40,
  "current_step": "等待用户审查分析结果",
  "message": "...",
  "requires_user_action": true,      # 新增：是否需要用户操作
  "action_url": "/api/content-analysis/ppt_xxx"  # 新增：操作URL
}
```

## 5. 服务实现设计

### 5.1 ContentAnalyzer服务

```python
# backend/app/services/content_analyzer.py

class ContentAnalyzer:
    """内容分析服务 - 使用大模型进行深度内容分析"""

    def __init__(self, config: Dict):
        # 使用现有最强模型或指定模型进行分析
        self.analyzer_model = self._select_analyzer_model(config)

    async def analyze_content(
        self,
        ppt_data: PPTParseResult
    ) -> ContentAnalysisResult:
        """执行内容分析"""

        # 1. 构建分析提示词
        prompt = self._build_analysis_prompt(ppt_data)

        # 2. 调用大模型
        raw_response = await self._call_model(prompt)

        # 3. 解析响应
        analysis_result = self._parse_analysis_response(
            raw_response,
            ppt_data.ppt_id
        )

        # 4. 后处理和验证
        analysis_result = self._post_process(analysis_result, ppt_data)

        return analysis_result

    def _build_analysis_prompt(self, ppt_data: PPTParseResult) -> str:
        """构建内容分析提示词"""
        # 详细的提示词工程
        pass

    async def _call_model(self, prompt: str) -> Dict:
        """调用大模型API"""
        pass

    def _parse_analysis_response(
        self,
        response: Dict,
        ppt_id: str
    ) -> ContentAnalysisResult:
        """解析模型响应为结构化数据"""
        pass
```

### 5.2 OptimizationOrchestrator服务

```python
# backend/app/services/optimization_orchestrator.py

class OptimizationOrchestrator:
    """优化编排服务 - 协调内容分析和模型优化"""

    def __init__(self, config: Dict):
        self.content_analyzer = ContentAnalyzer(config)
        self.model_engine = ModelEngine(config)
        self.iteration_corrector = IterationCorrector(config)
        self.ppt_generator = PPTGenerator()
        self.change_tracker = ChangeTracker()

    async def execute_phase1_analysis(
        self,
        ppt_data: PPTParseResult
    ) -> ContentAnalysisResult:
        """执行第一阶段：内容分析"""
        return await self.content_analyzer.analyze_content(ppt_data)

    async def execute_phase2_optimization(
        self,
        ppt_data: PPTParseResult,
        user_edits: UserEditRequest,
        content_analysis: ContentAnalysisResult
    ) -> Tuple[PPTGenerateResult, ChangeTrackingReport]:
        """执行第二阶段：基于用户编辑的优化"""

        # 1. 将内容分析和用户编辑转换为优化指令
        optimization_guidance = self._build_optimization_guidance(
            content_analysis,
            user_edits
        )

        # 2. 调用多模型引擎（传入优化指引）
        model_suggestions = await self.model_engine.analyze_ppt_parallel(
            ppt_data,
            guidance=optimization_guidance  # 新增参数
        )

        # 3. 迭代修正
        final_plan = await self.iteration_corrector.process(
            ppt_data.ppt_id,
            model_suggestions
        )

        # 4. 生成PPT（同时追踪修改）
        generate_result = await self.ppt_generator.generate(
            ppt_data,
            final_plan,
            track_changes=True  # 新增参数
        )

        # 5. 生成修改追踪报告
        change_report = self.change_tracker.generate_report(
            ppt_data,
            content_analysis,
            user_edits,
            final_plan,
            generate_result
        )

        return generate_result, change_report
```

### 5.3 ChangeTracker服务

```python
# backend/app/services/change_tracker.py

class ChangeTracker:
    """修改追踪服务"""

    def generate_report(
        self,
        original_ppt: PPTParseResult,
        content_analysis: ContentAnalysisResult,
        user_edits: UserEditRequest,
        optimization_plan: FinalOptimizationPlan,
        generate_result: PPTGenerateResult
    ) -> ChangeTrackingReport:
        """生成详细的修改追踪报告"""

        changes = []

        # 1. 从优化计划中提取修改
        for suggestion in optimization_plan.suggestions:
            change = self._suggestion_to_change(
                suggestion,
                original_ppt,
                source="model_suggestion"
            )
            changes.append(change)

        # 2. 关联用户请求的修改
        for opp in user_edits.modified_opportunities:
            if opp.user_modified:
                # 标记来源为用户请求
                pass

        # 3. 生成统计汇总
        summary = self._generate_summary(changes)

        return ChangeTrackingReport(
            ppt_id=original_ppt.ppt_id,
            generation_timestamp=datetime.now(),
            total_changes=len(changes),
            slides_modified=list(set(c.slide_index for c in changes)),
            changes=changes,
            change_summary=summary
        )
```

## 6. 前端设计

### 6.1 新增页面流程

```
Step 1: 上传PPT
   ↓
Step 2: 内容分析中（进度条0-40%）
   ↓
Step 3: 审查分析结果【新增】
   ├─ 整体分析卡片
   ├─ 每页分析列表
   ├─ 优化建议列表（可编辑）
   └─ 操作按钮：[应用所有建议] [跳过审查]
   ↓
Step 4: 优化执行中（进度条40-100%）
   ↓
Step 5: 查看结果
   ├─ 原有：模型建议、最终方案
   ├─ 新增：修改追踪报告
   └─ 操作按钮：[下载PPT] [下载修改报告]
```

### 6.2 主要Vue组件设计

```
Home.vue（修改）
├── UploadStep（保持不变）
├── AnalysisStep（新增）
│   ├── OverallAnalysisCard
│   ├── SlideAnalysisList
│   └── OptimizationOpportunityEditor
├── ProcessingStep（保持不变）
└── ResultStep（扩展）
    ├── ModelSuggestionsTab
    ├── FinalPlanTab
    └── ChangeReportTab（新增）
```

## 7. 实现步骤

### 阶段1：后端核心服务（第1-2天）
1. 添加新数据模型到 `schemas.py`
2. 实现 `ContentAnalyzer` 服务
3. 实现 `ChangeTracker` 服务
4. 实现 `OptimizationOrchestrator` 编排服务

### 阶段2：API接口（第3天）
5. 添加新API端点到 `routes.py`
6. 修改现有API支持新状态
7. 更新任务状态管理

### 阶段3：前端界面（第4-5天）
8. 创建分析结果审查组件
9. 创建优化建议编辑器
10. 创建修改追踪报告展示组件
11. 更新主页面流程

### 阶段4：集成测试（第6天）
12. 端到端流程测试
13. 边界情况处理
14. 性能优化

## 8. 技术要点

### 8.1 提示词工程
内容分析提示词需要：
- 清晰的输出格式要求（JSON Schema）
- 丰富的示例（Few-shot）
- 明确的评分标准
- 分步推理引导

### 8.2 状态管理
- 使用状态机管理复杂流程
- 支持状态回退（用户可返回编辑）
- 持久化中间结果

### 8.3 性能优化
- 内容分析结果缓存
- 前端轮询优化（根据状态调整频率）
- 大文件处理优化

## 9. 配置扩展

```yaml
# config/config.yaml 新增配置

content_analysis:
  enabled: true
  analyzer_model: "qianwen"  # 使用通义千问进行内容分析
  timeout: 60
  max_retries: 3

  analysis_depth: "comprehensive"  # comprehensive/standard/quick

  # 提示词模板
  prompt_template: "content_analysis_v1"

optimization_flow:
  require_user_review: true  # 是否强制用户审查
  auto_approve_timeout: 3600  # 自动批准超时（秒），-1表示永不自动批准

change_tracking:
  enabled: true
  detail_level: "detailed"  # detailed/summary
  export_formats: ["json", "markdown"]
```

## 10. 预期效果

### 用户体验改进
1. ✅ 更透明的优化过程
2. ✅ 用户可控的优化方向
3. ✅ 清晰的修改追踪
4. ✅ 更符合用户意图的结果

### 系统能力提升
1. ✅ 更深入的内容理解
2. ✅ 更有针对性的优化
3. ✅ 更好的可解释性
4. ✅ 更高的用户满意度
