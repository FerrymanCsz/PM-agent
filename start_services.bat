@echo off
chcp 65001 >nul
echo ==========================================
echo  面试模拟 Agent 系统 - 服务管理器
echo ==========================================
echo.

REM 检查是否安装了 psutil
d:\trae\PM_agent\miniconda3\python.exe -c "import psutil" 2>nul
if errorlevel 1 (
    echo 正在安装依赖 psutil...
    d:\trae\PM_agent\miniconda3\python.exe -m pip install psutil -q
)

echo 启动服务管理器...
echo 按 Ctrl+C 停止服务
echo.

cd /d d:\trae\PM_agent\backend
d:\trae\PM_agent\miniconda3\python.exe service_manager.py

echo.
echo 服务已停止
pause
