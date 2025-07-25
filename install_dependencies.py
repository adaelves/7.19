#!/usr/bin/env python3
"""
视频下载器依赖安装脚本
Video Downloader Dependencies Installation Script
"""
import sys
import subprocess
import os
from pathlib import Path

def run_command(command, description):
    """运行命令并显示结果"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} 成功")
            return True
        else:
            print(f"❌ {description} 失败:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ {description} 出错: {e}")
        return False

def check_python_version():
    """检查Python版本"""
    print("🐍 检查Python版本...")
    version = sys.version_info
    if version >= (3, 8):
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - 版本符合要求")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - 需要Python 3.8+")
        print("请从 https://www.python.org/downloads/ 下载并安装Python 3.8+")
        return False

def upgrade_pip():
    """升级pip"""
    return run_command(
        f"{sys.executable} -m pip install --upgrade pip",
        "升级pip到最新版本"
    )

def install_requirements():
    """安装requirements.txt中的依赖"""
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("❌ requirements.txt 文件不存在")
        return False
    
    return run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "安装项目依赖"
    )

def install_optional_dependencies():
    """安装可选依赖"""
    optional_deps = [
        ("cryptography", "加密支持"),
        ("psutil", "系统监控"),
    ]
    
    print("\n📦 安装可选依赖...")
    for package, description in optional_deps:
        success = run_command(
            f"{sys.executable} -m pip install {package}",
            f"安装 {package} ({description})"
        )
        if not success:
            print(f"⚠️  {package} 安装失败，但不影响核心功能")

def verify_installation():
    """验证安装"""
    print("\n🔍 验证安装...")
    
    # 检查核心依赖
    core_packages = ['PySide6', 'yt_dlp', 'requests', 'aiohttp', 'aiofiles']
    
    all_good = True
    for package in core_packages:
        try:
            __import__(package)
            print(f"✅ {package} 安装成功")
        except ImportError:
            print(f"❌ {package} 安装失败")
            all_good = False
    
    return all_good

def main():
    """主函数"""
    print("=" * 60)
    print("🎬 视频下载器依赖安装")
    print("Video Downloader Dependencies Installation")
    print("=" * 60)
    
    # 检查Python版本
    if not check_python_version():
        return 1
    
    print("\n" + "=" * 60)
    print("📦 开始安装依赖...")
    print("=" * 60)
    
    steps = [
        ("升级pip", upgrade_pip),
        ("安装核心依赖", install_requirements),
        ("安装可选依赖", install_optional_dependencies),
        ("验证安装", verify_installation),
    ]
    
    for step_name, step_func in steps:
        print(f"\n📋 步骤: {step_name}")
        print("-" * 40)
        
        if not step_func():
            if step_name in ["升级pip", "安装可选依赖"]:
                print(f"⚠️  {step_name} 失败，但继续执行...")
                continue
            else:
                print(f"❌ {step_name} 失败，安装中止")
                return 1
    
    print("\n" + "=" * 60)
    print("🎉 依赖安装完成！")
    print("=" * 60)
    
    print("\n📋 下一步:")
    print("1. 运行验证脚本: python verify_installation.py")
    print("2. 启动应用: python run.py")
    print("3. 或使用启动脚本:")
    print("   - Windows: run_VideoDownloader.bat")
    print("   - Linux/macOS: ./run_VideoDownloader.sh")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())