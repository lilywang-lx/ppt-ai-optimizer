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
from app.models.schemas import TaskProgress, ProcessStatus
from app.services import PPTParser, ModelEngine, IterationCorrector, PPTGenerator
from app.utils import generate_ppt_id, is_allowed_file, ensure_dir, get_file_size


router = APIRouter()

# 全局任务状态存储(生产环境应使用Redis等)
task_status: Dict[str, TaskProgress] = {}

# 全局结果存储
task_results: Dict[str, Dict[str, Any]] = {}


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
    后台处理PPT的完整流程

    Args:
        ppt_id: PPT ID
        file_path: 文件路径
        filename: 文件名
    """
    settings = get_settings()

    try:
        # 步骤1: 解析PPT
        update_progress(ppt_id, ProcessStatus.PARSING, 10, "解析PPT", "正在解析PPT文件...")
        parser = PPTParser()
        ppt_data = parser.parse(file_path, ppt_id)
        logger.info(f"PPT解析完成: {ppt_id}")

        # 步骤2: 多模型分析
        update_progress(ppt_id, ProcessStatus.ANALYZING, 30, "模型分析", "正在调用多个AI模型分析...")
        engine = ModelEngine(settings.models)
        model_suggestions = await engine.analyze_ppt_parallel(ppt_data)
        logger.info(f"模型分析完成: {ppt_id}, 收到 {len(model_suggestions)} 个模型建议")

        # 步骤3: 迭代修正
        update_progress(ppt_id, ProcessStatus.CORRECTING, 60, "迭代修正", "正在进行跨模型迭代修正...")
        corrector = IterationCorrector(settings.iteration, settings.conflict_resolution)
        final_plan = await corrector.process(ppt_id, model_suggestions)
        logger.info(f"迭代修正完成: {ppt_id}, 冲突率: {final_plan.conflict_rate:.2%}")

        # 步骤4: 生成新PPT
        update_progress(ppt_id, ProcessStatus.GENERATING, 80, "生成PPT", "正在生成优化后的PPT...")
        generator = PPTGenerator(settings.upload.temp_dir)
        result = await generator.generate(file_path, ppt_data, final_plan)

        if not result.success:
            raise Exception(result.error_message)

        logger.info(f"PPT生成完成: {ppt_id}")

        # 存储结果
        task_results[ppt_id] = {
            "ppt_data": ppt_data.dict(),
            "model_suggestions": [s.dict() for s in model_suggestions],
            "final_plan": final_plan.dict(),
            "output_file": result.output_path
        }

        # 完成
        update_progress(ppt_id, ProcessStatus.COMPLETED, 100, "完成", "PPT优化完成!")

    except Exception as e:
        logger.error(f"PPT处理失败: {ppt_id}, 错误: {str(e)}")
        update_progress(ppt_id, ProcessStatus.FAILED, 0, "失败", f"处理失败: {str(e)}")


def update_progress(ppt_id: str, status: ProcessStatus, progress: float, step: str, message: str):
    """更新任务进度"""
    task_status[ppt_id] = TaskProgress(
        ppt_id=ppt_id,
        status=status,
        progress=progress,
        current_step=step,
        message=message
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

    return {
        "ppt_id": ppt_id,
        "status": "completed",
        "model_suggestions": result["model_suggestions"],
        "final_plan": result["final_plan"],
        "download_url": f"/api/download/{ppt_id}"
    }


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
