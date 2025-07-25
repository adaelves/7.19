"""
系统集成功能演示
展示托盘图标、老板键、系统通知等功能
"""
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QTextEdit
from PySide6.QtCore import Qt, QTimer

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.system_integration_service import SystemIntegrationService


class SystemIntegrationDemo(QMainWindow):
    """系统集成功能演示窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("系统集成功能演示")
        self.setGeometry(100, 100, 600, 500)
        
        # 初始化系统集成服务
        self.system_integration = SystemIntegrationService(self)
        
        self.setup_ui()
        self.setup_connections()
        self.setup_system_integration()
        
    def setup_ui(self):
        """设置用户界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title = QLabel("系统集成功能演示")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # 功能说明
        info_text = QTextEdit()
        info_text.setMaximumHeight(120)
        info_text.setReadOnly(True)
        info_text.setPlainText(
            "本演示展示以下系统集成功能：\n"
            "• 系统托盘图标和右键菜单\n"
            "• 老板键快速隐藏窗口 (默认: Ctrl+Shift+H)\n"
            "• 系统通知功能\n"
            "• 窗口最小化到托盘\n"
            "• 开机启动设置\n"
            "• 协议和文件关联注册"
        )
        layout.addWidget(info_text)
        
        # 托盘功能测试
        tray_label = QLabel("托盘功能测试:")
        tray_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(tray_label)
        
        self.show_tray_btn = QPushButton("显示托盘图标")
        layout.addWidget(self.show_tray_btn)
        
        self.hide_tray_btn = QPushButton("隐藏托盘图标")
        layout.addWidget(self.hide_tray_btn)
        
        self.hide_to_tray_btn = QPushButton("最小化到托盘")
        layout.addWidget(self.hide_to_tray_btn)
        
        # 通知功能测试
        notify_label = QLabel("通知功能测试:")
        notify_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(notify_label)
        
        self.test_notify_btn = QPushButton("测试系统通知")
        layout.addWidget(self.test_notify_btn)
        
        self.download_complete_btn = QPushButton("模拟下载完成通知")
        layout.addWidget(self.download_complete_btn)
        
        self.download_failed_btn = QPushButton("模拟下载失败通知")
        layout.addWidget(self.download_failed_btn)
        
        # 系统集成测试
        integration_label = QLabel("系统集成测试:")
        integration_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(integration_label)
        
        self.test_startup_btn = QPushButton("测试开机启动设置")
        layout.addWidget(self.test_startup_btn)
        
        self.test_protocol_btn = QPushButton("测试协议注册")
        layout.addWidget(self.test_protocol_btn)
        
        self.test_file_assoc_btn = QPushButton("测试文件关联")
        layout.addWidget(self.test_file_assoc_btn)
        
        # 状态显示
        self.status_label = QLabel("状态: 就绪")
        self.status_label.setStyleSheet("color: green; margin-top: 10px;")
        layout.addWidget(self.status_label)
        
    def setup_connections(self):
        """设置信号连接"""
        # 托盘功能
        self.show_tray_btn.clicked.connect(self.show_tray_icon)
        self.hide_tray_btn.clicked.connect(self.hide_tray_icon)
        self.hide_to_tray_btn.clicked.connect(self.hide_to_tray)
        
        # 通知功能
        self.test_notify_btn.clicked.connect(self.test_notification)
        self.download_complete_btn.clicked.connect(self.test_download_complete)
        self.download_failed_btn.clicked.connect(self.test_download_failed)
        
        # 系统集成功能
        self.test_startup_btn.clicked.connect(self.test_startup)
        self.test_protocol_btn.clicked.connect(self.test_protocol)
        self.test_file_assoc_btn.clicked.connect(self.test_file_associations)
        
    def setup_system_integration(self):
        """设置系统集成功能"""
        # 连接系统集成服务的信号
        self.system_integration.show_window_requested.connect(self.show_and_raise)
        self.system_integration.hide_window_requested.connect(self.hide_to_tray)
        self.system_integration.quit_requested.connect(self.close)
        
        # 显示托盘图标
        self.system_integration.show_tray_icon()
        
        # 设置窗口关闭行为
        self.setAttribute(Qt.WA_QuitOnClose, False)
        
        self.update_status("系统集成服务已初始化")
        
    def show_tray_icon(self):
        """显示托盘图标"""
        self.system_integration.show_tray_icon()
        self.update_status("托盘图标已显示")
        
    def hide_tray_icon(self):
        """隐藏托盘图标"""
        self.system_integration.hide_tray_icon()
        self.update_status("托盘图标已隐藏")
        
    def hide_to_tray(self):
        """隐藏到托盘"""
        self.hide()
        self.system_integration.show_notification(
            "演示程序",
            "窗口已最小化到系统托盘，双击托盘图标可重新显示",
            3000
        )
        self.update_status("窗口已隐藏到托盘")
        
    def show_and_raise(self):
        """显示并激活窗口"""
        self.show()
        self.raise_()
        self.activateWindow()
        self.update_status("窗口已从托盘恢复")
        
    def test_notification(self):
        """测试系统通知"""
        self.system_integration.show_notification(
            "测试通知",
            "这是一个测试通知消息，用于验证系统通知功能是否正常工作。",
            5000
        )
        self.update_status("已发送测试通知")
        
    def test_download_complete(self):
        """测试下载完成通知"""
        self.system_integration.show_download_complete_notification("示例视频.mp4")
        self.update_status("已发送下载完成通知")
        
    def test_download_failed(self):
        """测试下载失败通知"""
        self.system_integration.show_download_failed_notification("示例视频.mp4", "网络连接超时")
        self.update_status("已发送下载失败通知")
        
    def test_startup(self):
        """测试开机启动设置"""
        current_status = self.system_integration.is_startup_enabled()
        new_status = not current_status
        
        success = self.system_integration.enable_startup(new_status)
        if success:
            status_text = "已启用" if new_status else "已禁用"
            self.update_status(f"开机启动{status_text}")
            self.system_integration.show_notification(
                "开机启动设置",
                f"开机启动已{status_text}",
                3000
            )
        else:
            self.update_status("开机启动设置失败", error=True)
            
    def test_protocol(self):
        """测试协议注册"""
        success = self.system_integration.register_protocol_handler("videodemo")
        if success:
            self.update_status("协议注册成功")
            self.system_integration.show_notification(
                "协议注册",
                "videodemo:// 协议已注册成功",
                3000
            )
        else:
            self.update_status("协议注册失败", error=True)
            
    def test_file_associations(self):
        """测试文件关联"""
        test_extensions = ['.mp4', '.avi']
        success = self.system_integration.register_file_associations(test_extensions)
        if success:
            self.update_status("文件关联注册成功")
            self.system_integration.show_notification(
                "文件关联",
                f"已注册 {len(test_extensions)} 种文件格式关联",
                3000
            )
        else:
            self.update_status("文件关联注册失败", error=True)
            
    def update_status(self, message: str, error: bool = False):
        """更新状态显示"""
        color = "red" if error else "green"
        self.status_label.setText(f"状态: {message}")
        self.status_label.setStyleSheet(f"color: {color}; margin-top: 10px;")
        
        # 3秒后恢复默认状态
        QTimer.singleShot(3000, lambda: self.reset_status())
        
    def reset_status(self):
        """重置状态显示"""
        self.status_label.setText("状态: 就绪")
        self.status_label.setStyleSheet("color: green; margin-top: 10px;")
        
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 如果托盘图标可用，最小化到托盘
        if (self.system_integration.tray_icon and 
            self.system_integration.tray_icon.isVisible()):
            event.ignore()
            self.hide_to_tray()
        else:
            # 清理资源
            self.system_integration.cleanup()
            event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("SystemIntegrationDemo")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("VideoDownloader")
    
    # 创建并显示演示窗口
    demo = SystemIntegrationDemo()
    demo.show()
    
    # 显示启动通知
    demo.system_integration.show_notification(
        "系统集成演示",
        "演示程序已启动，请测试各项功能",
        3000
    )
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())