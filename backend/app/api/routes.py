"""
API路由模块
提供PPT优化的REST API接口
"""
import os
import shutil
from pathlib import Path
from typing import Dict, Any
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from loguru import logger

from app.core.config import get_settings
from app.models.schemas import (
    TaskProgress, ProcessStatus, ContentAnalysisResult,
    UserEditRequest, ChangeTrackingReport
)
from app.services import PPTParser, ModelEngine, IterationCorrector, PPTGenerator
from app.services.optimization_orchestrator import OptimizationOrchestrator
from app.utils import generate_ppt_id, is_allowed_file, ensure_dir, get_file_size


router = APIRouter()

# 全局任务状态存储(生产环境应使用Redis等)
task_status: Dict[str, TaskProgress] = {}

# 全局结果存储
task_results: Dict[str, Dict[str, Any]] = {}

# 内容分析结果存储
content_analysis_results: Dict[str, ContentAnalysisResult] = {}

# 修改追踪报告存储
change_reports: Dict[str, ChangeTrackingReport] = {}

# PPT数据存储（用于第二阶段）
ppt_data_cache: Dict[str, Any] = {}


@router.post("/upload")
async def upload_ppt(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    上传PPT文件并开始处理

    Args:
        file: 上传的PPT文件
        background_tasks: 后台任务

    Returns:
        dict: 包含ppt_id和初始状态
    """
    settings = get_settings()

    try:
        # 验证文件类型
        if not is_allowed_file(file.filename, settings.upload.allowed_extensions):
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型。仅支持: {settings.upload.allowed_extensions}"
            )

        # 生成PPT ID
        ppt_id = generate_ppt_id()

        # 创建上传目录
        upload_dir = ensure_dir(settings.upload.upload_dir)
        file_path = upload_dir / f"{ppt_id}_{file.filename}"

        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 检查文件大小
        file_size = get_file_size(str(file_path))
        if file_size > settings.upload.max_size:
            os.remove(file_path)
            raise HTTPException(
                status_code=400,
                detail=f"文件过大。最大允许: {settings.upload.max_size / 1024 / 1024}MB"
            )

        logger.info(f"文件上传成功: {ppt_id}, 路径: {file_path}")

        # 初始化任务状态
        task_status[ppt_id] = TaskProgress(
            ppt_id=ppt_id,
            status=ProcessStatus.PENDING,
            progress=0,
            current_step="上传完成",
            message="文件已上传,等待处理"
        )

        # 启动后台处理任务
        background_tasks.add_task(process_ppt, ppt_id, str(file_path), file.filename)

        return {
            "ppt_id": ppt_id,
            "filename": file.filename,
            "status": "uploaded",
            "message": "文件上传成功,开始处理"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


async def process_ppt(ppt_id: str, file_path: str, filename: str):
    """
    后台处理PPT的完整流程（两阶段）
    阶段1: PPT解析 + 内容分析 → 等待用户审查
    阶段2: 用户提交编辑后 → 模型优化 + PPT生成

    Args:
        ppt_id: PPT ID
        file_path: 文件路径
        filename: 文件名
    """
    settings = get_settings()

    try:
        # =====================================================================
        # 阶段1: 内容分析
        # =====================================================================

        # 步骤1: 解析PPT
        update_progress(ppt_id, ProcessStatus.PARSING, 10, "解析PPT", "正在解析PPT文件...")
        parser = PPTParser()
        ppt_data = parser.parse(file_path, ppt_id)
        logger.info(f"PPT解析完成: {ppt_id}")

        # 缓存PPT数据（供第二阶段使用）
        ppt_data_cache[ppt_id] = {
            "ppt_data": ppt_data,
            "file_path": file_path,
            "filename": filename
        }

        # 步骤2: 内容深度分析
        update_progress(
            ppt_id, ProcessStatus.CONTENT_ANALYZING, 30,
            "内容分析", "正在使用大模型进行深度内容分析..."
        )
        orchestrator = OptimizationOrchestrator(settings.dict())
        content_analysis = await orchestrator.execute_phase1_analysis(ppt_data)
        logger.info(
            f"内容分析完成: {ppt_id}, "
            f"识别 {len(content_analysis.optimization_opportunities)} 个优化机会"
        )

        # 保存内容分析结果
        content_analysis_results[ppt_id] = content_analysis

        # 步骤3: 等待用户审查
        update_progress(
            ppt_id, ProcessStatus.WAITING_USER_REVIEW, 40,
            "等待审查", "内容分析已完成，请审查优化建议",
            requires_user_action=True,
            action_url=f"/api/content-analysis/{ppt_id}"
        )

        logger.info(f"第一阶段完成，等待用户审查: {ppt_id}")

        # 注意：此时函数返回，等待用户通过API提交编辑或跳过审查

    except Exception as e:
        logger.error(f"PPT处理失败（第一阶段）: {ppt_id}, 错误: {str(e)}")
        update_progress(ppt_id, ProcessStatus.FAILED, 0, "失败", f"处理失败: {str(e)}")


async def process_ppt_phase2(ppt_id: str, user_edits: UserEditRequest):
    """
    执行PPT优化的第二阶段

    Args:
        ppt_id: PPT ID
        user_edits: 用户编辑请求
    """
    settings = get_settings()

    try:
        # 获取缓存的数据
        if ppt_id not in ppt_data_cache:
            raise Exception("PPT数据未找到，请重新上传")

        if ppt_id not in content_analysis_results:
            raise Exception("内容分析结果未找到")

        cached_data = ppt_data_cache[ppt_id]
        ppt_data = cached_data["ppt_data"]
        file_path = cached_data["file_path"]
        content_analysis = content_analysis_results[ppt_id]

        # =====================================================================
        # 阶段2: 模型优化与生成
        # =====================================================================

        # 步骤4: 执行优化
        update_progress(
            ppt_id, ProcessStatus.OPTIMIZING, 50,
            "执行优化", "正在基于您的编辑执行优化..."
        )

        orchestrator = OptimizationOrchestrator(settings.dict())

        # 步骤5: 多模型分析（基于用户编辑的指引）
        update_progress(
            ppt_id, ProcessStatus.ANALYZING, 70,
            "模型分析", "正在调用多个AI模型进行优化分析..."
        )

        # 步骤6: 生成PPT和修改追踪报告
        update_progress(
            ppt_id, ProcessStatus.GENERATING, 85,
            "生成PPT", "正在生成优化后的PPT并追踪修改..."
        )

        generate_result, change_report = await orchestrator.execute_phase2_optimization(
            file_path,
            ppt_data,
            user_edits,
            content_analysis
        )

        if not generate_result.success:
            raise Exception(generate_result.error_message)

        logger.info(f"PPT生成完成: {ppt_id}, 修改数: {change_report.total_changes}")

        # 保存修改追踪报告
        change_reports[ppt_id] = change_report

        # 存储结果
        task_results[ppt_id] = {
            "ppt_data": ppt_data.dict(),
            "content_analysis": content_analysis.dict(),
            "user_edits": user_edits.dict(),
            "change_report": change_report.dict(),
            "output_file": generate_result.output_path
        }

        # 完成
        update_progress(ppt_id, ProcessStatus.COMPLETED, 100, "完成", "PPT优化完成!")

        logger.info(f"第二阶段完成: {ppt_id}")

    except Exception as e:
        logger.error(f"PPT处理失败（第二阶段）: {ppt_id}, 错误: {str(e)}")
        update_progress(ppt_id, ProcessStatus.FAILED, 0, "失败", f"处理失败: {str(e)}")


def update_progress(
    ppt_id: str,
    status: ProcessStatus,
    progress: float,
    step: str,
    message: str,
    requires_user_action: bool = False,
    action_url: str = None
):
    """更新任务进度"""
    task_status[ppt_id] = TaskProgress(
        ppt_id=ppt_id,
        status=status,
        progress=progress,
        current_step=step,
        message=message,
        requires_user_action=requires_user_action,
        action_url=action_url
    )


@router.get("/status/{ppt_id}")
async def get_status(ppt_id: str):
    """
    获取PPT处理状态

    Args:
        ppt_id: PPT ID

    Returns:
        dict: 任务状态
    """
    if ppt_id not in task_status:
        raise HTTPException(status_code=404, detail="任务不存在")

    return task_status[ppt_id].dict()


@router.get("/result/{ppt_id}")
async def get_result(ppt_id: str):
    """
    获取PPT处理结果

    Args:
        ppt_id: PPT ID

    Returns:
        dict: 处理结果
    """
    if ppt_id not in task_results:
        raise HTTPException(status_code=404, detail="结果不存在或处理未完成")

    result = task_results[ppt_id]

    response = {
        "ppt_id": ppt_id,
        "status": "completed",
        "download_url": f"/api/download/{ppt_id}"
    }

    # 包含内容分析（如果有）
    if "content_analysis" in result:
        response["content_analysis"] = result["content_analysis"]

    # 包含用户编辑（如果有）
    if "user_edits" in result:
        response["user_edits"] = result["user_edits"]

    # 包含修改追踪报告（如果有）
    if "change_report" in result:
        response["change_report"] = result["change_report"]

    # 兼容旧版本（如果有）
    if "model_suggestions" in result:
        response["model_suggestions"] = result["model_suggestions"]

    if "final_plan" in result:
        response["final_plan"] = result["final_plan"]

    return response


@router.get("/download/{ppt_id}")
async def download_ppt(ppt_id: str):
    """
    下载优化后的PPT

    Args:
        ppt_id: PPT ID

    Returns:
        FileResponse: PPT文件
    """
    if ppt_id not in task_results:
        raise HTTPException(status_code=404, detail="文件不存在")

    output_path = task_results[ppt_id]["output_file"]

    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="文件已被删除")

    return FileResponse(
        output_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=Path(output_path).name
    )


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "message": "服务运行正常"}


# ============================================================================
# 新增API端点 - 内容分析和交互式编辑
# ============================================================================

@router.get("/content-analysis/{ppt_id}")
async def get_content_analysis(ppt_id: str):
    """
    获取内容分析结果

    Args:
        ppt_id: PPT ID

    Returns:
        dict: 内容分析结果
    """
    if ppt_id not in content_analysis_results:
        raise HTTPException(status_code=404, detail="内容分析结果不存在或未完成")

    if ppt_id not in task_status:
        raise HTTPException(status_code=404, detail="任务不存在")

    status = task_status[ppt_id]

    # 检查状态
    if status.status != ProcessStatus.WAITING_USER_REVIEW:
        raise HTTPException(
            status_code=400,
            detail=f"当前状态不支持获取分析结果: {status.status}"
        )

    analysis = content_analysis_results[ppt_id]

    return {
        "ppt_id": ppt_id,
        "status": "waiting_user_review",
        "analysis": analysis.dict(),
        "message": "内容分析已完成，请审查优化建议"
    }


@router.post("/submit-edits/{ppt_id}")
async def submit_edits(ppt_id: str, user_edits: UserEditRequest, background_tasks: BackgroundTasks):
    """
    提交用户编辑并继续优化

    Args:
        ppt_id: PPT ID
        user_edits: 用户编辑请求
        background_tasks: 后台任务

    Returns:
        dict: 响应消息
    """
    if ppt_id not in task_status:
        raise HTTPException(status_code=404, detail="任务不存在")

    status = task_status[ppt_id]

    if status.status != ProcessStatus.WAITING_USER_REVIEW:
        raise HTTPException(
            status_code=400,
            detail=f"当前状态不支持提交编辑: {status.status}"
        )

    # 验证user_edits中的ppt_id
    if user_edits.ppt_id != ppt_id:
        raise HTTPException(status_code=400, detail="PPT ID不匹配")

    logger.info(f"接收用户编辑: {ppt_id}, 批准的优化机会数: {sum(1 for o in user_edits.modified_opportunities if o.user_approved)}")

    # 更新状态为用户编辑中
    update_progress(
        ppt_id, ProcessStatus.USER_EDITING, 45,
        "处理编辑", "正在处理您的编辑..."
    )

    # 启动第二阶段后台任务
    background_tasks.add_task(process_ppt_phase2, ppt_id, user_edits)

    return {
        "ppt_id": ppt_id,
        "status": "optimizing",
        "message": "已接收您的修改，开始执行优化..."
    }


@router.post("/skip-review/{ppt_id}")
async def skip_review(ppt_id: str, background_tasks: BackgroundTasks):
    """
    跳过审查，使用默认优化建议

    Args:
        ppt_id: PPT ID
        background_tasks: 后台任务

    Returns:
        dict: 响应消息
    """
    if ppt_id not in task_status:
        raise HTTPException(status_code=404, detail="任务不存在")

    status = task_status[ppt_id]

    if status.status != ProcessStatus.WAITING_USER_REVIEW:
        raise HTTPException(
            status_code=400,
            detail=f"当前状态不支持跳过审查: {status.status}"
        )

    if ppt_id not in content_analysis_results:
        raise HTTPException(status_code=404, detail="内容分析结果不存在")

    logger.info(f"用户跳过审查，使用默认建议: {ppt_id}")

    # 创建默认用户编辑
    settings = get_settings()
    orchestrator = OptimizationOrchestrator(settings.dict())
    content_analysis = content_analysis_results[ppt_id]
    default_edits = orchestrator.create_default_user_edits(content_analysis)

    # 更新状态
    update_progress(
        ppt_id, ProcessStatus.USER_EDITING, 45,
        "使用默认建议", "正在使用默认优化建议..."
    )

    # 启动第二阶段后台任务
    background_tasks.add_task(process_ppt_phase2, ppt_id, default_edits)

    return {
        "ppt_id": ppt_id,
        "status": "optimizing",
        "message": "使用默认优化建议，开始执行优化..."
    }


@router.get("/change-report/{ppt_id}")
async def get_change_report(ppt_id: str):
    """
    获取修改追踪报告

    Args:
        ppt_id: PPT ID

    Returns:
        dict: 修改追踪报告
    """
    if ppt_id not in change_reports:
        raise HTTPException(status_code=404, detail="修改报告不存在或处理未完成")

    report = change_reports[ppt_id]

    return {
        "ppt_id": ppt_id,
        "report": report.dict()
    }
