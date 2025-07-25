"""
设置对话框演示程序
展示完整的设置界面功能
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt

from app.ui.dialogs.settings_dialog import SettingsDialog
from app.ui.styles.theme_manager import ThemeManager


class SettingsDemo(QMainWindow):
    """设置对话框演示主窗口"""
    
    def __init__(self):
        super().__init__()
        self.theme_manager = ThemeManager()
        self.setup_ui()
        self.apply_theme()
        
    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("设置对话框演示")
        self.setGeometry(100, 100, 400, 300)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # 标题
        title = QLabel("多平台视频下载器 - 设置演示")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # 说明文本
        description = QLabel(
            "点击下面的按钮打开设置对话框，体验完整的设置功能：\n\n"
            "• 通用设置：应用程序基本配置\n"
            "• 下载设置：路径管理和文件命名模板\n"
            "• 网络设置：代理配置和连接参数\n"
            "• 外观设置：主题和界面自定义\n"
            "• 高级设置：性能优化和数据管理"
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #666; line-height: 1.5;")
        layout.addWidget(description)
        
        layout.addStretch()
        
        # 打开设置按钮
        self.settings_btn = QPushButton("打开设置对话框")
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #007aff;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #0056cc;
            }
            QPushButton:pressed {
                background-color: #004499;
            }
        """)
        self.settings_btn.clicked.connect(self.show_settings)
        layout.addWidget(self.settings_btn)
        
        # 主题切换按钮
        self.theme_btn = QPushButton("切换主题")
        self.theme_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #007aff;
                border: 1px solid #007aff;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #007aff;
                color: white;
            }
        """)
        self.theme_btn.clicked.connect(self.toggle_theme)
        layout.addWidget(self.theme_btn)
        
        # 状态标签
        self.status_label = QLabel("准备就绪")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #8e8e93; font-size: 12px; margin-top: 10px;")
        layout.addWidget(self.status_label)
        
    def show_settings(self):
        """显示设置对话框"""
        self.status_label.setText("正在打开设置对话框...")
        
        settings_dialog = SettingsDialog(self)
        settings_dialog.settings_changed.connect(self.on_settings_changed)
        
        result = settings_dialog.exec()
        
        if result == SettingsDialog.Accepted:
            self.status_label.setText("设置已保存")
        else:
            self.status_label.setText("设置已取消")
            
    def on_settings_changed(self, settings):
        """设置改变处理"""
        self.status_label.setText(f"设置已更新 - 共 {len(settings)} 项配置")
        
        # 如果主题改变，更新界面
        if 'theme' in settings:
            if settings['theme'] != self.theme_manager.current_theme:
                self.theme_manager.set_theme(settings['theme'])
                self.apply_theme()
                
        print("设置已更新:")
        for key, value in settings.items():
            print(f"  {key}: {value}")
            
    def toggle_theme(self):
        """切换主题"""
        current_theme = self.theme_manager.current_theme
        new_theme = "dark" if current_theme == "light" else "light"
        self.theme_manager.set_theme(new_theme)
        self.apply_theme()
        self.status_label.setText(f"主题已切换为: {new_theme}")
        
    def apply_theme(self):
        """应用主题"""
        stylesheet = self.theme_manager.get_stylesheet()
        self.setStyleSheet(stylesheet)
        
        # 更新主题按钮文本
        theme_text = "切换到深色主题" if self.theme_manager.current_theme == "light" else "切换到浅色主题"
        self.theme_btn.setText(theme_text)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序属性
    app.setApplicationName("设置对话框演示")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Video Downloader")
    
    # 创建并显示主窗口
    window = SettingsDemo()
    window.show()
    
    print("设置对话框演示程序已启动")
    print("功能说明:")
    print("1. 点击'打开设置对话框'按钮体验完整设置功能")
    print("2. 在设置对话框中可以:")
    print("   - 配置下载路径和文件命名模板")
    print("   - 设置网络代理和连接参数")
    print("   - 测试代理连接")
    print("   - 切换主题和调整界面")
    print("   - 管理高级选项和数据")
    print("3. 点击'切换主题'按钮体验主题切换")
    print("4. 所有设置都会实时预览和保存")
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())