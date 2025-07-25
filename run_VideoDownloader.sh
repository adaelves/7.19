#!/bin/bash

# 视频下载器启动脚本
# Video Downloader Launch Script

echo "================================================"
echo "🎬 多平台视频下载器 v1.0.0"
echo "Multi-platform Video Downloader v1.0.0"
echo "================================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "❌ 错误: Python未安装"
        echo "❌ Error: Python not installed"
        echo
        echo "请安装Python 3.8或更高版本"
        echo "Please install Python 3.8 or higher"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
echo "✅ $PYTHON_VERSION"

# Check if we're in the right directory
if [ ! -f "run.py" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Make sure the script is executable
chmod +x "$0"

# Run the application
echo
echo "🚀 启动应用程序..."
echo "🚀 Starting application..."
echo

$PYTHON_CMD run.py

EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo
    echo "❌ 应用程序启动失败 (退出代码: $EXIT_CODE)"
    echo "❌ Application failed to start (exit code: $EXIT_CODE)"
    echo
    echo "请检查依赖项是否已安装:"
    echo "Please check if dependencies are installed:"
    echo "  pip install -r requirements.txt"
    echo
fi

echo
echo "👋 应用程序已退出"
echo "👋 Application exited"