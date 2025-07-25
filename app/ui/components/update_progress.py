"""
Update progress components for displaying update status and progress.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, 
    QPushButton, QFrame, QTextEdit, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor, QBrush

from app.services.update_service import UpdateProgress


class UpdateProgressWidget(QWidget):
    """Widget for displaying update progress"""
    
    # Signals
    cancel_requested = Signal()
    retry_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_stage = ""
        self.setup_ui()
        self.setup_animations()
    
    def setup_ui(self):
        """Setup progress widget UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Header with icon and title
        header_layout = QHBoxLayout()
        
        self.icon_label = QLabel("🔄")
        self.icon_label.setFont(QFont("", 24))
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedSize(40, 40)
        
        self.title_label = QLabel("正在更新...")
        self.title_label.setFont(QFont("", 14, QFont.Bold))
        
        header_layout.addWidget(self.icon_label)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Progress section
        progress_frame = QFrame()
        progress_frame.setFrameStyle(QFrame.Box)
        progress_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #DDD;
                border-radius: 8px;
                padding: 16px;
                background-color: #F8F9FA;
            }
        """)
        
        progress_layout = QVBoxLayout(progress_frame)
        
        # Stage indicator
        self.stage_label = QLabel("准备中...")
        self.stage_label.setFont(QFont("", 12, QFont.Bold))
        self.stage_label.setStyleSheet("color: #007AFF;")
        progress_layout.addWidget(self.stage_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #DDD;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
                background-color: white;
            }
            QProgressBar::chunk {
                background-color: #007AFF;
                border-radius: 6px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        # Status message
        self.status_label = QLabel("初始化更新...")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #666; margin-top: 8px;")
        progress_layout.addWidget(self.status_label)
        
        layout.addWidget(progress_frame)
        
        # Error section (initially hidden)
        self.error_frame = QFrame()
        self.error_frame.setFrameStyle(QFrame.Box)
        self.error_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #FF3B30;
                border-radius: 8px;
                padding: 16px;
                background-color: #FFF5F5;
            }
        """)
        self.error_frame.setVisible(False)
        
        error_layout = QVBoxLayout(self.error_frame)
        
        error_title = QLabel("❌ 更新失败")
        error_title.setFont(QFont("", 12, QFont.Bold))
        error_title.setStyleSheet("color: #FF3B30;")
        error_layout.addWidget(error_title)
        
        self.error_message = QLabel()
        self.error_message.setWordWrap(True)
        self.error_message.setStyleSheet("color: #666; margin-top: 8px;")
        error_layout.addWidget(self.error_message)
        
        layout.addWidget(self.error_frame)
        
        # Success section (initially hidden)
        self.success_frame = QFrame()
        self.success_frame.setFrameStyle(QFrame.Box)
        self.success_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #34C759;
                border-radius: 8px;
                padding: 16px;
                background-color: #F0FFF4;
            }
        """)
        self.success_frame.setVisible(False)
        
        success_layout = QVBoxLayout(self.success_frame)
        
        success_title = QLabel("✅ 更新完成")
        success_title.setFont(QFont("", 12, QFont.Bold))
        success_title.setStyleSheet("color: #34C759;")
        success_layout.addWidget(success_title)
        
        self.success_message = QLabel("更新已成功安装，请重启应用以使用新版本。")
        self.success_message.setWordWrap(True)
        self.success_message.setStyleSheet("color: #666; margin-top: 8px;")
        success_layout.addWidget(self.success_message)
        
        layout.addWidget(self.success_frame)
        
        # Button section
        button_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.cancel_requested.emit)
        
        self.retry_btn = QPushButton("重试")
        self.retry_btn.clicked.connect(self.retry_requested.emit)
        self.retry_btn.setVisible(False)
        self.retry_btn.setStyleSheet("""
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
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.retry_btn)
        
        layout.addLayout(button_layout)
    
    def setup_animations(self):
        """Setup progress animations"""
        # Icon rotation animation
        self.icon_animation = QPropertyAnimation(self.icon_label, b"rotation")
        self.icon_animation.setDuration(2000)
        self.icon_animation.setStartValue(0)
        self.icon_animation.setEndValue(360)
        self.icon_animation.setLoopCount(-1)  # Infinite loop
        self.icon_animation.setEasingCurve(QEasingCurve.Linear)
    
    def update_progress(self, progress: UpdateProgress):
        """Update progress display"""
        # Update stage
        if progress.stage != self.current_stage:
            self.current_stage = progress.stage
            self._update_stage_display(progress.stage)
        
        # Update progress bar
        self.progress_bar.setValue(int(progress.progress * 100))
        
        # Update status message
        self.status_label.setText(progress.message)
        
        # Handle different stages
        if progress.stage == "error":
            self._show_error(progress.error or progress.message)
        elif progress.stage == "complete":
            self._show_success()
        elif progress.stage in ["checking", "downloading", "extracting", "installing"]:
            self._show_progress()
    
    def _update_stage_display(self, stage: str):
        """Update stage-specific display"""
        stage_messages = {
            "checking": "🔍 检查更新",
            "downloading": "⬇️ 下载更新",
            "extracting": "📦 解压文件",
            "installing": "⚙️ 安装更新",
            "complete": "✅ 更新完成",
            "error": "❌ 更新失败"
        }
        
        stage_text = stage_messages.get(stage, "处理中...")
        self.stage_label.setText(stage_text)
        
        # Update title
        if stage == "complete":
            self.title_label.setText("更新完成!")
            self.icon_animation.stop()
            self.icon_label.setText("✅")
        elif stage == "error":
            self.title_label.setText("更新失败")
            self.icon_animation.stop()
            self.icon_label.setText("❌")
        else:
            self.title_label.setText("正在更新...")
            if not self.icon_animation.state() == QPropertyAnimation.Running:
                self.icon_animation.start()
    
    def _show_progress(self):
        """Show progress state"""
        self.error_frame.setVisible(False)
        self.success_frame.setVisible(False)
        self.retry_btn.setVisible(False)
        self.cancel_btn.setText("取消")
    
    def _show_error(self, error_message: str):
        """Show error state"""
        self.error_frame.setVisible(True)
        self.success_frame.setVisible(False)
        self.error_message.setText(error_message)
        self.retry_btn.setVisible(True)
        self.cancel_btn.setText("关闭")
        
        # Stop animations
        self.icon_animation.stop()
    
    def _show_success(self):
        """Show success state"""
        self.error_frame.setVisible(False)
        self.success_frame.setVisible(True)
        self.retry_btn.setVisible(False)
        self.cancel_btn.setText("关闭")
        
        # Stop animations
        self.icon_animation.stop()
    
    def reset(self):
        """Reset progress widget to initial state"""
        self.current_stage = ""
        self.progress_bar.setValue(0)
        self.stage_label.setText("准备中...")
        self.status_label.setText("初始化更新...")
        self.title_label.setText("正在更新...")
        self.icon_label.setText("🔄")
        
        self.error_frame.setVisible(False)
        self.success_frame.setVisible(False)
        self.retry_btn.setVisible(False)
        self.cancel_btn.setText("取消")
        
        self.icon_animation.stop()


