"""
数据模型定义
定义系统中使用的标准化数据结构
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class OptimizationDimension(str, Enum):
    """优化维度枚举"""
    CONTENT = "content"  # 内容
    LOGIC = "logic"  # 逻辑
    LAYOUT = "layout"  # 排版
    COLOR = "color"  # 配色
    FONT = "font"  # 字体
    CHART = "chart"  # 图表


class Priority(str, Enum):
    """优先级枚举"""
    MUST = "must"  # 必须
    RECOMMEND = "recommend"  # 推荐
    OPTIONAL = "optional"  # 可选


class SlideType(str, Enum):
    """幻灯片类型"""
    TITLE = "title"  # 标题页
    CONTENT = "content"  # 内容页
    CHART = "chart"  # 图表页
    IMAGE = "image"  # 图片页
    MIXED = "mixed"  # 混合页


class ProcessStatus(str, Enum):
    """处理状态"""
    PENDING = "pending"  # 等待中
    PARSING = "parsing"  # 解析中
    CONTENT_ANALYZING = "content_analyzing"  # 内容分析中
    WAITING_USER_REVIEW = "waiting_user_review"  # 等待用户审查
    USER_EDITING = "user_editing"  # 用户编辑中
    OPTIMIZING = "optimizing"  # 优化执行中
    ANALYZING = "analyzing"  # 模型分析中
    CORRECTING = "correcting"  # 修正中
    GENERATING = "generating"  # 生成中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败


class LayoutInfo(BaseModel):
    """版式信息"""
    layout_type: str
    width: float
    height: float
    placeholders: List[Dict[str, Any]] = []


class StyleInfo(BaseModel):
    """样式信息"""
    font_name: Optional[str] = None
    font_size: Optional[float] = None
    font_color: Optional[str] = None
    background_color: Optional[str] = None
    alignment: Optional[str] = None


class SlideData(BaseModel):
    """单页幻灯片数据"""
    slide_id: int
    slide_index: int
    slide_type: SlideType
    content: str
    layout_info: LayoutInfo
    style_info: StyleInfo
    images: List[Dict[str, Any]] = []
    charts: List[Dict[str, Any]] = []


class PPTParseResult(BaseModel):
    """PPT解析结果"""
    ppt_id: str
    filename: str
    total_slides: int
    slides: List[SlideData]
    theme: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}
    parse_time: datetime = Field(default_factory=datetime.now)


class OptimizationSuggestion(BaseModel):
    """单条优化建议"""
    slide_index: int
    optimization_dimension: OptimizationDimension
    original_content: str
    suggestion: str
    reason: str
    priority: Priority


class ModelSuggestion(BaseModel):
    """单个模型的优化建议(标准化格式)"""
    ppt_id: str
    model_name: str
    optimization_suggestions: List[OptimizationSuggestion]
    core_strength: str
    timestamp: datetime = Field(default_factory=datetime.now)


class CorrectionAction(str, Enum):
    """修正动作"""
    KEEP = "keep"  # 保留
    MODIFY = "modify"  # 修正
    ADD = "add"  # 补充
    REMOVE = "remove"  # 删除


class CorrectionRecord(BaseModel):
    """修正记录"""
    action: CorrectionAction
    original_suggestion: Optional[OptimizationSuggestion] = None
    new_suggestion: Optional[OptimizationSuggestion] = None
    reason: str
    corrector_model: str


class IterationResult(BaseModel):
    """单轮迭代结果"""
    round: int
    model_name: str
    suggestions: List[OptimizationSuggestion]
    corrections: List[CorrectionRecord] = []
    timestamp: datetime = Field(default_factory=datetime.now)


class ConflictType(str, Enum):
    """冲突类型"""
    DIRECT = "direct"  # 直接冲突(完全矛盾)
    PARTIAL = "partial"  # 部分冲突(部分矛盾)


class Conflict(BaseModel):
    """冲突信息"""
    slide_index: int
    dimension: OptimizationDimension
    conflict_type: ConflictType
    conflicting_suggestions: List[OptimizationSuggestion]
    description: str


class ConflictResolution(BaseModel):
    """冲突调和结果"""
    conflict: Conflict
    resolution_method: str  # "rule" / "model_arbiter" / "manual"
    selected_suggestion: OptimizationSuggestion
    reason: str


class FinalOptimizationPlan(BaseModel):
    """最终优化方案"""
    ppt_id: str
    suggestions: List[OptimizationSuggestion]
    iteration_history: List[IterationResult] = []
    conflicts: List[Conflict] = []
    resolutions: List[ConflictResolution] = []
    conflict_rate: float
    metadata: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.now)


class PPTGenerateResult(BaseModel):
    """PPT生成结果"""
    ppt_id: str
    output_filename: str
    output_path: str
    generation_method: str  # "api" / "library"
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class TaskProgress(BaseModel):
    """任务进度"""
    ppt_id: str
    status: ProcessStatus
    progress: float  # 0-100
    current_step: str
    message: str
    requires_user_action: bool = False  # 是否需要用户操作
    action_url: Optional[str] = None  # 操作URL
    timestamp: datetime = Field(default_factory=datetime.now)


# ============================================================================
# 内容分析相关数据模型
# ============================================================================

import uuid


class ContentIssue(BaseModel):
    """内容问题"""
    issue_type: str = Field(description="问题类型：redundant/unclear/missing/misplaced/inconsistent")
    description: str
    severity: str = Field(description="严重程度：critical/major/minor")
    location: Optional[str] = None


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
    issues: List[ContentIssue] = []

    # 优化方向
    optimization_directions: List[str] = []


class Section(BaseModel):
    """章节信息"""
    section_name: str
    slide_indices: List[int]
    purpose: str
    is_necessary: bool
    improvement_suggestion: Optional[str] = None


class OutlineStructure(BaseModel):
    """大纲结构分析"""
    sections: List[Section]
    structure_type: str = Field(description="结构类型：linear/parallel/circular/problem-solution")
    structure_quality: str = Field(description="结构质量：excellent/good/fair/poor")
    structure_issues: List[str] = Field(description="结构问题列表")


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


class OptimizationOpportunity(BaseModel):
    """优化机会点"""
    opportunity_id: str = Field(default_factory=lambda: f"opp_{uuid.uuid4().hex[:8]}")

    # 位置信息
    scope: str = Field(description="范围：overall/section/slide")
    slide_indices: List[int] = Field(description="涉及的页码（overall时为空）", default_factory=list)

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


class ContentAnalysisResult(BaseModel):
    """大模型内容分析结果"""
    ppt_id: str
    analysis_timestamp: datetime = Field(default_factory=datetime.now)

    # 整体分析
    overall_analysis: OverallAnalysis

    # 每页分析
    slide_analyses: List[SlideAnalysis]

    # 优化建议
    optimization_opportunities: List[OptimizationOpportunity]

    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# 用户编辑相关数据模型
# ============================================================================

class UserPreferences(BaseModel):
    """用户偏好设置"""
    style: Optional[str] = Field(None, description="风格偏好：professional/casual/academic/creative")
    color_scheme: Optional[str] = Field(None, description="配色偏好")
    emphasis_areas: List[str] = Field(default_factory=list, description="需要重点优化的方面")
    constraints: List[str] = Field(default_factory=list, description="约束条件")


class UserEditRequest(BaseModel):
    """用户编辑请求"""
    ppt_id: str

    # 用户修改的优化机会
    modified_opportunities: List[OptimizationOpportunity]

    # 用户添加的额外指令
    additional_instructions: Optional[str] = None

    # 用户偏好设置
    preferences: Optional[UserPreferences] = None


# ============================================================================
# 修改追踪相关数据模型
# ============================================================================

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


class ChangeTrackingReport(BaseModel):
    """修改追踪报告"""
    ppt_id: str
    generation_timestamp: datetime = Field(default_factory=datetime.now)

    # 总体统计
    total_changes: int
    slides_modified: List[int]

    # 详细修改记录
    changes: List[ChangeRecord]

    # 修改分类统计
    change_summary: ChangeSummary
