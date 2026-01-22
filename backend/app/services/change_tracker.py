"""
修改追踪服务
追踪PPT优化过程中的所有修改，生成详细的修改报告
"""
from typing import Dict, List, Any
from datetime import datetime
from loguru import logger
from collections import defaultdict

from app.models.schemas import (
    PPTParseResult,
    ContentAnalysisResult,
    UserEditRequest,
    FinalOptimizationPlan,
    PPTGenerateResult,
    ChangeTrackingReport,
    ChangeRecord,
    ChangeSummary,
    OptimizationSuggestion
)


class ChangeTracker:
    """修改追踪器 - 生成详细的修改追踪报告"""

    def __init__(self):
        """初始化修改追踪器"""
        pass

    def generate_report(
        self,
        original_ppt: PPTParseResult,
        content_analysis: ContentAnalysisResult,
        user_edits: UserEditRequest,
        optimization_plan: FinalOptimizationPlan,
        generate_result: PPTGenerateResult
    ) -> ChangeTrackingReport:
        """
        生成详细的修改追踪报告

        Args:
            original_ppt: 原始PPT数据
            content_analysis: 内容分析结果
            user_edits: 用户编辑请求
            optimization_plan: 最终优化方案
            generate_result: PPT生成结果

        Returns:
            ChangeTrackingReport: 修改追踪报告
        """
        logger.info(f"生成修改追踪报告: {original_ppt.ppt_id}")

        changes = []

        # 1. 从内容分析中提取的修改
        content_analysis_changes = self._extract_from_content_analysis(
            content_analysis,
            user_edits
        )
        changes.extend(content_analysis_changes)

        # 2. 从优化方案中提取的修改
        optimization_changes = self._extract_from_optimization_plan(
            optimization_plan,
            original_ppt
        )
        changes.extend(optimization_changes)

        # 3. 关联用户请求的修改
        changes = self._mark_user_requested_changes(changes, user_edits)

        # 4. 生成统计汇总
        summary = self._generate_summary(changes)

        # 5. 提取修改的页面列表
        slides_modified = list(set(c.slide_index for c in changes))
        slides_modified.sort()

        report = ChangeTrackingReport(
            ppt_id=original_ppt.ppt_id,
            generation_timestamp=datetime.now(),
            total_changes=len(changes),
            slides_modified=slides_modified,
            changes=changes,
            change_summary=summary
        )

        logger.info(
            f"修改报告生成完成: {original_ppt.ppt_id}, "
            f"总修改数: {len(changes)}, 涉及页面: {len(slides_modified)}"
        )

        return report

    def _extract_from_content_analysis(
        self,
        content_analysis: ContentAnalysisResult,
        user_edits: UserEditRequest
    ) -> List[ChangeRecord]:
        """
        从内容分析中提取修改记录

        Args:
            content_analysis: 内容分析结果
            user_edits: 用户编辑

        Returns:
            List[ChangeRecord]: 修改记录列表
        """
        changes = []

        # 从用户批准的优化机会中提取
        for opp in user_edits.modified_opportunities:
            if not opp.user_approved:
                continue  # 跳过未批准的

            # 根据优化机会创建修改记录
            for slide_idx in opp.slide_indices:
                change = ChangeRecord(
                    slide_index=slide_idx,
                    change_type=self._map_category_to_type(opp.category),
                    dimension=self._map_category_to_dimension(opp.category),
                    element=self._infer_element_from_category(opp.category),
                    before=opp.current_state,
                    after=opp.suggested_action,
                    reason=opp.description,
                    source="content_analysis" if not opp.user_modified else "user_request",
                    impact_level=self._map_priority_to_impact(opp.priority)
                )
                changes.append(change)

        return changes

    def _extract_from_optimization_plan(
        self,
        optimization_plan: FinalOptimizationPlan,
        original_ppt: PPTParseResult
    ) -> List[ChangeRecord]:
        """
        从优化方案中提取修改记录

        Args:
            optimization_plan: 最终优化方案
            original_ppt: 原始PPT数据

        Returns:
            List[ChangeRecord]: 修改记录列表
        """
        changes = []

        for suggestion in optimization_plan.suggestions:
            # 获取原始内容
            slide_idx = suggestion.slide_index
            if 0 <= slide_idx < len(original_ppt.slides):
                original_slide = original_ppt.slides[slide_idx]
                before_content = original_slide.content
            else:
                before_content = ""

            # 创建修改记录
            change = ChangeRecord(
                slide_index=suggestion.slide_index,
                change_type=self._dimension_to_type(suggestion.optimization_dimension.value),
                dimension=suggestion.optimization_dimension.value,
                element=self._infer_element_from_dimension(suggestion.optimization_dimension.value),
                before=suggestion.original_content or before_content[:100],
                after=suggestion.suggestion[:100],
                reason=suggestion.reason,
                source="model_suggestion",
                impact_level=self._priority_to_impact(suggestion.priority.value)
            )
            changes.append(change)

        return changes

    def _mark_user_requested_changes(
        self,
        changes: List[ChangeRecord],
        user_edits: UserEditRequest
    ) -> List[ChangeRecord]:
        """
        标记用户主动请求的修改

        Args:
            changes: 原始修改列表
            user_edits: 用户编辑

        Returns:
            List[ChangeRecord]: 更新后的修改列表
        """
        # 获取用户修改过的优化机会
        user_modified_opps = [
            opp for opp in user_edits.modified_opportunities
            if opp.user_modified
        ]

        # 标记相关的修改
        for change in changes:
            for opp in user_modified_opps:
                if change.slide_index in opp.slide_indices:
                    change.source = "user_request"
                    if opp.user_comment:
                        change.reason += f" (用户备注: {opp.user_comment})"

        return changes

    def _generate_summary(self, changes: List[ChangeRecord]) -> ChangeSummary:
        """
        生成修改汇总统计

        Args:
            changes: 修改记录列表

        Returns:
            ChangeSummary: 修改汇总
        """
        by_type = defaultdict(int)
        by_dimension = defaultdict(int)
        by_source = defaultdict(int)
        by_impact = defaultdict(int)

        for change in changes:
            by_type[change.change_type] += 1
            by_dimension[change.dimension] += 1
            by_source[change.source] += 1
            by_impact[change.impact_level] += 1

        return ChangeSummary(
            by_type=dict(by_type),
            by_dimension=dict(by_dimension),
            by_source=dict(by_source),
            by_impact=dict(by_impact)
        )

    # ============================================================================
    # 辅助映射方法
    # ============================================================================

    def _map_category_to_type(self, category: str) -> str:
        """映射类别到修改类型"""
        mapping = {
            "content": "content",
            "structure": "structure",
            "logic": "content",
            "presentation": "style"
        }
        return mapping.get(category, "content")

    def _map_category_to_dimension(self, category: str) -> str:
        """映射类别到维度"""
        mapping = {
            "content": "content",
            "structure": "layout",
            "logic": "logic",
            "presentation": "layout"
        }
        return mapping.get(category, "content")

    def _infer_element_from_category(self, category: str) -> str:
        """从类别推断元素"""
        mapping = {
            "content": "body",
            "structure": "layout",
            "logic": "body",
            "presentation": "layout"
        }
        return mapping.get(category, "body")

    def _map_priority_to_impact(self, priority: str) -> str:
        """映射优先级到影响程度"""
        mapping = {
            "high": "major",
            "medium": "moderate",
            "low": "minor"
        }
        return mapping.get(priority, "moderate")

    def _dimension_to_type(self, dimension: str) -> str:
        """维度到修改类型"""
        mapping = {
            "content": "content",
            "logic": "content",
            "layout": "layout",
            "color": "style",
            "font": "style",
            "chart": "content"
        }
        return mapping.get(dimension, "content")

    def _infer_element_from_dimension(self, dimension: str) -> str:
        """从维度推断元素"""
        mapping = {
            "content": "body",
            "logic": "body",
            "layout": "layout",
            "color": "background",
            "font": "title",
            "chart": "chart"
        }
        return mapping.get(dimension, "body")

    def _priority_to_impact(self, priority: str) -> str:
        """优先级到影响程度"""
        mapping = {
            "must": "major",
            "recommend": "moderate",
            "optional": "minor"
        }
        return mapping.get(priority, "moderate")
