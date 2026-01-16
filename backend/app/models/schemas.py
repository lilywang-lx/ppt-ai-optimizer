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
    ANALYZING = "analyzing"  # 分析中
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
    timestamp: datetime = Field(default_factory=datetime.now)
