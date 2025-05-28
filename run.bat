@echo off
echo 正在启动小说转漫画应用...

:: 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python未安装，请先安装Python 3.8-3.10
    pause
    exit /b
)

:: 检查是否已安装依赖
if not exist venv (
    echo 首次运行，正在创建虚拟环境...
    python -m venv venv
    call venv\Scripts\activate
    echo 正在安装依赖...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)

:: 启动应用
echo 启动应用...
python app.py

pause