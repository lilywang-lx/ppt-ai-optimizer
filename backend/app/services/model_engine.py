"""
多模型调用引擎
负责并行调用多个PPT专用大模型,并将结果标准化
"""
import asyncio
import json
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from loguru import logger

from app.models.schemas import (
    PPTParseResult,
    ModelSuggestion,
    OptimizationSuggestion,
    OptimizationDimension,
    Priority
)
from app.core.config import ModelConfig


class BaseModelClient(ABC):
    """模型客户端基类"""

    def __init__(self, config: ModelConfig):
        """
        初始化模型客户端

        Args:
            config: 模型配置
        """
        self.config = config
        self.name = config.name
        self.enabled = config.enabled

    @abstractmethod
    async def analyze_ppt(self, ppt_data: PPTParseResult) -> ModelSuggestion:
        """
        分析PPT并返回优化建议

        Args:
            ppt_data: PPT解析数据

        Returns:
            ModelSuggestion: 标准化的优化建议
        """
        pass

    @abstractmethod
    def _build_prompt(self, ppt_data: PPTParseResult) -> str:
        """
        构建提示词

        Args:
            ppt_data: PPT解析数据

        Returns:
            str: 提示词
        """
        pass

    @abstractmethod
    def _parse_response(self, response: Dict[str, Any], ppt_id: str) -> ModelSuggestion:
        """
        解析模型响应并转换为标准格式

        Args:
            response: 模型原始响应
            ppt_id: PPT ID

        Returns:
            ModelSuggestion: 标准化建议
        """
        pass

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _call_api(self, prompt: str) -> Dict[str, Any]:
        """
        调用模型API(带重试)

        Args:
            prompt: 提示词

        Returns:
            Dict: API响应
        """
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await self._make_request(client, prompt)
            return response

    @abstractmethod
    async def _make_request(self, client: httpx.AsyncClient, prompt: str) -> Dict[str, Any]:
        """
        发起HTTP请求

        Args:
            client: HTTP客户端
            prompt: 提示词

        Returns:
            Dict: API响应
        """
        pass


