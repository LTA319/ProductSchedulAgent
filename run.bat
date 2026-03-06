@echo off
REM 生产排程智能体启动脚本 (Windows)

echo ========================================
echo 生产排程智能体
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8 或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [信息] 检测到 Python 版本:
python --version
echo.

REM 检查虚拟环境是否存在
if not exist "venv\" (
    echo [信息] 虚拟环境不存在，正在创建...
    python -m venv venv
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo [成功] 虚拟环境创建完成
    echo.
)

REM 激活虚拟环境
echo [信息] 激活虚拟环境...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [错误] 激活虚拟环境失败
    pause
    exit /b 1
)

REM 检查依赖是否安装
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo [信息] 检测到缺少依赖包，正在安装...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 安装依赖包失败
        pause
        exit /b 1
    )
    echo [成功] 依赖包安装完成
    echo.
)

REM 启动应用
echo [信息] 启动 Web 应用...
echo [提示] 浏览器将自动打开 http://localhost:8501
echo [提示] 按 Ctrl+C 可停止应用
echo.
streamlit run ui/app.py

pause
