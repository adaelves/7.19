@echo off
chcp 65001 >nul
title 视频下载器 - Video Downloader

echo.
echo ================================================
echo 🎬 多平台视频下载器 v1.0.0
echo Multi-platform Video Downloader v1.0.0
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: Python未安装或未添加到PATH
    echo ❌ Error: Python not installed or not in PATH
    echo.
    echo 请从以下地址下载并安装Python:
    echo Please download and install Python from:
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python版本: %PYTHON_VERSION%
echo ✅ Python version: %PYTHON_VERSION%

REM Run the application
echo.
echo 🚀 启动应用程序...
echo 🚀 Starting application...
echo.

python run.py

if errorlevel 1 (
    echo.
    echo ❌ 应用程序启动失败
    echo ❌ Application failed to start
    echo.
    echo 请检查依赖项是否已安装:
    echo Please check if dependencies are installed:
    echo   pip install -r requirements.txt
    echo.
    pause
)

echo.
echo 👋 应用程序已退出
echo 👋 Application exited
pause