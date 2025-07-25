#!/usr/bin/env python3
"""
视频下载器启动脚本
Multi-platform Video Downloader Launcher
"""
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Main launcher function"""
    print("=" * 50)
    print("🎬 多平台视频下载器 v1.0.0")
    print("Multi-platform Video Downloader v1.0.0")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ 错误: 需要Python 3.8或更高版本")
        print("❌ Error: Python 3.8+ required")
        sys.exit(1)
    
    # Check dependencies
    try:
        import PySide6
        print("✅ PySide6 已安装")
    except ImportError:
        print("❌ 错误: PySide6未安装，请运行: pip install PySide6")
        print("❌ Error: PySide6 not installed, run: pip install PySide6")
        sys.exit(1)
    
    try:
        import yt_dlp
        print("✅ yt-dlp 已安装")
    except ImportError:
        print("❌ 错误: yt-dlp未安装，请运行: pip install yt-dlp")
        print("❌ Error: yt-dlp not installed, run: pip install yt-dlp")
        sys.exit(1)
    
    print("✅ 所有依赖项检查通过")
    print("✅ All dependencies check passed")
    print()
    
    # Launch application
    try:
        print("🚀 启动混合界面...")
        print("🚀 Starting hybrid interface...")
        
        from app.main_hybrid import main as hybrid_main
        return hybrid_main()
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print(f"❌ Launch failed: {e}")
        
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())