"""
后端启动脚本
"""
import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=5000,
        reload=settings.DEBUG,
        log_level="info"
    )
