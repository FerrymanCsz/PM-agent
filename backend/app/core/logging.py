"""
日志配置
"""
import logging
import sys
from pathlib import Path


def setup_logging():
    """配置日志"""
    
    # 创建日志目录
    log_dir = Path("./logs")
    log_dir.mkdir(exist_ok=True)
    
    # 配置根日志记录器
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            # 控制台输出
            logging.StreamHandler(sys.stdout),
            # 文件输出
            logging.FileHandler(
                log_dir / "app.log",
                encoding='utf-8'
            )
        ]
    )
    
    # 设置第三方库的日志级别
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    
    return logging.getLogger(__name__)


# 全局日志记录器
logger = setup_logging()