class UpdateLogWidget(QWidget):
    """Widget for displaying detailed update logs"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.log_entries = []
    
    def setup_ui(self):
        """Setup log widget UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("更新日志")
        title_label.setFont(QFont("", 12, QFont.Bold))
        
        self.clear_btn = QPushButton("清空")
        self.clear_btn.clicked.connect(self.clear_log)
        self.clear_btn.setMaximumWidth(60)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.clear_btn)
        
        layout.addLayout(header_layout)
        
        # Log display
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        self.log_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #DDD;
                border-radius: 6px;
                background-color: #F8F9FA;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10px;
            }
        """)
        
        layout.addWidget(self.log_text)
    
    def add_log_entry(self, message: str, level: str = "info"):
        """Add log entry"""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color coding based on level
        colors = {
            "info": "#666",
            "success": "#34C759",
            "warning": "#FF9500",
            "error": "#FF3B30"
        }
        
        color = colors.get(level, "#666")
        
        log_entry = f'<span style="color: {color};">[{timestamp}] {message}</span>'
        self.log_entries.append(log_entry)
        
        # Update display
        self.log_text.setHtml("<br>".join(self.log_entries))
        
        # Scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_log(self):
        """Clear log entries"""
        self.log_entries.clear()
        self.log_text.clear()
    
    def update_from_progress(self, progress: UpdateProgress):
        """Update log from progress info"""
        level = "error" if progress.stage == "error" else "info"
        if progress.stage == "complete":
            level = "success"
        
        self.add_log_entry(progress.message, level)
        
        if progress.error:
            self.add_log_entry(f"错误详情: {progress.error}", "error")


class CompactUpdateIndicator(QWidget):
    """Compact update indicator for status bar or toolbar"""
    
    # Signals
    clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.update_available = False
        self.is_updating = False
        self.setup_ui()
    
    def setup_ui(self):
        """Setup compact indicator UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        
        self.icon_label = QLabel("🔄")
        self.icon_label.setFont(QFont("", 12))
        
        self.text_label = QLabel("检查更新")
        self.text_label.setFont(QFont("", 10))
        
        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)
        
        # Make clickable
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            CompactUpdateIndicator {
                border: 1px solid #DDD;
                border-radius: 12px;
                background-color: #F8F9FA;
            }
            CompactUpdateIndicator:hover {
                background-color: #E9ECEF;
            }
        """)
    
    def mousePressEvent(self, event):
        """Handle mouse click"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
    
    def set_update_available(self, available: bool, version: str = ""):
        """Set update available state"""
        self.update_available = available
        
        if available:
            self.icon_label.setText("🔔")
            self.text_label.setText(f"新版本 {version}")
            self.setStyleSheet("""
                CompactUpdateIndicator {
                    border: 1px solid #007AFF;
                    border-radius: 12px;
                    background-color: #E3F2FD;
                }
                CompactUpdateIndicator:hover {
                    background-color: #BBDEFB;
                }
            """)
        else:
            self.icon_label.setText("✅")
            self.text_label.setText("已是最新")
            self.setStyleSheet("""
                CompactUpdateIndicator {
                    border: 1px solid #34C759;
                    border-radius: 12px;
                    background-color: #F0FFF4;
                }
                CompactUpdateIndicator:hover {
                    background-color: #E8F5E8;
                }
            """)
    
    def set_updating(self, updating: bool):
        """Set updating state"""
        self.is_updating = updating
        
        if updating:
            self.icon_label.setText("⏳")
            self.text_label.setText("更新中...")
            self.setStyleSheet("""
                CompactUpdateIndicator {
                    border: 1px solid #FF9500;
                    border-radius: 12px;
                    background-color: #FFF3E0;
                }
            """)
        else:
            # Reset to previous state
            self.set_update_available(self.update_available)
    
    def set_error(self, error_message: str = ""):
        """Set error state"""
        self.icon_label.setText("❌")
        self.text_label.setText("更新失败")
        self.setToolTip(error_message)
        self.setStyleSheet("""
            CompactUpdateIndicator {
                border: 1px solid #FF3B30;
                border-radius: 12px;
                background-color: #FFF5F5;
            }
            CompactUpdateIndicator:hover {
                background-color: #FFEBEE;
            }
        """)