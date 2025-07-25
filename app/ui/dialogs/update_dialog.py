"""
Update dialog for displaying available updates and managing update process.
"""

import asyncio
from typing import Optional
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QProgressBar, QTextEdit, QCheckBox, QGroupBox, QSpinBox,
    QMessageBox, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QPixmap, QIcon

from app.services.update_service import UpdateService, ReleaseInfo, UpdateProgress


class UpdateWorker(QThread):
    """Worker thread for update operations"""
    
    progress_updated = Signal(object)  # UpdateProgress
    update_completed = Signal(bool)    # success
    
    def __init__(self, update_service: UpdateService, release_info: ReleaseInfo):
        super().__init__()
        self.update_service = update_service
        self.release_info = release_info
        self.should_stop = False
        
        # Set progress callback
        self.update_service.set_progress_callback(self.on_progress)
    
    def on_progress(self, progress: UpdateProgress):
        """Handle progress updates from update service"""
        self.progress_updated.emit(progress)
    
    def run(self):
        """Run update process"""
        try:
            # Create event loop for async operations
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Download update
            if self.should_stop:
                return
            
            download_path = loop.run_until_complete(
                self.update_service.download_update(self.release_info)
            )
            
            if self.should_stop:
                return
            
            # Extract update
            extract_path = loop.run_until_complete(
                self.update_service.extract_update(download_path)
            )
            
            if self.should_stop:
                return
            
            # Install update
            success = loop.run_until_complete(
                self.update_service.install_update(extract_path, backup=True)
            )
            
            self.update_completed.emit(success)
            
        except Exception as e:
            progress = UpdateProgress("error", 0.0, "更新失败", str(e))
            self.progress_updated.emit(progress)
            self.update_completed.emit(False)
        finally:
            loop.close()
    
    def stop(self):
        """Stop update process"""
        self.should_stop = True


