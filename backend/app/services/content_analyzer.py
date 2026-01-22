"""
内容分析服务
使用大模型进行深度内容分析，识别优化机会
"""
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.models.schemas import (
    PPTParseResult,
    ContentAnalysisResult,
    OverallAnalysis,
    OutlineStructure,
    Section,
    SlideAnalysis,
    ContentIssue,
    OptimizationOpportunity
)
from app.core.config import ModelConfig


class ContentAnalyzer:
    """内容分析器 - 使用大模型进行深度内容分析"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化内容分析器

        Args:
            config: 系统配置，包含模型配置
        """
        self.config = config

        # 选择分析模型（使用通义千问作为默认分析模型）
        analyzer_model_name = config.get("content_analysis", {}).get("analyzer_model", "qianwen")
        self.analyzer_model_config = config["models"].get(analyzer_model_name, {})

        if not self.analyzer_model_config.get("enabled", False):
            logger.warning(f"分析模型 {analyzer_model_name} 未启用，尝试使用第一个可用模型")
            # 寻找第一个启用的模型
            for model_name, model_config in config["models"].items():
                if model_config.get("enabled", False):
                    self.analyzer_model_config = model_config
                    analyzer_model_name = model_name
                    break

        self.analyzer_model_name = analyzer_model_name
        self.timeout = self.analyzer_model_config.get("timeout", 60)

        logger.info(f"内容分析器初始化完成，使用模型: {self.analyzer_model_name}")

    async def analyze_content(self, ppt_data: PPTParseResult) -> ContentAnalysisResult:
        """
        执行内容分析

        Args:
            ppt_data: PPT解析结果

        Returns:
            ContentAnalysisResult: 内容分析结果
        """
        logger.info(f"开始内容分析: {ppt_data.ppt_id}")

        try:
            # 1. 构建分析提示词
            prompt = self._build_analysis_prompt(ppt_data)
            logger.debug(f"分析提示词长度: {len(prompt)}")

            # 2. 调用大模型
            raw_response = await self._call_model(prompt)
            logger.debug(f"模型响应获取成功")

            # 3. 解析响应
            analysis_result = self._parse_analysis_response(raw_response, ppt_data.ppt_id)
            logger.info(f"内容分析完成: {ppt_data.ppt_id}, 识别 {len(analysis_result.optimization_opportunities)} 个优化机会")

            # 4. 后处理和验证
            analysis_result = self._post_process(analysis_result, ppt_data)

            return analysis_result

        except Exception as e:
            logger.error(f"内容分析失败: {ppt_data.ppt_id}, 错误: {str(e)}")
            # 返回一个基本的分析结果
            return self._create_fallback_analysis(ppt_data)

    def _build_analysis_prompt(self, ppt_data: PPTParseResult) -> str:
        """
        构建内容分析提示词

        Args:
            ppt_data: PPT解析结果

        Returns:
            str: 分析提示词
        """
        # 提取PPT内容摘要
        slides_summary = []
        for slide in ppt_data.slides:
            slide_summary = {
                "index": slide.slide_index,
                "type": slide.slide_type.value,
                "content": slide.content[:500] if slide.content else "",  # 限制长度
                "has_images": len(slide.images) > 0,
                "has_charts": len(slide.charts) > 0
            }
            slides_summary.append(slide_summary)

        prompt = f"""你是一位专业的PPT内容分析专家。请对以下PPT进行深度分析，并以JSON格式返回分析结果。

# PPT基本信息
- 文件名: {ppt_data.filename}
- 总页数: {ppt_data.total_slides}
- 主题: {ppt_data.theme.get('name', '未知')}

# 每页内容
{json.dumps(slides_summary, ensure_ascii=False, indent=2)}

# 分析任务
请从以下几个维度进行分析：

1. **整体分析** (overall_analysis)
   - 提取3-5个核心要点 (key_points)
   - 识别PPT主题 (theme)、目标受众 (target_audience)、演示目标 (presentation_goal)
   - 分析大纲结构 (outline_structure)
     * 将PPT划分为逻辑章节 (sections)
     * 评估结构类型 (structure_type): linear/parallel/circular/problem-solution
     * 评估结构质量 (structure_quality): excellent/good/fair/poor
     * 指出结构问题 (structure_issues)
   - 评分（0-10分）:
     * 内容连贯性 (content_coherence)
     * 逻辑流畅度 (logic_flow)
     * 内容完整性 (completeness)
   - 提供整体优化建议 (overall_suggestions)

2. **每页分析** (slide_analyses)
   对每一页提供:
   - 主要内容点 (main_points)
   - 清晰度评分 (clarity: 0-10)
   - 相关性评分 (relevance: 0-10)
   - 信息密度 (information_density): too_dense/appropriate/too_sparse
   - 识别的问题列表 (issues)
     * issue_type: redundant/unclear/missing/misplaced/inconsistent
     * severity: critical/major/minor
   - 优化方向 (optimization_directions)

3. **优化机会** (optimization_opportunities)
   识别具体的优化机会点，每个包含:
   - scope: overall/section/slide
   - slide_indices: 相关页码列表
   - category: content/structure/logic/presentation
   - title: 优化标题
   - description: 详细描述
   - current_state: 当前状态
   - suggested_action: 建议操作
   - expected_benefit: 预期收益
   - priority: high/medium/low
   - impact_score: 影响力评分(0-10)

# 输出格式
请严格按照以下JSON结构返回结果（不要包含任何其他文字）:

```json
{{
  "overall_analysis": {{
    "key_points": ["要点1", "要点2", "要点3"],
    "theme": "PPT主题",
    "target_audience": "目标受众",
    "presentation_goal": "演示目标",
    "outline_structure": {{
      "sections": [
        {{
          "section_name": "章节名",
          "slide_indices": [0, 1, 2],
          "purpose": "章节目的",
          "is_necessary": true,
          "improvement_suggestion": "改进建议（可选）"
        }}
      ],
      "structure_type": "linear",
      "structure_quality": "good",
      "structure_issues": ["问题1", "问题2"]
    }},
    "content_coherence": 7.5,
    "logic_flow": 8.0,
    "completeness": 7.0,
    "overall_suggestions": ["建议1", "建议2"]
  }},
  "slide_analyses": [
    {{
      "slide_index": 0,
      "slide_title": "页面标题",
      "main_points": ["要点1", "要点2"],
      "clarity": 8.0,
      "relevance": 9.0,
      "information_density": "appropriate",
      "issues": [
        {{
          "issue_type": "unclear",
          "description": "问题描述",
          "severity": "minor",
          "location": "具体位置（可选）"
        }}
      ],
      "optimization_directions": ["方向1", "方向2"]
    }}
  ],
  "optimization_opportunities": [
    {{
      "scope": "slide",
      "slide_indices": [0],
      "category": "content",
      "title": "优化标题",
      "description": "详细描述",
      "current_state": "当前状态",
      "suggested_action": "建议操作",
      "expected_benefit": "预期收益",
      "priority": "high",
      "impact_score": 8.0
    }}
  ]
}}
```

请开始分析。
"""
        return prompt

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _call_model(self, prompt: str) -> Dict[str, Any]:
        """
        调用大模型API（带重试）

        Args:
            prompt: 分析提示词

        Returns:
            Dict: 模型响应
        """
        model_name = self.analyzer_model_name

        if model_name == "qianwen":
            return await self._call_qianwen(prompt)
        elif model_name == "xunfei":
            return await self._call_xunfei(prompt)
        elif model_name == "wenxin":
            return await self._call_wenxin(prompt)
        elif model_name == "hunyuan":
            return await self._call_hunyuan(prompt)
        else:
            raise ValueError(f"不支持的模型: {model_name}")

    async def _call_qianwen(self, prompt: str) -> Dict[str, Any]:
        """调用通义千问API"""
        api_url = self.analyzer_model_config.get("api_url")
        api_key = self.analyzer_model_config.get("api_key")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "qwen-max",
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            },
            "parameters": {
                "result_format": "message"
            }
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(api_url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    async def _call_xunfei(self, prompt: str) -> Dict[str, Any]:
        """调用讯飞星火API"""
        # 实现讯飞星火API调用逻辑
        # TODO: 根据实际API规范实现
        raise NotImplementedError("讯飞星火API调用待实现")

    async def _call_wenxin(self, prompt: str) -> Dict[str, Any]:
        """调用文心一言API"""
        # 实现文心一言API调用逻辑
        # TODO: 根据实际API规范实现
        raise NotImplementedError("文心一言API调用待实现")

    async def _call_hunyuan(self, prompt: str) -> Dict[str, Any]:
        """调用腾讯混元API"""
        # 实现腾讯混元API调用逻辑
        # TODO: 根据实际API规范实现
        raise NotImplementedError("腾讯混元API调用待实现")

    def _parse_analysis_response(
        self,
        response: Dict[str, Any],
        ppt_id: str
    ) -> ContentAnalysisResult:
        """
        解析模型响应为结构化数据

        Args:
            response: 模型原始响应
            ppt_id: PPT ID

        Returns:
            ContentAnalysisResult: 结构化分析结果
        """
        try:
            # 提取响应文本
            if self.analyzer_model_name == "qianwen":
                text = response.get("output", {}).get("choices", [{}])[0].get("message", {}).get("content", "")
            else:
                # 其他模型的响应提取逻辑
                text = str(response)

            # 提取JSON部分
            json_start = text.find("{")
            json_end = text.rfind("}") + 1

            if json_start == -1 or json_end == 0:
                raise ValueError("响应中未找到有效的JSON")

            json_text = text[json_start:json_end]
            analysis_data = json.loads(json_text)

            # 构建结构化对象
            overall_data = analysis_data.get("overall_analysis", {})
            outline_data = overall_data.get("outline_structure", {})

            # 构建大纲结构
            sections = [
                Section(**section_data)
                for section_data in outline_data.get("sections", [])
            ]

            outline_structure = OutlineStructure(
                sections=sections,
                structure_type=outline_data.get("structure_type", "linear"),
                structure_quality=outline_data.get("structure_quality", "good"),
                structure_issues=outline_data.get("structure_issues", [])
            )

            # 构建整体分析
            overall_analysis = OverallAnalysis(
                key_points=overall_data.get("key_points", []),
                theme=overall_data.get("theme", "未知主题"),
                target_audience=overall_data.get("target_audience", "通用受众"),
                presentation_goal=overall_data.get("presentation_goal", "信息传达"),
                outline_structure=outline_structure,
                content_coherence=float(overall_data.get("content_coherence", 7.0)),
                logic_flow=float(overall_data.get("logic_flow", 7.0)),
                completeness=float(overall_data.get("completeness", 7.0)),
                overall_suggestions=overall_data.get("overall_suggestions", [])
            )

            # 构建每页分析
            slide_analyses = []
            for slide_data in analysis_data.get("slide_analyses", []):
                issues = [
                    ContentIssue(**issue_data)
                    for issue_data in slide_data.get("issues", [])
                ]

                slide_analysis = SlideAnalysis(
                    slide_index=slide_data.get("slide_index", 0),
                    slide_title=slide_data.get("slide_title", ""),
                    main_points=slide_data.get("main_points", []),
                    clarity=float(slide_data.get("clarity", 7.0)),
                    relevance=float(slide_data.get("relevance", 7.0)),
                    information_density=slide_data.get("information_density", "appropriate"),
                    issues=issues,
                    optimization_directions=slide_data.get("optimization_directions", [])
                )
                slide_analyses.append(slide_analysis)

            # 构建优化机会
            optimization_opportunities = []
            for opp_data in analysis_data.get("optimization_opportunities", []):
                opportunity = OptimizationOpportunity(
                    scope=opp_data.get("scope", "slide"),
                    slide_indices=opp_data.get("slide_indices", []),
                    category=opp_data.get("category", "content"),
                    title=opp_data.get("title", ""),
                    description=opp_data.get("description", ""),
                    current_state=opp_data.get("current_state", ""),
                    suggested_action=opp_data.get("suggested_action", ""),
                    expected_benefit=opp_data.get("expected_benefit", ""),
                    priority=opp_data.get("priority", "medium"),
                    impact_score=float(opp_data.get("impact_score", 5.0))
                )
                optimization_opportunities.append(opportunity)

            # 构建完整结果
            result = ContentAnalysisResult(
                ppt_id=ppt_id,
                overall_analysis=overall_analysis,
                slide_analyses=slide_analyses,
                optimization_opportunities=optimization_opportunities,
                metadata={
                    "analyzer_model": self.analyzer_model_name,
                    "raw_response_length": len(text)
                }
            )

            return result

        except Exception as e:
            logger.error(f"解析分析响应失败: {str(e)}")
            raise

    def _post_process(
        self,
        analysis_result: ContentAnalysisResult,
        ppt_data: PPTParseResult
    ) -> ContentAnalysisResult:
        """
        后处理和验证分析结果

        Args:
            analysis_result: 原始分析结果
            ppt_data: PPT数据

        Returns:
            ContentAnalysisResult: 处理后的分析结果
        """
        # 验证页码
        valid_indices = set(range(ppt_data.total_slides))

        # 过滤无效的优化机会
        valid_opportunities = []
        for opp in analysis_result.optimization_opportunities:
            if opp.scope == "overall" or all(idx in valid_indices for idx in opp.slide_indices):
                valid_opportunities.append(opp)
            else:
                logger.warning(f"过滤无效优化机会: {opp.title}, 无效页码: {opp.slide_indices}")

        analysis_result.optimization_opportunities = valid_opportunities

        # 确保每页都有分析
        analyzed_indices = {sa.slide_index for sa in analysis_result.slide_analyses}
        for idx in valid_indices:
            if idx not in analyzed_indices:
                # 添加基本分析
                slide = ppt_data.slides[idx]
                basic_analysis = SlideAnalysis(
                    slide_index=idx,
                    slide_title=f"第 {idx + 1} 页",
                    main_points=["待分析"],
                    clarity=7.0,
                    relevance=7.0,
                    information_density="appropriate",
                    issues=[],
                    optimization_directions=[]
                )
                analysis_result.slide_analyses.append(basic_analysis)

        # 按页码排序
        analysis_result.slide_analyses.sort(key=lambda x: x.slide_index)

        return analysis_result

    def _create_fallback_analysis(self, ppt_data: PPTParseResult) -> ContentAnalysisResult:
        """
        创建降级的基本分析结果

        Args:
            ppt_data: PPT数据

        Returns:
            ContentAnalysisResult: 基本分析结果
        """
        logger.warning(f"使用降级分析: {ppt_data.ppt_id}")

        # 创建基本的大纲结构
        outline_structure = OutlineStructure(
            sections=[
                Section(
                    section_name="主要内容",
                    slide_indices=list(range(ppt_data.total_slides)),
                    purpose="内容展示",
                    is_necessary=True
                )
            ],
            structure_type="linear",
            structure_quality="fair",
            structure_issues=["需要进一步优化"]
        )

        # 创建基本的整体分析
        overall_analysis = OverallAnalysis(
            key_points=["待详细分析"],
            theme=ppt_data.theme.get("name", "未知主题"),
            target_audience="通用受众",
            presentation_goal="信息传达",
            outline_structure=outline_structure,
            content_coherence=7.0,
            logic_flow=7.0,
            completeness=7.0,
            overall_suggestions=["建议进行详细的内容审查"]
        )

        # 为每页创建基本分析
        slide_analyses = []
        for slide in ppt_data.slides:
            slide_analysis = SlideAnalysis(
                slide_index=slide.slide_index,
                slide_title=f"第 {slide.slide_index + 1} 页",
                main_points=["待详细分析"],
                clarity=7.0,
                relevance=7.0,
                information_density="appropriate",
                issues=[],
                optimization_directions=["内容优化", "视觉优化"]
            )
            slide_analyses.append(slide_analysis)

        # 创建一些基本的优化机会
        optimization_opportunities = [
            OptimizationOpportunity(
                scope="overall",
                slide_indices=[],
                category="content",
                title="整体内容优化",
                description="建议对PPT内容进行全面审查和优化",
                current_state="基础内容已完成",
                suggested_action="进行详细的内容分析和优化",
                expected_benefit="提升PPT整体质量",
                priority="high",
                impact_score=8.0
            )
        ]

        return ContentAnalysisResult(
            ppt_id=ppt_data.ppt_id,
            overall_analysis=overall_analysis,
            slide_analyses=slide_analyses,
            optimization_opportunities=optimization_opportunities,
            metadata={
                "fallback": True,
                "reason": "模型分析失败，使用降级方案"
            }
        )
