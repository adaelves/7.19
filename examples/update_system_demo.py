"""
Update system demonstration script.
Shows how to use the update system components.
"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QTextEdit
from PySide6.QtCore import QTimer

from app.services.config_service import ConfigService
from app.services.update_service import UpdateService
from app.core.updater import AutoUpdater, UpdateManager
from app.ui.dialogs.update_dialog import UpdateNotificationDialog, UpdateDialog, UpdateSettingsDialog
from app.ui.dialogs.changelog_dialog import ChangelogDialog
from app.ui.components.update_progress import UpdateProgressWidget, CompactUpdateIndicator


class UpdateSystemDemo(QMainWindow):
    """Demo window for update system"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("更新系统演示")
        self.setGeometry(100, 100, 800, 600)
        
        # Initialize services
        self.config_service = ConfigService("demo_config.json")
        self.update_service = UpdateService(self.config_service)
        self.auto_updater = AutoUpdater(self.config_service)
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup demo UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("更新系统功能演示")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Update indicator
        self.update_indicator = CompactUpdateIndicator()
        self.update_indicator.clicked.connect(self.show_update_info)
        layout.addWidget(self.update_indicator)
        
        # Progress widget
        self.progress_widget = UpdateProgressWidget()
        self.progress_widget.cancel_requested.connect(self.cancel_update)
        self.progress_widget.retry_requested.connect(self.retry_update)
        layout.addWidget(self.progress_widget)
        
        # Control buttons
        self.check_btn = QPushButton("检查更新")
        self.check_btn.clicked.connect(self.check_updates)
        layout.addWidget(self.check_btn)
        
        self.notification_btn = QPushButton("显示更新通知")
        self.notification_btn.clicked.connect(self.show_update_notification)
        layout.addWidget(self.notification_btn)
        
        self.dialog_btn = QPushButton("显示更新对话框")
        self.dialog_btn.clicked.connect(self.show_update_dialog)
        layout.addWidget(self.dialog_btn)
        
        self.changelog_btn = QPushButton("显示更新日志")
        self.changelog_btn.clicked.connect(self.show_changelog)
        layout.addWidget(self.changelog_btn)
        
        self.settings_btn = QPushButton("更新设置")
        self.settings_btn.clicked.connect(self.show_update_settings)
        layout.addWidget(self.settings_btn)
        
        # Simulate progress button
        self.simulate_btn = QPushButton("模拟更新进度")
        self.simulate_btn.clicked.connect(self.simulate_update_progress)
        layout.addWidget(self.simulate_btn)
        
        # Log area
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setPlaceholderText("操作日志将显示在这里...")
        layout.addWidget(self.log_text)
        
        # Status
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("padding: 5px; background-color: #f0f0f0; border-radius: 3px;")
        layout.addWidget(self.status_label)
    
    def setup_connections(self):
        """Setup signal connections"""
        # Connect update service callbacks
        self.update_service.set_progress_callback(self.on_progress_update)
        self.auto_updater.update_available.connect(self.on_update_available)
        self.auto_updater.error_occurred.connect(self.on_update_error)
    
    def log_message(self, message):
        """Add message to log"""
        self.log_text.append(f"[{self.get_timestamp()}] {message}")
    
    def get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
    
    def check_updates(self):
        """Check for updates"""
        self.log_message("开始检查更新...")
        self.status_label.setText("检查更新中...")
        self.update_indicator.set_updating(True)
        
        # Simulate update check
        QTimer.singleShot(2000, self.simulate_update_check_result)
    
    def simulate_update_check_result(self):
        """Simulate update check result"""
        import random
        
        if random.choice([True, False]):
            # Simulate update available
            self.log_message("发现新版本 v1.2.0")
            self.status_label.setText("发现更新")
            self.update_indicator.set_update_available(True, "v1.2.0")
        else:
            # No update available
            self.log_message("已是最新版本")
            self.status_label.setText("已是最新版本")
            self.update_indicator.set_update_available(False)
    
    def show_update_info(self):
        """Show update information"""
        self.log_message("显示更新信息")
        
        # Get version info
        current_version = self.update_service.current_version
        message = f"当前版本: {current_version}\n点击了更新指示器"
        
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "更新信息", message)
    
    def show_update_notification(self):
        """Show update notification dialog"""
        self.log_message("显示更新通知对话框")
        
        # Create mock release info
        from app.services.update_service import ReleaseInfo
        from datetime import datetime
        
        release_info = ReleaseInfo(
            version="1.2.0",
            tag_name="v1.2.0",
            release_date=datetime.now(),
            changelog="• 修复了若干bug\n• 添加了新功能\n• 性能优化",
            download_url="https://example.com/download.zip",
            file_size=10485760,  # 10MB
            is_prerelease=False
        )
        
        dialog = UpdateNotificationDialog(release_info, self)
        result = dialog.exec()
        
        if result == UpdateNotificationDialog.Accepted:
            self.log_message("用户选择立即更新")
        else:
            self.log_message("用户选择稍后更新")
    
    def show_update_dialog(self):
        """Show full update dialog"""
        self.log_message("显示完整更新对话框")
        
        # Create mock release info
        from app.services.update_service import ReleaseInfo
        from datetime import datetime
        
        release_info = ReleaseInfo(
            version="1.2.0",
            tag_name="v1.2.0",
            release_date=datetime.now(),
            changelog="""# 版本 1.2.0 更新内容

## 新增功能
• 添加了自动更新系统
• 支持更多视频平台
• 改进了用户界面

## 修复问题
• 修复了下载中断的问题
• 解决了内存泄漏
• 优化了启动速度

## 其他改进
• 更新了依赖库
• 改进了错误处理
• 增强了稳定性""",
            download_url="https://example.com/download.zip",
            file_size=10485760,  # 10MB
            is_prerelease=False
        )
        
        dialog = UpdateDialog(release_info, self)
        dialog.set_update_service(self.update_service)
        dialog.exec()
    
    def show_changelog(self):
        """Show changelog dialog"""
        self.log_message("显示更新日志")
        
        dialog = ChangelogDialog(self.update_service, self)
        dialog.exec()
    
    def show_update_settings(self):
        """Show update settings dialog"""
        self.log_message("显示更新设置")
        
        dialog = UpdateSettingsDialog(self.update_service, self)
        dialog.exec()
    
    def simulate_update_progress(self):
        """Simulate update progress"""
        self.log_message("开始模拟更新进度")
        self.progress_widget.reset()
        
        # Simulate different stages
        self.simulate_stage = 0
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress_step)
        self.progress_timer.start(500)  # Update every 500ms
    
    def update_progress_step(self):
        """Update progress step"""
        from app.services.update_service import UpdateProgress
        
        stages = [
            ("checking", "正在检查更新..."),
            ("downloading", "正在下载更新文件..."),
            ("extracting", "正在解压更新文件..."),
            ("installing", "正在安装更新..."),
            ("complete", "更新完成!")
        ]
        
        if self.simulate_stage < len(stages):
            stage, message = stages[self.simulate_stage]
            progress = (self.simulate_stage + 1) / len(stages)
            
            update_progress = UpdateProgress(stage, progress, message)
            self.progress_widget.update_progress(update_progress)
            
            self.simulate_stage += 1
        else:
            self.progress_timer.stop()
            self.log_message("模拟更新完成")
    
    def cancel_update(self):
        """Cancel update"""
        self.log_message("用户取消更新")
        if hasattr(self, 'progress_timer'):
            self.progress_timer.stop()
    
    def retry_update(self):
        """Retry update"""
        self.log_message("用户选择重试更新")
        self.simulate_update_progress()
    
    def on_progress_update(self, progress):
        """Handle progress update from update service"""
        self.log_message(f"更新进度: {progress.stage} - {progress.message}")
        self.progress_widget.update_progress(progress)
    
    def on_update_available(self, release_info):
        """Handle update available"""
        self.log_message(f"发现更新: {release_info.version}")
        self.update_indicator.set_update_available(True, release_info.version)
    
    def on_update_error(self, error_message):
        """Handle update error"""
        self.log_message(f"更新错误: {error_message}")
        self.update_indicator.set_error(error_message)


def main():
    """Main function"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("更新系统演示")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("多平台视频下载器")
    
    # Create and show demo window
    demo = UpdateSystemDemo()
    demo.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()