"""
自定义状态栏组件 - macOS风格
"""
from PySide6.QtWidgets import (
    QStatusBar, QLabel, QProgressBar, QWidget, 
    QHBoxLayout, QFrame
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont


class CustomStatusBar(QStatusBar):
    """自定义状态栏"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_timer()
        
    def setup_ui(self):
        """设置用户界面"""
        self.setObjectName("customStatusBar")
        self.setFixedHeight(32)
        self.setStyleSheet("""
            #customStatusBar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(245, 245, 245, 0.95),
                    stop:1 rgba(235, 235, 235, 0.95));
                border-top: 1px solid rgba(0, 0, 0, 0.1);
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
                color: #1d1d1f;
                font-size: 12px;
            }
        """)
        
        # 创建状态栏内容
        self.create_status_widgets()
        
    def create_status_widgets(self):
        """创建状态栏组件"""
        # 主容器
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(16, 4, 16, 4)
        layout.setSpacing(16)
        
        # 总进度信息
        self.total_progress_label = QLabel("就绪")
        self.total_progress_label.setObjectName("totalProgressLabel")
        layout.addWidget(self.total_progress_label)
        
        # 分隔符
        separator1 = self.create_separator()
        layout.addWidget(separator1)
        
        # 下载速度
        self.speed_label = QLabel("0 B/s")
        self.speed_label.setObjectName("speedLabel")
        layout.addWidget(self.speed_label)
        
        # 分隔符
        separator2 = self.create_separator()
        layout.addWidget(separator2)
        
        # 剩余时间
        self.time_label = QLabel("--:--")
        self.time_label.setObjectName("timeLabel")
        layout.addWidget(self.time_label)
        
        # 分隔符
        separator3 = self.create_separator()
        layout.addWidget(separator3)
        
        # 活跃任务数
        self.active_tasks_label = QLabel("0 个任务")
        self.active_tasks_label.setObjectName("activeTasksLabel")
        layout.addWidget(self.active_tasks_label)
        
        # 弹性空间
        layout.addStretch()
        
        # 网络状态指示器
        self.network_status = QLabel("🌐")
        self.network_status.setObjectName("networkStatus")
        self.network_status.setToolTip("网络状态")
        layout.addWidget(self.network_status)
        
        # 添加到状态栏
        self.addPermanentWidget(container, 1)
        
    def create_separator(self):
        """创建分隔符"""
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setFixedHeight(16)
        separator.setStyleSheet("""
            QFrame {
                color: rgba(0, 0, 0, 0.2);
                margin: 2px 0;
            }
        """)
        return separator
        
    def setup_timer(self):
        """设置定时器"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_network_status)
        self.update_timer.start(5000)  # 每5秒更新一次网络状态
        
    def update_status(self, message: str, progress: int = 0):
        """更新状态信息"""
        self.total_progress_label.setText(message)
        
    def update_download_stats(self, speed: str, remaining_time: str, active_tasks: int):
        """更新下载统计信息"""
        self.speed_label.setText(speed)
        self.time_label.setText(remaining_time)
        self.active_tasks_label.setText(f"{active_tasks} 个任务")
        
    def update_network_status(self):
        """更新网络状态"""
        # 这里可以添加网络连接检测逻辑
        # 暂时使用静态图标
        self.network_status.setText("🌐")
        
    def set_total_progress(self, current: int, total: int):
        """设置总进度"""
        if total > 0:
            percentage = int((current / total) * 100)
            self.total_progress_label.setText(f"总进度: {current}/{total} ({percentage}%)")
        else:
            self.total_progress_label.setText("就绪")
            
    def show_message(self, message: str, timeout: int = 3000):
        """显示临时消息"""
        self.showMessage(message, timeout)