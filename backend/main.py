"""
主程序入口
FastAPI应用启动文件
"""
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import get_settings
from app.api.routes import router
from app.utils import ensure_dir


# 配置日志
def setup_logging():
    """配置日志系统"""
    settings = get_settings()
    log_dir = ensure_dir(settings.logging.log_dir)

    # 移除默认处理器
    logger.remove()

    # 添加控制台输出
    logger.add(
        sys.stdout,
        format=settings.logging.format,
        level=settings.logging.level,
        colorize=True
    )

    # 添加文件输出
    logger.add(
        log_dir / "app.log",
        format=settings.logging.format,
        level=settings.logging.level,
        rotation=settings.logging.rotation,
        retention=settings.logging.retention,
        compression="zip"
    )

    logger.info("日志系统初始化完成")


# 创建FastAPI应用
def create_app() -> FastAPI:
    """
    创建并配置FastAPI应用

    Returns:
        FastAPI: 应用实例
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app.name,
        version=settings.app.version,
        description="多模型协同的PPT智能优化与自动生成系统",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors.allow_origins,
        allow_credentials=settings.cors.allow_credentials,
        allow_methods=settings.cors.allow_methods,
        allow_headers=settings.cors.allow_headers,
    )

    # 注册路由
    app.include_router(router, prefix="/api", tags=["PPT Optimizer"])

    # 启动事件
    @app.on_event("startup")
    async def startup_event():
        logger.info(f"{settings.app.name} v{settings.app.version} 启动中...")

        # 确保必要的目录存在
        ensure_dir(settings.upload.upload_dir)
        ensure_dir(settings.upload.temp_dir)
        ensure_dir(settings.logging.log_dir)

        logger.info("应用启动完成")

    # 关闭事件
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("应用正在关闭...")

    return app


# 初始化日志
setup_logging()

# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()

    logger.info(f"启动服务器: http://{settings.app.host}:{settings.app.port}")
    logger.info(f"API文档: http://{settings.app.host}:{settings.app.port}/docs")

    uvicorn.run(
        "main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
        log_level="info"
    )
