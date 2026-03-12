@echo off
chcp 65001 >nul
echo ======================================
echo  面试模拟Agent系统 - 后端启动脚本
echo ======================================
echo.

cd /d "%~dp0\backend"

if not exist "venv\Scripts\python.exe" (
    echo [1/4] 创建虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo 创建虚拟环境失败，请检查Python是否安装
        pause
        exit /b 1
    )
)

echo [2/4] 激活虚拟环境...
call venv\Scripts\activate.bat

echo [3/4] 安装依赖...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo 安装依赖失败
    pause
    exit /b 1
)

echo [4/4] 启动后端服务...
echo.
echo 服务启动后，请访问：
echo - 前端: http://localhost:3000/
echo - API文档: http://localhost:5000/docs
echo.
python run.py

pause