class UpdateNotificationDialog(QDialog):
    """Simple notification dialog for available updates"""
    
    def __init__(self, release_info: ReleaseInfo, parent=None):
        super().__init__(parent)
        self.release_info = release_info
        self.setup_ui()
    
    def setup_ui(self):
        """Setup notification dialog UI"""
        self.setWindowTitle("发现新版本")
        self.setFixedSize(400, 300)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Icon and title
        header_layout = QHBoxLayout()
        
        # Update icon (you can add an actual icon here)
        icon_label = QLabel("🔄")
        icon_label.setFont(QFont("", 24))
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(f"新版本 {self.release_info.version} 可用")
        title_label.setFont(QFont("", 14, QFont.Bold))
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Current vs new version
        version_frame = QFrame()
        version_frame.setFrameStyle(QFrame.Box)
        version_layout = QVBoxLayout(version_frame)
        
        current_label = QLabel(f"当前版本: {self.get_current_version()}")
        new_label = QLabel(f"最新版本: {self.release_info.version}")
        new_label.setStyleSheet("color: #007AFF; font-weight: bold;")
        
        version_layout.addWidget(current_label)
        version_layout.addWidget(new_label)
        layout.addWidget(version_frame)
        
        # Release date
        date_label = QLabel(f"发布日期: {self.release_info.release_date.strftime('%Y-%m-%d')}")
        date_label.setStyleSheet("color: #666;")
        layout.addWidget(date_label)
        
        # Changelog preview
        changelog_label = QLabel("更新内容:")
        changelog_label.setFont(QFont("", 10, QFont.Bold))
        layout.addWidget(changelog_label)
        
        changelog_text = QTextEdit()
        changelog_text.setPlainText(self.release_info.changelog[:200] + "..." if len(self.release_info.changelog) > 200 else self.release_info.changelog)
        changelog_text.setMaximumHeight(80)
        changelog_text.setReadOnly(True)
        layout.addWidget(changelog_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        later_btn = QPushButton("稍后提醒")
        later_btn.clicked.connect(self.reject)
        
        details_btn = QPushButton("查看详情")
        details_btn.clicked.connect(self.show_details)
        
        update_btn = QPushButton("立即更新")
        update_btn.clicked.connect(self.accept)
        update_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056CC;
            }
        """)
        
        button_layout.addWidget(later_btn)
        button_layout.addWidget(details_btn)
        button_layout.addWidget(update_btn)
        
        layout.addLayout(button_layout)
    
    def get_current_version(self) -> str:
        """Get current application version"""
        try:
            version_file = Path("version.txt")
            if version_file.exists():
                return version_file.read_text().strip()
            return "1.0.0"
        except Exception:
            return "1.0.0"
    
    def show_details(self):
        """Show detailed update information"""
        dialog = UpdateDialog(self.release_info, self.parent())
        dialog.exec()


class UpdateDialog(QDialog):
    """Main update dialog with full functionality"""
    
    def __init__(self, release_info: ReleaseInfo, parent=None):
        super().__init__(parent)
        self.release_info = release_info
        self.update_service = None
        self.update_worker = None
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup main update dialog UI"""
        self.setWindowTitle(f"更新到版本 {self.release_info.version}")
        self.setFixedSize(600, 500)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        icon_label = QLabel("🔄")
        icon_label.setFont(QFont("", 32))
        header_layout.addWidget(icon_label)
        
        title_layout = QVBoxLayout()
        title_label = QLabel(f"更新到版本 {self.release_info.version}")
        title_label.setFont(QFont("", 16, QFont.Bold))
        
        subtitle_label = QLabel(f"发布于 {self.release_info.release_date.strftime('%Y年%m月%d日')}")
        subtitle_label.setStyleSheet("color: #666;")
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Version comparison
        version_group = QGroupBox("版本信息")
        version_layout = QVBoxLayout(version_group)
        
        current_label = QLabel(f"当前版本: {self.get_current_version()}")
        new_label = QLabel(f"最新版本: {self.release_info.version}")
        size_label = QLabel(f"下载大小: {self.format_file_size(self.release_info.file_size)}")
        
        version_layout.addWidget(current_label)
        version_layout.addWidget(new_label)
        version_layout.addWidget(size_label)
        
        layout.addWidget(version_group)
        
        # Changelog
        changelog_group = QGroupBox("更新内容")
        changelog_layout = QVBoxLayout(changelog_group)
        
        self.changelog_text = QTextEdit()
        self.changelog_text.setPlainText(self.release_info.changelog)
        self.changelog_text.setReadOnly(True)
        self.changelog_text.setMaximumHeight(150)
        
        changelog_layout.addWidget(self.changelog_text)
        layout.addWidget(changelog_group)
        
        # Progress section
        progress_group = QGroupBox("更新进度")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        self.status_label = QLabel("准备更新...")
        self.status_label.setVisible(False)
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        
        layout.addWidget(progress_group)
        
        # Options
        options_group = QGroupBox("更新选项")
        options_layout = QVBoxLayout(options_group)
        
        self.backup_checkbox = QCheckBox("创建当前版本备份")
        self.backup_checkbox.setChecked(True)
        
        self.auto_restart_checkbox = QCheckBox("更新完成后自动重启应用")
        self.auto_restart_checkbox.setChecked(True)
        
        options_layout.addWidget(self.backup_checkbox)
        options_layout.addWidget(self.auto_restart_checkbox)
        
        layout.addWidget(options_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.update_btn = QPushButton("开始更新")
        self.update_btn.clicked.connect(self.start_update)
        self.update_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056CC;
            }
            QPushButton:disabled {
                background-color: #CCC;
            }
        """)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.update_btn)
        
        layout.addLayout(button_layout)
    
    def setup_connections(self):
        """Setup signal connections"""
        pass
    
    def set_update_service(self, update_service: UpdateService):
        """Set update service instance"""
        self.update_service = update_service
    
    def get_current_version(self) -> str:
        """Get current application version"""
        try:
            version_file = Path("version.txt")
            if version_file.exists():
                return version_file.read_text().strip()
            return "1.0.0"
        except Exception:
            return "1.0.0"
    
    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "未知"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def start_update(self):
        """Start update process"""
        if not self.update_service:
            QMessageBox.warning(self, "错误", "更新服务未初始化")
            return
        
        # Show progress UI
        self.progress_bar.setVisible(True)
        self.status_label.setVisible(True)
        self.update_btn.setEnabled(False)
        self.cancel_btn.setText("停止")
        
        # Start update worker
        self.update_worker = UpdateWorker(self.update_service, self.release_info)
        self.update_worker.progress_updated.connect(self.on_progress_updated)
        self.update_worker.update_completed.connect(self.on_update_completed)
        self.update_worker.start()
    
    def on_progress_updated(self, progress: UpdateProgress):
        """Handle progress updates"""
        self.progress_bar.setValue(int(progress.progress * 100))
        self.status_label.setText(progress.message)
        
        if progress.stage == "error":
            self.status_label.setStyleSheet("color: red;")
            self.update_btn.setEnabled(True)
            self.cancel_btn.setText("关闭")
        elif progress.stage == "complete":
            self.status_label.setStyleSheet("color: green;")
    
    def on_update_completed(self, success: bool):
        """Handle update completion"""
        if success:
            self.status_label.setText("更新完成!")
            self.status_label.setStyleSheet("color: green;")
            
            if self.auto_restart_checkbox.isChecked():
                QMessageBox.information(self, "更新完成", "更新已完成，应用将重新启动。")
                # Here you would implement application restart logic
                self.accept()
            else:
                QMessageBox.information(self, "更新完成", "更新已完成，请手动重启应用以使用新版本。")
                self.accept()
        else:
            self.status_label.setText("更新失败")
            self.status_label.setStyleSheet("color: red;")
            self.update_btn.setEnabled(True)
            self.cancel_btn.setText("关闭")
    
    def reject(self):
        """Handle dialog rejection"""
        if self.update_worker and self.update_worker.isRunning():
            reply = QMessageBox.question(
                self, "确认", "更新正在进行中，确定要取消吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.update_worker.stop()
                self.update_worker.wait()
                super().reject()
        else:
            super().reject()


class UpdateSettingsDialog(QDialog):
    """Dialog for configuring update settings"""
    
    def __init__(self, update_service: UpdateService, parent=None):
        super().__init__(parent)
        self.update_service = update_service
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Setup settings dialog UI"""
        self.setWindowTitle("更新设置")
        self.setFixedSize(400, 300)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Auto check settings
        auto_group = QGroupBox("自动检查更新")
        auto_layout = QVBoxLayout(auto_group)
        
        self.auto_check_checkbox = QCheckBox("启用自动检查更新")
        auto_layout.addWidget(self.auto_check_checkbox)
        
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("检查间隔:"))
        
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(1, 168)  # 1 hour to 1 week
        self.interval_spinbox.setSuffix(" 小时")
        interval_layout.addWidget(self.interval_spinbox)
        interval_layout.addStretch()
        
        auto_layout.addLayout(interval_layout)
        layout.addWidget(auto_group)
        
        # Advanced settings
        advanced_group = QGroupBox("高级设置")
        advanced_layout = QVBoxLayout(advanced_group)
        
        self.prerelease_checkbox = QCheckBox("包含预发布版本")
        advanced_layout.addWidget(self.prerelease_checkbox)
        
        layout.addWidget(advanced_group)
        
        # Current version info
        info_group = QGroupBox("版本信息")
        info_layout = QVBoxLayout(info_group)
        
        current_version = self.update_service.current_version
        version_label = QLabel(f"当前版本: {current_version}")
        info_layout.addWidget(version_label)
        
        last_check = self.update_service.config_service.get("update.last_check")
        if last_check:
            from datetime import datetime
            last_check_time = datetime.fromisoformat(last_check)
            last_check_label = QLabel(f"上次检查: {last_check_time.strftime('%Y-%m-%d %H:%M')}")
        else:
            last_check_label = QLabel("上次检查: 从未")
        
        info_layout.addWidget(last_check_label)
        layout.addWidget(info_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        check_now_btn = QPushButton("立即检查")
        check_now_btn.clicked.connect(self.check_now)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.save_settings)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056CC;
            }
        """)
        
        button_layout.addWidget(check_now_btn)
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def load_settings(self):
        """Load current settings"""
        settings = self.update_service.get_update_settings()
        
        self.auto_check_checkbox.setChecked(settings["auto_check"])
        self.interval_spinbox.setValue(settings["check_interval"])
        self.prerelease_checkbox.setChecked(settings["include_prereleases"])
    
    def save_settings(self):
        """Save settings"""
        settings = {
            "auto_check": self.auto_check_checkbox.isChecked(),
            "check_interval": self.interval_spinbox.value(),
            "include_prereleases": self.prerelease_checkbox.isChecked()
        }
        
        self.update_service.update_settings(settings)
        self.accept()
    
    def check_now(self):
        """Check for updates now"""
        # This would trigger an immediate update check
        # Implementation depends on how you want to handle this
        QMessageBox.information(self, "检查更新", "正在检查更新...")