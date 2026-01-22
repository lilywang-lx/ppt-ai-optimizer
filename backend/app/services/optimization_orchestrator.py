"""
优化编排服务
协调内容分析、用户编辑和模型优化的整个流程
"""
import asyncio
from typing import Dict, Any, Tuple, List
from datetime import datetime
from loguru import logger

from app.models.schemas import (
    PPTParseResult,
    ContentAnalysisResult,
    UserEditRequest,
    FinalOptimizationPlan,
    PPTGenerateResult,
    ChangeTrackingReport,
    OptimizationOpportunity,
    ModelSuggestion,
    OptimizationSuggestion,
    OptimizationDimension,
    Priority
)
from app.services.content_analyzer import ContentAnalyzer
from app.services.model_engine import ModelEngine
from app.services.iteration_corrector import IterationCorrector
from app.services.ppt_generator import PPTGenerator
from app.services.change_tracker import ChangeTracker
from app.core.config import IterationConfig, ConflictResolutionConfig


class OptimizationOrchestrator:
    """优化编排器 - 协调两阶段优化流程"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化优化编排器

        Args:
            config: 系统配置
        """
        self.config = config

        # 从配置字典创建配置对象
        iteration_config = IterationConfig(**config.get('iteration', {}))
        conflict_config = ConflictResolutionConfig(**config.get('conflict_resolution', {}))

        # 初始化各个服务
        self.content_analyzer = ContentAnalyzer(config)
        self.model_engine = ModelEngine(config)
        self.iteration_corrector = IterationCorrector(iteration_config, conflict_config)
        self.ppt_generator = PPTGenerator()
        self.change_tracker = ChangeTracker()

        logger.info("优化编排器初始化完成")

    async def execute_phase1_analysis(
        self,
        ppt_data: PPTParseResult
    ) -> ContentAnalysisResult:
        """
        执行第一阶段：内容分析

        Args:
            ppt_data: PPT解析结果

        Returns:
            ContentAnalysisResult: 内容分析结果
        """
        logger.info(f"执行第一阶段 - 内容分析: {ppt_data.ppt_id}")

        try:
            # 调用内容分析器
            analysis_result = await self.content_analyzer.analyze_content(ppt_data)

            logger.info(
                f"第一阶段完成: {ppt_data.ppt_id}, "
                f"识别 {len(analysis_result.optimization_opportunities)} 个优化机会"
            )

            return analysis_result

        except Exception as e:
            logger.error(f"第一阶段执行失败: {ppt_data.ppt_id}, 错误: {str(e)}")
            raise

    async def execute_phase2_optimization(
        self,
        original_ppt_path: str,
        ppt_data: PPTParseResult,
        user_edits: UserEditRequest,
        content_analysis: ContentAnalysisResult
    ) -> Tuple[PPTGenerateResult, ChangeTrackingReport]:
        """
        执行第二阶段：基于用户编辑的优化

        Args:
            original_ppt_path: 原始PPT文件路径
            ppt_data: PPT解析结果
            user_edits: 用户编辑请求
            content_analysis: 内容分析结果

        Returns:
            Tuple[PPTGenerateResult, ChangeTrackingReport]: PPT生成结果和修改追踪报告
        """
        logger.info(f"执行第二阶段 - 模型优化: {ppt_data.ppt_id}")

        try:
            # 1. 将用户批准的优化机会转换为优化建议
            optimization_suggestions = self._convert_opportunities_to_suggestions(
                user_edits.modified_opportunities,
                content_analysis
            )
            logger.info(f"转换了 {len(optimization_suggestions)} 条优化建议")

            # 2. 创建模拟的FinalOptimizationPlan（跳过模型分析和迭代修正）
            final_plan = FinalOptimizationPlan(
                ppt_id=ppt_data.ppt_id,
                suggestions=optimization_suggestions,
                iteration_history=[],
                conflicts=[],
                resolutions=[],
                conflict_rate=0.0,
                metadata={
                    "source": "user_approved_opportunities",
                    "user_preferences": user_edits.preferences.dict() if user_edits.preferences else {},
                    "additional_instructions": user_edits.additional_instructions
                }
            )

            # 3. 生成PPT
            generate_result = await self.ppt_generator.generate(
                original_ppt_path,
                ppt_data,
                final_plan
            )
            logger.info(f"PPT生成完成: {generate_result.output_filename}")

            # 4. 生成修改追踪报告
            change_report = self.change_tracker.generate_report(
                ppt_data,
                content_analysis,
                user_edits,
                final_plan,
                generate_result
            )
            logger.info(f"修改追踪报告生成完成，总修改数: {change_report.total_changes}")

            logger.info(f"第二阶段完成: {ppt_data.ppt_id}")

            return generate_result, change_report

        except Exception as e:
            logger.error(f"第二阶段执行失败: {ppt_data.ppt_id}, 错误: {str(e)}")
            raise

    def _convert_opportunities_to_suggestions(
        self,
        opportunities: List[OptimizationOpportunity],
        content_analysis: ContentAnalysisResult
    ) -> List[OptimizationSuggestion]:
        """
        将优化机会转换为优化建议

        Args:
            opportunities: 优化机会列表
            content_analysis: 内容分析结果

        Returns:
            List[OptimizationSuggestion]: 优化建议列表
        """
        suggestions = []

        for opp in opportunities:
            # 只处理用户批准的优化机会
            if not opp.user_approved:
                continue

            # 根据优化机会的scope和slide_indices创建建议
            if opp.scope == "slide":
                # 为每个相关页面创建建议
                for slide_idx in opp.slide_indices:
                    suggestion = self._create_suggestion_from_opportunity(
                        opp, slide_idx, content_analysis
                    )
                    suggestions.append(suggestion)
            elif opp.scope == "section":
                # 为章节中的每个页面创建建议
                for slide_idx in opp.slide_indices:
                    suggestion = self._create_suggestion_from_opportunity(
                        opp, slide_idx, content_analysis
                    )
                    suggestions.append(suggestion)
            elif opp.scope == "overall":
                # 整体优化，为所有页面创建建议（或只为标题页）
                # 这里简化处理，只为第一页创建建议
                if len(content_analysis.slide_analyses) > 0:
                    suggestion = self._create_suggestion_from_opportunity(
                        opp, 0, content_analysis
                    )
                    suggestions.append(suggestion)

        return suggestions

    def _create_suggestion_from_opportunity(
        self,
        opp: OptimizationOpportunity,
        slide_idx: int,
        content_analysis: ContentAnalysisResult
    ) -> OptimizationSuggestion:
        """
        从优化机会创建优化建议

        Args:
            opp: 优化机会
            slide_idx: 页面索引
            content_analysis: 内容分析

        Returns:
            OptimizationSuggestion: 优化建议
        """
        # 映射category到dimension
        category_to_dimension = {
            "content": OptimizationDimension.CONTENT,
            "structure": OptimizationDimension.LAYOUT,
            "logic": OptimizationDimension.LOGIC,
            "presentation": OptimizationDimension.LAYOUT
        }

        dimension = category_to_dimension.get(
            opp.category,
            OptimizationDimension.CONTENT
        )

        # 映射priority到Priority枚举
        priority_map = {
            "high": Priority.MUST,
            "medium": Priority.RECOMMEND,
            "low": Priority.OPTIONAL
        }

        priority = priority_map.get(opp.priority, Priority.RECOMMEND)

        # 获取原始内容
        original_content = opp.current_state
        if slide_idx < len(content_analysis.slide_analyses):
            slide_analysis = content_analysis.slide_analyses[slide_idx]
            if slide_analysis.main_points:
                original_content = "; ".join(slide_analysis.main_points[:2])

        # 构建建议理由
        reason = opp.description
        if opp.expected_benefit:
            reason += f" 预期收益: {opp.expected_benefit}"
        if opp.user_modified and opp.user_comment:
            reason += f" (用户备注: {opp.user_comment})"

        suggestion = OptimizationSuggestion(
            slide_index=slide_idx,
            optimization_dimension=dimension,
            original_content=original_content,
            suggestion=opp.suggested_action,
            reason=reason,
            priority=priority
        )

        return suggestion

    def _build_optimization_guidance(
        self,
        content_analysis: ContentAnalysisResult,
        user_edits: UserEditRequest
    ) -> Dict[str, Any]:
        """
        构建优化指引（将内容分析和用户编辑转换为模型引擎可理解的格式）

        Args:
            content_analysis: 内容分析结果
            user_edits: 用户编辑

        Returns:
            Dict: 优化指引
        """
        # 获取用户批准的优化机会
        approved_opportunities = [
            opp for opp in user_edits.modified_opportunities
            if opp.user_approved
        ]

        # 按优先级排序
        priority_order = {"high": 0, "medium": 1, "low": 2}
        approved_opportunities.sort(
            key=lambda x: (priority_order.get(x.priority, 1), -x.impact_score)
        )

        # 提取整体指导原则
        overall_guidance = {
            "theme": content_analysis.overall_analysis.theme,
            "target_audience": content_analysis.overall_analysis.target_audience,
            "presentation_goal": content_analysis.overall_analysis.presentation_goal,
            "key_points": content_analysis.overall_analysis.key_points,
            "overall_suggestions": content_analysis.overall_analysis.overall_suggestions
        }

        # 提取每页的问题和方向
        slide_guidance = {}
        for slide_analysis in content_analysis.slide_analyses:
            slide_guidance[slide_analysis.slide_index] = {
                "issues": [
                    {
                        "type": issue.issue_type,
                        "description": issue.description,
                        "severity": issue.severity
                    }
                    for issue in slide_analysis.issues
                ],
                "optimization_directions": slide_analysis.optimization_directions,
                "clarity_score": slide_analysis.clarity,
                "relevance_score": slide_analysis.relevance
            }

        # 用户偏好
        user_preferences = {}
        if user_edits.preferences:
            user_preferences = {
                "style": user_edits.preferences.style,
                "color_scheme": user_edits.preferences.color_scheme,
                "emphasis_areas": user_edits.preferences.emphasis_areas,
                "constraints": user_edits.preferences.constraints
            }

        # 构建指引字典
        guidance = {
            "approved_opportunities": [
                {
                    "opportunity_id": opp.opportunity_id,
                    "scope": opp.scope,
                    "slide_indices": opp.slide_indices,
                    "category": opp.category,
                    "title": opp.title,
                    "description": opp.description,
                    "suggested_action": opp.suggested_action,
                    "priority": opp.priority,
                    "impact_score": opp.impact_score,
                    "user_modified": opp.user_modified,
                    "user_comment": opp.user_comment
                }
                for opp in approved_opportunities
            ],
            "overall_guidance": overall_guidance,
            "slide_guidance": slide_guidance,
            "user_preferences": user_preferences,
            "additional_instructions": user_edits.additional_instructions
        }

        return guidance

    def create_default_user_edits(
        self,
        content_analysis: ContentAnalysisResult
    ) -> UserEditRequest:
        """
        创建默认的用户编辑（当用户跳过审查时使用）

        Args:
            content_analysis: 内容分析结果

        Returns:
            UserEditRequest: 默认用户编辑请求
        """
        # 默认批准所有高优先级和中优先级的优化机会
        modified_opportunities = []

        for opp in content_analysis.optimization_opportunities:
            # 只自动批准高优先级和中优先级
            if opp.priority in ["high", "medium"]:
                opp.user_approved = True
                opp.user_modified = False
                modified_opportunities.append(opp)
            else:
                # 低优先级默认不批准
                opp.user_approved = False
                modified_opportunities.append(opp)

        default_edits = UserEditRequest(
            ppt_id=content_analysis.ppt_id,
            modified_opportunities=modified_opportunities,
            additional_instructions="使用默认优化建议",
            preferences=None
        )

        logger.info(
            f"创建默认编辑: {content_analysis.ppt_id}, "
            f"批准 {sum(1 for o in modified_opportunities if o.user_approved)} 个优化机会"
        )

        return default_edits