class XunfeiModelClient(BaseModelClient):
    """讯飞星火模型客户端"""

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        logger.info(f"初始化讯飞星火模型客户端: {self.name}")

    async def analyze_ppt(self, ppt_data: PPTParseResult) -> ModelSuggestion:
        """分析PPT并返回优化建议"""
        try:
            logger.info(f"讯飞星火开始分析PPT: {ppt_data.ppt_id}")

            # 构建提示词
            prompt = self._build_prompt(ppt_data)

            # 调用API
            response = await self._call_api(prompt)

            # 解析响应
            suggestion = self._parse_response(response, ppt_data.ppt_id)

            logger.info(f"讯飞星火分析完成: {ppt_data.ppt_id}, 建议数: {len(suggestion.optimization_suggestions)}")
            return suggestion

        except Exception as e:
            logger.error(f"讯飞星火分析失败: {ppt_data.ppt_id}, 错误: {str(e)}")
            raise

    def _build_prompt(self, ppt_data: PPTParseResult) -> str:
        """构建提示词"""
        # 构建PPT描述
        ppt_desc = f"PPT文件名: {ppt_data.filename}\n"
        ppt_desc += f"总页数: {ppt_data.total_slides}\n\n"

        # 添加每页内容
        for slide in ppt_data.slides:
            ppt_desc += f"第{slide.slide_index + 1}页 ({slide.slide_type}):\n"
            ppt_desc += f"内容: {slide.content[:200]}...\n"  # 限制长度
            ppt_desc += f"版式: {slide.layout_info.layout_type}\n\n"

        # 构建完整提示词
        prompt = f"""你是一个专业的PPT优化助手。请分析以下PPT内容,从内容、逻辑、排版、配色、字体、图表等维度提供优化建议。

{ppt_desc}

请以JSON格式返回优化建议,格式如下:
{{
  "suggestions": [
    {{
      "slide_index": 0,
      "optimization_dimension": "layout",
      "original_content": "原始内容描述",
      "suggestion": "具体优化建议",
      "reason": "建议理由",
      "priority": "recommend"
    }}
  ]
}}

优化维度可选值: content, logic, layout, color, font, chart
优先级可选值: must, recommend, optional
"""
        return prompt

    async def _make_request(self, client: httpx.AsyncClient, prompt: str) -> Dict[str, Any]:
        """发起HTTP请求"""
        # 注意: 这里是示例实现,实际需要根据讯飞星火的真实API文档调整
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}"
        }

        payload = {
            "app_id": self.config.app_id,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        response = await client.post(
            self.config.api_url,
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def _parse_response(self, response: Dict[str, Any], ppt_id: str) -> ModelSuggestion:
        """解析响应"""
        try:
            # 从响应中提取内容
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "{}")

            # 解析JSON
            data = json.loads(content)
            suggestions_data = data.get("suggestions", [])

            # 转换为标准格式
            suggestions = []
            for s in suggestions_data:
                suggestion = OptimizationSuggestion(
                    slide_index=s.get("slide_index", 0),
                    optimization_dimension=OptimizationDimension(s.get("optimization_dimension", "content")),
                    original_content=s.get("original_content", ""),
                    suggestion=s.get("suggestion", ""),
                    reason=s.get("reason", ""),
                    priority=Priority(s.get("priority", "recommend"))
                )
                suggestions.append(suggestion)

            return ModelSuggestion(
                ppt_id=ppt_id,
                model_name=self.name,
                optimization_suggestions=suggestions,
                core_strength=self.config.core_strength
            )

        except Exception as e:
            logger.error(f"解析讯飞星火响应失败: {str(e)}")
            # 返回空建议
            return ModelSuggestion(
                ppt_id=ppt_id,
                model_name=self.name,
                optimization_suggestions=[],
                core_strength=self.config.core_strength
            )


class WenxinModelClient(BaseModelClient):
    """文心一言模型客户端"""

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        logger.info(f"初始化文心一言模型客户端: {self.name}")

    async def analyze_ppt(self, ppt_data: PPTParseResult) -> ModelSuggestion:
        """分析PPT并返回优化建议"""
        try:
            logger.info(f"文心一言开始分析PPT: {ppt_data.ppt_id}")
            prompt = self._build_prompt(ppt_data)
            response = await self._call_api(prompt)
            suggestion = self._parse_response(response, ppt_data.ppt_id)
            logger.info(f"文心一言分析完成: {ppt_data.ppt_id}")
            return suggestion
        except Exception as e:
            logger.error(f"文心一言分析失败: {ppt_data.ppt_id}, 错误: {str(e)}")
            raise

    def _build_prompt(self, ppt_data: PPTParseResult) -> str:
        """构建提示词(侧重排版和配色)"""
        prompt = f"""作为PPT设计专家,请重点分析以下PPT的排版、配色、字体设计,提供专业的优化建议。

PPT基本信息:
- 文件名: {ppt_data.filename}
- 总页数: {ppt_data.total_slides}

"""
        for slide in ppt_data.slides[:5]:  # 限制前5页
            prompt += f"\n第{slide.slide_index + 1}页:\n"
            prompt += f"类型: {slide.slide_type}\n"
            prompt += f"版式: {slide.layout_info.layout_type}\n"
            if slide.style_info.font_name:
                prompt += f"字体: {slide.style_info.font_name}\n"

        prompt += "\n请以JSON格式返回优化建议,重点关注layout、color、font维度。"
        return prompt

    async def _make_request(self, client: httpx.AsyncClient, prompt: str) -> Dict[str, Any]:
        """发起HTTP请求"""
        # 文心一言API示例实现
        headers = {
            "Content-Type": "application/json"
        }

        # 构建带access_token的URL
        url = f"{self.config.api_url}?access_token={self.config.api_key}"

        payload = {
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

    def _parse_response(self, response: Dict[str, Any], ppt_id: str) -> ModelSuggestion:
        """解析响应"""
        # 类似讯飞星火的解析逻辑
        try:
            content = response.get("result", "{}")
            data = json.loads(content) if isinstance(content, str) else content
            suggestions_data = data.get("suggestions", [])

            suggestions = [
                OptimizationSuggestion(
                    slide_index=s.get("slide_index", 0),
                    optimization_dimension=OptimizationDimension(s.get("optimization_dimension", "layout")),
                    original_content=s.get("original_content", ""),
                    suggestion=s.get("suggestion", ""),
                    reason=s.get("reason", ""),
                    priority=Priority(s.get("priority", "recommend"))
                )
                for s in suggestions_data
            ]

            return ModelSuggestion(
                ppt_id=ppt_id,
                model_name=self.name,
                optimization_suggestions=suggestions,
                core_strength=self.config.core_strength
            )
        except Exception as e:
            logger.error(f"解析文心一言响应失败: {str(e)}")
            return ModelSuggestion(
                ppt_id=ppt_id,
                model_name=self.name,
                optimization_suggestions=[],
                core_strength=self.config.core_strength
            )


class QianwenModelClient(BaseModelClient):
    """通义千问模型客户端"""

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        logger.info(f"初始化通义千问模型客户端: {self.name}")

    async def analyze_ppt(self, ppt_data: PPTParseResult) -> ModelSuggestion:
        """分析PPT(侧重内容逻辑和图表)"""
        try:
            logger.info(f"通义千问开始分析PPT: {ppt_data.ppt_id}")
            prompt = self._build_prompt(ppt_data)
            response = await self._call_api(prompt)
            suggestion = self._parse_response(response, ppt_data.ppt_id)
            logger.info(f"通义千问分析完成: {ppt_data.ppt_id}")
            return suggestion
        except Exception as e:
            logger.error(f"通义千问分析失败: {str(e)}")
            raise

    def _build_prompt(self, ppt_data: PPTParseResult) -> str:
        """构建提示词(侧重内容逻辑)"""

        # 提取前5页的内容概要
        slides_summary = ""
        for idx, slide in enumerate(ppt_data.slides[:5]):
            slides_summary += f"\n第{idx+1}页 ({slide.slide_type}):\n{slide.content[:200]}\n"

        prompt = f"""你是一位专业的PPT优化专家。请分析以下PPT并提供优化建议。

PPT信息:
- 文件名: {ppt_data.filename}
- 总页数: {ppt_data.total_slides}页
- 前5页内容概要:{slides_summary}

请重点分析:
1. 内容的逻辑性和完整性
2. 文字表达的清晰度和专业性
3. 图表的数据可视化效果
4. 整体结构和布局

请必须按照以下JSON格式返回优化建议(只返回JSON，不要其他文字):

{{
  "suggestions": [
    {{
      "slide_index": 1,
      "optimization_dimension": "content",
      "original_content": "原始内容片段",
      "suggestion": "具体的优化建议",
      "reason": "为什么需要优化",
      "priority": "recommend"
    }}
  ]
}}

注意:
- optimization_dimension可选: content(内容), logic(逻辑), layout(版式), color(配色), font(字体), chart(图表)
- priority可选: must(必须), recommend(推荐), optional(可选)
- 请至少提供3-5条具体的优化建议
- 只返回JSON格式，不要包含其他解释性文字
"""
        return prompt

    async def _make_request(self, client: httpx.AsyncClient, prompt: str) -> Dict[str, Any]:
        """发起HTTP请求"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}"
        }

        payload = {
            "model": "qwen-turbo",
            "input": {
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
        }

        response = await client.post(self.config.api_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

    def _parse_response(self, response: Dict[str, Any], ppt_id: str) -> ModelSuggestion:
        """解析响应"""
        try:
            content = response.get("output", {}).get("text", "{}")

            # 清理可能的markdown代码块标记
            if isinstance(content, str):
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

            logger.debug(f"通义千问原始响应内容: {content[:500]}")

            data = json.loads(content) if isinstance(content, str) else content
            suggestions_data = data.get("suggestions", [])

            logger.info(f"通义千问解析到 {len(suggestions_data)} 条建议")

            suggestions = [
                OptimizationSuggestion(
                    slide_index=s.get("slide_index", 0),
                    optimization_dimension=OptimizationDimension(s.get("optimization_dimension", "logic")),
                    original_content=s.get("original_content", ""),
                    suggestion=s.get("suggestion", ""),
                    reason=s.get("reason", ""),
                    priority=Priority(s.get("priority", "recommend"))
                )
                for s in suggestions_data
            ]

            return ModelSuggestion(
                ppt_id=ppt_id,
                model_name=self.name,
                optimization_suggestions=suggestions,
                core_strength=self.config.core_strength
            )
        except Exception as e:
            logger.error(f"解析通义千问响应失败: {str(e)}")
            return ModelSuggestion(
                ppt_id=ppt_id,
                model_name=self.name,
                optimization_suggestions=[],
                core_strength=self.config.core_strength
            )


class HunyuanModelClient(BaseModelClient):
    """腾讯混元模型客户端"""

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        logger.info(f"初始化腾讯混元模型客户端: {self.name}")

    async def analyze_ppt(self, ppt_data: PPTParseResult) -> ModelSuggestion:
        """分析PPT(全维度融合)"""
        try:
            logger.info(f"腾讯混元开始分析PPT: {ppt_data.ppt_id}")
            prompt = self._build_prompt(ppt_data)
            response = await self._call_api(prompt)
            suggestion = self._parse_response(response, ppt_data.ppt_id)
            logger.info(f"腾讯混元分析完成: {ppt_data.ppt_id}")
            return suggestion
        except Exception as e:
            logger.error(f"腾讯混元分析失败: {str(e)}")
            raise

    def _build_prompt(self, ppt_data: PPTParseResult) -> str:
        """构建提示词"""

        # 提取前5页的内容概要
        slides_summary = ""
        for idx, slide in enumerate(ppt_data.slides[:5]):
            slides_summary += f"\n第{idx+1}页 ({slide.slide_type}):\n{slide.content[:200]}\n"

        prompt = f"""你是一位资深的PPT综合优化专家。请全面分析以下PPT并提供专业的优化建议。

PPT信息:
- 文件名: {ppt_data.filename}
- 总页数: {ppt_data.total_slides}页
- 前5页内容概要:{slides_summary}

请从以下多个维度进行全面分析:
1. 内容质量和逻辑结构
2. 视觉排版和布局
3. 配色方案和品牌一致性
4. 字体选择和可读性
5. 图表设计和数据可视化
6. 整体专业度和说服力

请严格按照以下JSON格式返回优化建议(只返回JSON，不要其他说明):

{{
  "suggestions": [
    {{
      "slide_index": 1,
      "optimization_dimension": "layout",
      "original_content": "当前存在的问题描述",
      "suggestion": "详细的优化建议和改进方案",
      "reason": "为什么这样优化会更好",
      "priority": "recommend"
    }}
  ]
}}

字段说明:
- slide_index: 页码(1-{ppt_data.total_slides})
- optimization_dimension: content/logic/layout/color/font/chart
- priority: must(必须)/recommend(推荐)/optional(可选)
- 请提供5-10条切实可行的优化建议
- 必须只返回纯JSON，不要添加markdown标记或其他文字
"""
        return prompt

    async def _make_request(self, client: httpx.AsyncClient, prompt: str) -> Dict[str, Any]:
        """发起HTTP请求"""
        # 腾讯混元API示例
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"{self.config.secret_id}:{self.config.secret_key}"
        }

        payload = {
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        response = await client.post(self.config.api_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

    def _parse_response(self, response: Dict[str, Any], ppt_id: str) -> ModelSuggestion:
        """解析响应"""
        try:
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "{}")

            # 清理可能的markdown代码块标记
            if isinstance(content, str):
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

            logger.debug(f"腾讯混元原始响应内容: {content[:500]}")

            data = json.loads(content) if isinstance(content, str) else content
            suggestions_data = data.get("suggestions", [])

            logger.info(f"腾讯混元解析到 {len(suggestions_data)} 条建议")

            suggestions = [
                OptimizationSuggestion(
                    slide_index=s.get("slide_index", 0),
                    optimization_dimension=OptimizationDimension(s.get("optimization_dimension", "content")),
                    original_content=s.get("original_content", ""),
                    suggestion=s.get("suggestion", ""),
                    reason=s.get("reason", ""),
                    priority=Priority(s.get("priority", "recommend"))
                )
                for s in suggestions_data
            ]

            return ModelSuggestion(
                ppt_id=ppt_id,
                model_name=self.name,
                optimization_suggestions=suggestions,
                core_strength=self.config.core_strength
            )
        except Exception as e:
            logger.error(f"解析腾讯混元响应失败: {str(e)}")
            return ModelSuggestion(
                ppt_id=ppt_id,
                model_name=self.name,
                optimization_suggestions=[],
                core_strength=self.config.core_strength
            )


class ModelEngine:
    """模型引擎 - 管理多个模型的并行调用"""

    def __init__(self, model_configs: Dict[str, ModelConfig]):
        """
        初始化模型引擎

        Args:
            model_configs: 模型配置字典
        """
        self.clients: Dict[str, BaseModelClient] = {}

        # 初始化各个模型客户端
        if "xunfei" in model_configs and model_configs["xunfei"].enabled:
            self.clients["xunfei"] = XunfeiModelClient(model_configs["xunfei"])

        if "wenxin" in model_configs and model_configs["wenxin"].enabled:
            self.clients["wenxin"] = WenxinModelClient(model_configs["wenxin"])

        if "qianwen" in model_configs and model_configs["qianwen"].enabled:
            self.clients["qianwen"] = QianwenModelClient(model_configs["qianwen"])

        if "hunyuan" in model_configs and model_configs["hunyuan"].enabled:
            self.clients["hunyuan"] = HunyuanModelClient(model_configs["hunyuan"])

        logger.info(f"模型引擎初始化完成,已加载 {len(self.clients)} 个模型")

    async def analyze_ppt_parallel(
        self,
        ppt_data: PPTParseResult,
        guidance: Dict[str, Any] = None
    ) -> List[ModelSuggestion]:
        """
        并行调用所有模型分析PPT

        Args:
            ppt_data: PPT解析数据
            guidance: 可选的优化指引（来自内容分析）

        Returns:
            List[ModelSuggestion]: 所有模型的建议列表
        """
        logger.info(f"开始并行调用 {len(self.clients)} 个模型分析PPT: {ppt_data.ppt_id}")

        if guidance:
            logger.info(f"使用优化指引，包含 {len(guidance.get('approved_opportunities', []))} 个批准的优化机会")

        # 创建异步任务
        tasks = []
        model_names = []
        for name, client in self.clients.items():
            tasks.append(self._safe_analyze(client, ppt_data, guidance))
            model_names.append(name)

        # 并行执行
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        suggestions = []
        for name, result in zip(model_names, results):
            if isinstance(result, Exception):
                logger.error(f"模型 {name} 调用失败: {str(result)}")
                # 降级处理: 返回空建议
                suggestions.append(ModelSuggestion(
                    ppt_id=ppt_data.ppt_id,
                    model_name=name,
                    optimization_suggestions=[],
                    core_strength=self.clients[name].config.core_strength
                ))
            else:
                suggestions.append(result)

        logger.info(f"并行分析完成,共收到 {len(suggestions)} 个模型的建议")
        return suggestions

    async def _safe_analyze(
        self,
        client: BaseModelClient,
        ppt_data: PPTParseResult,
        guidance: Dict[str, Any] = None
    ) -> ModelSuggestion:
        """
        安全地调用模型(带异常捕获)

        Args:
            client: 模型客户端
            ppt_data: PPT数据
            guidance: 可选的优化指引

        Returns:
            ModelSuggestion: 建议结果
        """
        try:
            return await client.analyze_ppt(ppt_data)
        except Exception as e:
            logger.error(f"模型 {client.name} 调用异常: {str(e)}")
            raise
