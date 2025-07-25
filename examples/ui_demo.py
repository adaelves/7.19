"""
改进后的macOS风格界面演示 - 基于HTML版本设计
展示完整的用户界面和功能整合
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from app.ui.main_window import MacOSMainWindow
from app.core.config import config_manager


class UIDemo(QWidget):
    """界面演示启动器"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """设置启动器界面"""
        self.setWindowTitle("多平台视频下载器 - 界面演示")
        self.setGeometry(200, 200, 500, 400)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # 标题
        title = QLabel("多平台视频下载器")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("SF Pro Display", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #1d1d1f; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # 副标题
        subtitle = QLabel("基于HTML设计的macOS风格界面")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setFont(QFont("SF Pro Text", 16))
        subtitle.setStyleSheet("color: #8e8e93; margin-bottom: 30px;")
        layout.addWidget(subtitle)
        
        # 功能介绍
        features = QLabel(
            "✨ 界面特色：\n\n"
            "• macOS原生风格设计，完美还原HTML版本\n"
            "• 标签页导航：历史记录、创作者监控、首选项\n"
            "• 智能搜索栏：支持URL直接添加和视频搜索\n"
            "• 增强状态栏：实时显示下载统计和控制\n"
            "• 完整设置系统：代理配置、主题切换、路径管理\n"
            "• 响应式布局：适配不同窗口大小\n"
            "• 流畅动画：提供优秀的用户体验"
        )
        features.setWordWrap(True)
        features.setStyleSheet("""
            color: #1d1d1f;
            font-size: 14px;
            line-height: 1.6;
            background-color: #f2f2f7;
            border: 1px solid #c6c6c8;
            border-radius: 12px;
            padding: 20px;
        """)
        layout.addWidget(features)
        
        layout.addStretch()
        
        # 启动按钮
        start_btn = QPushButton("🚀 启动主界面")
        start_btn.setFont(QFont("SF Pro Text", 16, QFont.Weight.Medium))
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: #0071e3;
                color: white;
                border: none;
                border-radius: 12px;
                padding: 16px 32px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #0051cc;
            }
            QPushButton:pressed {
                background-color: #004499;
            }
        """)
        start_btn.clicked.connect(self.launch_main_window)
        layout.addWidget(start_btn)
        
        # 说明文字
        note = QLabel("点击按钮启动主界面，体验完整的功能和设计")
        note.setAlignment(Qt.AlignCenter)
        note.setStyleSheet("color: #8e8e93; font-size: 12px; margin-top: 10px;")
        layout.addWidget(note)
        
    def launch_main_window(self):
        """启动主窗口"""
        self.main_window = MacOSMainWindow()
        self.main_window.show()
        
        # 添加一些示例数据
        self.add_sample_data()
        
        # 隐藏启动器
        self.hide()
        
        print("🎉 主界面已启动！")
        print("\n📋 功能说明：")
        print("1. 标签页导航：")
        print("   • 历史记录 - 查看下载历史和管理")
        print("   • 创作者监控 - 监控喜欢的创作者")
        print("   • 首选项 - 快速设置和高级配置")
        print("\n2. 搜索功能：")
        print("   • 直接粘贴视频URL进行下载")
        print("   • 搜索关键词查找视频")
        print("   • 支持批量添加和队列管理")
        print("\n3. 设置系统：")
        print("   • 点击右上角设置按钮打开完整设置")
        print("   • 支持主题切换、代理配置、路径管理等")
        print("   • 实时预览和保存功能")
        print("\n4. 状态管理：")
        print("   • 底部状态栏显示下载统计")
        print("   • 支持全部暂停/开始操作")
        print("   • 实时更新下载状态")
        
    def add_sample_data(self):
        """添加示例数据"""
        # 模拟添加一些下载任务
        sample_urls = [
            "https://www.bilibili.com/video/BV1234567890",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.douyin.com/video/1234567890"
        ]
        
        for url in sample_urls:
            self.main_window.add_download_from_url(url)
        
        # 更新状态信息
        self.main_window.update_status_info()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序属性
    app.setApplicationName("多平台视频下载器")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("Video Downloader Pro")
    
    # 设置应用程序字体
    font = QFont("SF Pro Text", 13)
    app.setFont(font)
    
    # 创建并显示启动器
    demo = UIDemo()
    demo.show()
    
    print("🎬 多平台视频下载器界面演示")
    print("=" * 50)
    print("基于您的HTML设计，我们重新设计了PySide6界面：")
    print("\n🎨 设计改进：")
    print("• 完全还原HTML版本的macOS风格")
    print("• 标题栏：经典的红绿黄窗口控制按钮")
    print("• 导航栏：标签页式导航，清晰的功能分类")
    print("• 搜索栏：智能输入框，支持URL和搜索")
    print("• 状态栏：增强的状态显示和控制")
    print("\n🚀 功能整合：")
    print("• 统一的设置系统，包含所有配置选项")
    print("• 智能的URL处理和视频搜索")
    print("• 完整的下载管理和状态跟踪")
    print("• 响应式的界面布局和主题切换")
    print("\n💡 用户体验：")
    print("• 直观的操作流程和视觉反馈")
    print("• 流畅的动画和过渡效果")
    print("• 一致的设计语言和交互模式")
    print("• 完善的错误处理和提示信息")
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())