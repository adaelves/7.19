#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多平台视频下载器 - 统一主程序入口
支持多种界面风格选择
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QFont

# 导入不同的界面实现
from app.ui.html_style_window import HTMLStyleWindow
from app.ui.main_window import MacOSMainWindow


def setup_application():
    """设置应用程序基本配置"""
    app = QApplication(sys.argv)
    
    # 设置应用程序基本信息
    app.setApplicationName("多平台视频下载器")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("VideoDownloader")
    app.setOrganizationDomain("videodownloader.com")
    
    # 设置应用程序图标
    if os.path.exists("assets/icon.png"):
        app.setWindowIcon(QIcon("assets/icon.png"))
    
    # 设置字体
    font = QFont("SF Pro Text")
    if not font.exactMatch():
        font = QFont("-apple-system")
        if not font.exactMatch():
            font = QFont("Segoe UI")
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)
    
    # 启用高DPI支持
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    return app


def choose_interface_style():
    """选择界面风格"""
    # 检查命令行参数
    if len(sys.argv) > 1:
        style = sys.argv[1].lower()
        if style in ['html', 'native']:
            return style
    
    # 默认使用HTML风格（推荐）
    return 'html'


def check_dependencies():
    """检查依赖项"""
    print("🔍 检查依赖项...")
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 错误: 需要Python 3.8或更高版本")
        return False
    
    # 检查PySide6
    try:
        import PySide6
        print("✅ PySide6 已安装")
    except ImportError:
        print("❌ 错误: PySide6未安装，请运行: pip install PySide6")
        return False
    
    # 检查yt-dlp
    try:
        import yt_dlp
        print("✅ yt-dlp 已安装")
    except ImportError:
        print("❌ 错误: yt-dlp未安装，请运行: pip install yt-dlp")
        return False
    
    print("✅ 所有依赖项检查通过")
    return True


def main():
    """主函数"""
    print("=" * 60)
    print("🎬 多平台视频下载器 v2.0.0")
    print("Multi-platform Video Downloader v2.0.0")
    print("=" * 60)
    
    # 检查依赖项
    if not check_dependencies():
        return 1
    
    try:
        # 设置应用程序
        app = setup_application()
        
        # 选择界面风格
        interface_style = choose_interface_style()
        
        # 创建对应的主窗口
        if interface_style == 'html':
            # HTML风格界面（推荐）- 完全按照HTML设计实现
            main_window = HTMLStyleWindow()
            print("🎨 启动HTML风格界面 - 完全按照设计稿实现")
        else:
            # 原生macOS风格界面
            main_window = MacOSMainWindow()
            print("🍎 启动macOS原生风格界面")
        
        # 显示主窗口
        main_window.show()
        
        print(f"✅ 多平台视频下载器已启动")
        print(f"💡 提示: 可以使用 'python run.py html' 或 'python run.py native' 选择界面风格")
        print("=" * 60)
        
        # 运行应用程序
        return app.exec()
        
    except Exception as e:
        print(f"❌ 应用程序启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())