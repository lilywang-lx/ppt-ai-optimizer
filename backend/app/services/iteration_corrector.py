"""
跨模型建议迭代修正器 - 核心强化模块
实现多模型建议的迭代修正、冲突检测与调和
"""
import json
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from loguru import logger

from app.models.schemas import (
    ModelSuggestion,
    OptimizationSuggestion,
    FinalOptimizationPlan,
    Conflict,
    ConflictResolution,
    ConflictType,
    IterationResult,
    CorrectionRecord,
    CorrectionAction,
    OptimizationDimension
)
from app.core.config import IterationConfig, ConflictResolutionConfig


class IterationCorrector:
    """迭代修正器类"""

    def __init__(
        self,
        iteration_config: IterationConfig,
        conflict_config: ConflictResolutionConfig
    ):
        """
        初始化迭代修正器

        Args:
            iteration_config: 迭代配置
            conflict_config: 冲突调和配置
        """
        self.config = iteration_config
        self.conflict_config = conflict_config
        logger.info("迭代修正器初始化完成")

    async def process(
        self,
        ppt_id: str,
        model_suggestions: List[ModelSuggestion]
    ) -> FinalOptimizationPlan:
        """
        处理模型建议,执行迭代修正

        Args:
            ppt_id: PPT ID
            model_suggestions: 原始模型建议列表

        Returns:
            FinalOptimizationPlan: 最终优化方案
        """
        logger.info(f"开始迭代修正流程: {ppt_id}")

        # 如果未启用迭代修正,直接合并所有建议
        if not self.config.enabled:
            return self._merge_without_iteration(ppt_id, model_suggestions)

        # 执行迭代修正
        iteration_history = []
        current_suggestions = model_suggestions

        for round_num in range(self.config.max_rounds):
            logger.info(f"开始第 {round_num + 1} 轮迭代修正")

            # 检测冲突
            conflicts = self._detect_conflicts(current_suggestions)
            conflict_rate = self._calculate_conflict_rate(conflicts, current_suggestions)

            logger.info(f"第 {round_num + 1} 轮冲突率: {conflict_rate:.2%}")

            # 判断是否需要继续迭代
            if conflict_rate < self.config.conflict_threshold:
                logger.info(f"冲突率低于阈值 {self.config.conflict_threshold},停止迭代")
                break

            # 执行修正 (这里简化处理,实际应该调用模型API进行修正)
            # 在生产环境中,这里应该按照workflow配置依次调用模型进行修正
            iteration_history.append(IterationResult(
                round=round_num + 1,
                model_name="iteration_processor",
                suggestions=self._flatten_suggestions(current_suggestions),
                corrections=[]
            ))

        # 检测最终冲突
        final_conflicts = self._detect_conflicts(current_suggestions)
        conflict_rate = self._calculate_conflict_rate(final_conflicts, current_suggestions)

        # 调和冲突
        resolutions = self._resolve_conflicts(final_conflicts, current_suggestions)

        # 生成最终方案
        final_suggestions = self._generate_final_suggestions(
            current_suggestions,
            resolutions
        )

        plan = FinalOptimizationPlan(
            ppt_id=ppt_id,
            suggestions=final_suggestions,
            iteration_history=iteration_history,
            conflicts=final_conflicts,
            resolutions=resolutions,
            conflict_rate=conflict_rate,
            metadata={
                "total_iterations": len(iteration_history),
                "model_count": len(model_suggestions)
            }
        )

        logger.info(f"迭代修正完成: {ppt_id}, 最终建议数: {len(final_suggestions)}, 冲突率: {conflict_rate:.2%}")
        return plan

    def _detect_conflicts(self, suggestions: List[ModelSuggestion]) -> List[Conflict]:
        """
        检测模型建议之间的冲突

        Args:
            suggestions: 模型建议列表

        Returns:
            List[Conflict]: 冲突列表
        """
        conflicts = []

        # 按 (slide_index, dimension) 分组建议
        grouped: Dict[Tuple[int, OptimizationDimension], List[Tuple[str, OptimizationSuggestion]]] = defaultdict(list)

        for model_sug in suggestions:
            for sug in model_sug.optimization_suggestions:
                key = (sug.slide_index, sug.optimization_dimension)
                grouped[key].append((model_sug.model_name, sug))

        # 检查每组是否有冲突
        for (slide_idx, dimension), group_suggestions in grouped.items():
            if len(group_suggestions) <= 1:
                continue  # 只有一个建议,无冲突

            # 检查建议是否冲突
            suggestions_list = [s for _, s in group_suggestions]
            if self._has_conflict(suggestions_list):
                conflict = Conflict(
                    slide_index=slide_idx,
                    dimension=dimension,
                    conflict_type=ConflictType.DIRECT,
                    conflicting_suggestions=suggestions_list,
                    description=f"第{slide_idx+1}页的{dimension}维度存在{len(suggestions_list)}个不同建议"
                )
                conflicts.append(conflict)

        return conflicts

    def _has_conflict(self, suggestions: List[OptimizationSuggestion]) -> bool:
        """
        判断多个建议是否冲突

        简单实现: 如果建议内容差异较大则认为冲突
        """
        if len(suggestions) <= 1:
            return False

        # 提取所有建议内容
        contents = [s.suggestion.lower() for s in suggestions]

        # 简单判断: 如果内容完全不同则认为冲突
        # 在实际应用中,这里应该使用更复杂的语义相似度比较
        unique_contents = set(contents)
        return len(unique_contents) > 1

    def _calculate_conflict_rate(
        self,
        conflicts: List[Conflict],
        suggestions: List[ModelSuggestion]
    ) -> float:
        """
        计算冲突率

        冲突率 = 冲突建议条数 / 总建议条数
        """
        if not conflicts:
            return 0.0

        # 统计冲突涉及的建议总数
        conflict_count = sum(len(c.conflicting_suggestions) for c in conflicts)

        # 统计总建议数
        total_count = sum(len(s.optimization_suggestions) for s in suggestions)

        if total_count == 0:
            return 0.0

        return conflict_count / total_count

    def _resolve_conflicts(
        self,
        conflicts: List[Conflict],
        suggestions: List[ModelSuggestion]
    ) -> List[ConflictResolution]:
        """
        调和冲突

        Args:
            conflicts: 冲突列表
            suggestions: 模型建议

        Returns:
            List[ConflictResolution]: 调和结果列表
        """
        resolutions = []

        for conflict in conflicts:
            # 尝试按规则调和
            resolution = self._resolve_by_rules(conflict)

            if resolution is None:
                # 规则无法调和,使用模型仲裁
                resolution = self._resolve_by_arbiter(conflict)

            resolutions.append(resolution)

        return resolutions

    def _resolve_by_rules(self, conflict: Conflict) -> ConflictResolution:
        """
        按预设规则调和冲突

        Args:
            conflict: 冲突信息

        Returns:
            ConflictResolution: 调和结果
        """
        dimension_str = conflict.dimension.value
        rules = self.conflict_config.rules.get(dimension_str, {})

        if not rules:
            return None

        # 简单实现: 选择优先级最高的建议
        priority_order = {"must": 3, "recommend": 2, "optional": 1}
        best_suggestion = max(
            conflict.conflicting_suggestions,
            key=lambda s: priority_order.get(s.priority.value, 0)
        )

        return ConflictResolution(
            conflict=conflict,
            resolution_method="rule",
            selected_suggestion=best_suggestion,
            reason=f"根据{dimension_str}维度的优先级规则选择"
        )

    def _resolve_by_arbiter(self, conflict: Conflict) -> ConflictResolution:
        """
        使用仲裁模型调和冲突

        在实际应用中,这里应该调用仲裁模型API
        这里简化为选择第一个must优先级的建议,或随机选择
        """
        # 优先选择must级别的建议
        must_suggestions = [
            s for s in conflict.conflicting_suggestions
            if s.priority.value == "must"
        ]

        if must_suggestions:
            selected = must_suggestions[0]
            reason = "选择must优先级建议"
        else:
            # 选择第一个建议
            selected = conflict.conflicting_suggestions[0]
            reason = "由仲裁模型选择的最优建议"

        return ConflictResolution(
            conflict=conflict,
            resolution_method="model_arbiter",
            selected_suggestion=selected,
            reason=reason
        )

    def _generate_final_suggestions(
        self,
        model_suggestions: List[ModelSuggestion],
        resolutions: List[ConflictResolution]
    ) -> List[OptimizationSuggestion]:
        """
        生成最终优化建议

        Args:
            model_suggestions: 模型建议
            resolutions: 冲突调和结果

        Returns:
            List[OptimizationSuggestion]: 最终建议列表
        """
        # 收集所有建议
        all_suggestions = {}  # key: (slide_index, dimension), value: suggestion

        for model_sug in model_suggestions:
            for sug in model_sug.optimization_suggestions:
                key = (sug.slide_index, sug.optimization_dimension)
                all_suggestions[key] = sug

        # 应用冲突调和结果
        for resolution in resolutions:
            conflict = resolution.conflict
            key = (conflict.slide_index, conflict.dimension)
            all_suggestions[key] = resolution.selected_suggestion

        # 转换为列表并排序
        final = list(all_suggestions.values())
        final.sort(key=lambda s: (s.slide_index, s.optimization_dimension.value))

        return final

    def _merge_without_iteration(
        self,
        ppt_id: str,
        model_suggestions: List[ModelSuggestion]
    ) -> FinalOptimizationPlan:
        """
        不进行迭代修正,直接合并所有建议

        Args:
            ppt_id: PPT ID
            model_suggestions: 模型建议列表

        Returns:
            FinalOptimizationPlan: 最终方案
        """
        all_suggestions = []
        for model_sug in model_suggestions:
            all_suggestions.extend(model_sug.optimization_suggestions)

        return FinalOptimizationPlan(
            ppt_id=ppt_id,
            suggestions=all_suggestions,
            iteration_history=[],
            conflicts=[],
            resolutions=[],
            conflict_rate=0.0,
            metadata={"iteration_enabled": False}
        )

    def _flatten_suggestions(
        self,
        model_suggestions: List[ModelSuggestion]
    ) -> List[OptimizationSuggestion]:
        """展平模型建议为建议列表"""
        result = []
        for ms in model_suggestions:
            result.extend(ms.optimization_suggestions)
        return result
