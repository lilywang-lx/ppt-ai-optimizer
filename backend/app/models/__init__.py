"""数据模型模块"""
from .schemas import (
    OptimizationDimension,
    Priority,
    SlideType,
    ProcessStatus,
    SlideData,
    PPTParseResult,
    OptimizationSuggestion,
    ModelSuggestion,
    CorrectionRecord,
    IterationResult,
    Conflict,
    ConflictResolution,
    FinalOptimizationPlan,
    PPTGenerateResult,
    TaskProgress
)

__all__ = [
    'OptimizationDimension',
    'Priority',
    'SlideType',
    'ProcessStatus',
    'SlideData',
    'PPTParseResult',
    'OptimizationSuggestion',
    'ModelSuggestion',
    'CorrectionRecord',
    'IterationResult',
    'Conflict',
    'ConflictResolution',
    'FinalOptimizationPlan',
    'PPTGenerateResult',
    'TaskProgress'
]
