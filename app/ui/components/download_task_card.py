"""
下载任务卡片组件 - macOS风格
"""
import uuid
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QPushButton, QProgressBar, QFrame, QMenu
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPixmap, QPainter, QBrush, QColor
from .touch_context_menu import TouchContextMenu


class MagicProgressBar(QProgressBar):
    """魔法进度条 - 带波形图效果"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(8)
        self.setTextVisible(False)
        self.speed_history = []  # 速度历史用于波形图
        self.max_speed = 1.0  # 动态最大速度
        self.animation_offset = 0  # 动画偏移
        
        # 设置样式
        self.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: rgba(0, 0, 0, 0.1);
            }
            QProgressBar::chunk {
                border-radius: 4px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #007aff, stop:0.5 #5ac8fa, stop:1 #30d158);
            }
        """)
        
        # 动画定时器
        from PySide6.QtCore import QTimer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_wave)
        
    def add_speed_point(self, speed: float):
        """添加速度点用于波形图"""
        self.speed_history.append(speed)
        if len(self.speed_history) > 100:  # 保持最近100个点
            self.speed_history.pop(0)
            
        # 更新最大速度
        if speed > self.max_speed:
            self.max_speed = speed * 1.2  # 留一些余量
            
        # 启动动画
        if not self.animation_timer.isActive() and speed > 0:
            self.animation_timer.start(50)  # 20fps
            
        self.update()
        
    def animate_wave(self):
        """动画波形"""
        self.animation_offset += 1
        if self.animation_offset > 100:
            self.animation_offset = 0
        self.update()
        
        # 如果没有新的速度数据，停止动画
        if not self.speed_history or self.speed_history[-1] == 0:
            self.animation_timer.stop()
            
    def paintEvent(self, event):
        """自定义绘制进度条"""
        super().paintEvent(event)
        
        # 绘制增强的波形图
        if self.speed_history and self.isVisible():
            painter = QPainter(self)
            if not painter.isActive():
                return
                
            painter.setRenderHint(QPainter.Antialiasing)
            
            width = self.width()
            height = self.height()
            
            # 绘制波形背景
            painter.setPen(Qt.NoPen)
            gradient_brush = QBrush(QColor(0, 122, 255, 30))
            painter.setBrush(gradient_brush)
            
            # 创建波形路径
            from PySide6.QtGui import QPainterPath
            wave_path = QPainterPath()
            
            if len(self.speed_history) > 1:
                # 计算波形点
                points_count = min(len(self.speed_history), width // 2)
                for i in range(points_count):
                    x = int(width * i / points_count)
                    speed_index = len(self.speed_history) - points_count + i
                    if speed_index >= 0:
                        speed = self.speed_history[speed_index]
                        normalized_speed = speed / max(self.max_speed, 1.0)
                        wave_height = height * 0.4 * normalized_speed
                        
                        # 添加动画效果
                        wave_offset = 0.1 * height * abs(
                            __import__('math').sin(
                                (i + self.animation_offset) * 0.2
                            )
                        )
                        
                        y = height - wave_height - wave_offset
                        
                        if i == 0:
                            wave_path.moveTo(x, y)
                        else:
                            wave_path.lineTo(x, y)
                
                # 绘制波形
                painter.setPen(QColor(0, 122, 255, 150))
                painter.drawPath(wave_path)
                
            painter.end()


class StatusIndicator(QWidget):
    """状态指示器 - 带动画效果"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.status = "waiting"
        self.setFixedSize(12, 12)
        self.animation_value = 0.0
        self.pulse_direction = 1
        
        # 动画定时器
        from PySide6.QtCore import QTimer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_pulse)
        
    def set_status(self, status: str):
        """设置状态"""
        old_status = self.status
        self.status = status
        
        # 启动/停止动画
        if status == "downloading" and not self.animation_timer.isActive():
            self.animation_timer.start(100)  # 10fps脉冲动画
        elif status != "downloading" and self.animation_timer.isActive():
            self.animation_timer.stop()
            self.animation_value = 0.0
            
        self.update()
        
    def animate_pulse(self):
        """脉冲动画"""
        self.animation_value += 0.1 * self.pulse_direction
        if self.animation_value >= 1.0:
            self.animation_value = 1.0
            self.pulse_direction = -1
        elif self.animation_value <= 0.0:
            self.animation_value = 0.0
            self.pulse_direction = 1
            
        self.update()
        
    def paintEvent(self, event):
        """绘制状态指示器"""
        if not self.isVisible():
            return
            
        painter = QPainter(self)
        if not painter.isActive():
            return
            
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 根据状态设置颜色
        colors = {
            "waiting": QColor(142, 142, 147),
            "downloading": QColor(0, 122, 255),
            "completed": QColor(40, 202, 66),
            "paused": QColor(255, 189, 46),
            "error": QColor(255, 95, 87)
        }
        
        color = colors.get(self.status, colors["waiting"])
        
        # 绘制主圆点
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, 8, 8)
        
        # 下载状态时绘制脉冲效果
        if self.status == "downloading" and self.animation_value > 0:
            pulse_alpha = int(100 * (1.0 - self.animation_value))
            pulse_color = QColor(color.red(), color.green(), color.blue(), pulse_alpha)
            painter.setBrush(QBrush(pulse_color))
            
            # 脉冲圆环
            pulse_size = 2 + int(6 * self.animation_value)
            pulse_x = 6 - pulse_size // 2
            pulse_y = 6 - pulse_size // 2
            painter.drawEllipse(pulse_x, pulse_y, pulse_size, pulse_size)
            
        painter.end()


class DownloadTaskCard(QWidget):
    """下载任务卡片"""
    
    action_requested = Signal(str)  # 动作信号
    selected = Signal()  # 选中信号
    
    def __init__(self, url: str, metadata: dict = None, parent=None):
        super().__init__(parent)
        self.task_id = str(uuid.uuid4())
        self.url = url
        self.metadata = metadata or {}
        self.status = "waiting"
        self.progress = 0.0
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """设置用户界面"""
        self.setObjectName("downloadTaskCard")
        self.setProperty("class", "card")
        self.setFixedHeight(80)
        self.setMinimumWidth(600)
        
        # 主布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        # 缩略图
        self.thumbnail = QLabel()
        self.thumbnail.setFixedSize(60, 45)
        self.thumbnail.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 0.1);
                border-radius: 6px;
                border: 1px solid rgba(0, 0, 0, 0.1);
            }
        """)
        self.thumbnail.setAlignment(Qt.AlignCenter)
        self.thumbnail.setText("📹")
        layout.addWidget(self.thumbnail)
        
        # 信息区域
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        # 标题和作者
        title_layout = QHBoxLayout()
        title_layout.setSpacing(8)
        
        self.title_label = QLabel(self.metadata.get('title', '正在获取视频信息...'))
        self.title_label.setObjectName("taskTitle")
        self.title_label.setStyleSheet("""
            #taskTitle {
                font-size: 14px;
                font-weight: 500;
                color: #1d1d1f;
            }
        """)
        title_layout.addWidget(self.title_label, 1)
        
        # 状态指示器
        self.status_indicator = StatusIndicator()
        title_layout.addWidget(self.status_indicator)
        
        info_layout.addLayout(title_layout)
        
        # 作者信息
        self.author_label = QLabel(self.metadata.get('author', ''))
        self.author_label.setObjectName("taskAuthor")
        self.author_label.setStyleSheet("""
            #taskAuthor {
                font-size: 12px;
                color: #8e8e93;
            }
        """)
        info_layout.addWidget(self.author_label)
        
        # 进度条
        self.progress_bar = MagicProgressBar()
        info_layout.addWidget(self.progress_bar)
        
        layout.addLayout(info_layout, 1)
        
        # 状态和速度信息
        status_layout = QVBoxLayout()
        status_layout.setSpacing(2)
        
        self.status_label = QLabel("等待中")
        self.status_label.setObjectName("taskStatus")
        self.status_label.setStyleSheet("""
            #taskStatus {
                font-size: 12px;
                font-weight: 500;
                color: #8e8e93;
            }
        """)
        self.status_label.setAlignment(Qt.AlignRight)
        status_layout.addWidget(self.status_label)
        
        self.speed_label = QLabel("")
        self.speed_label.setObjectName("taskSpeed")
        self.speed_label.setStyleSheet("""
            #taskSpeed {
                font-size: 11px;
                color: #8e8e93;
            }
        """)
        self.speed_label.setAlignment(Qt.AlignRight)
        status_layout.addWidget(self.speed_label)
        
        layout.addLayout(status_layout)
        
        # 操作按钮
        self.action_button = QPushButton("▶")
        self.action_button.setObjectName("taskActionButton")
        self.action_button.setFixedSize(32, 32)
        self.action_button.setStyleSheet("""
            #taskActionButton {
                background-color: rgba(0, 122, 255, 0.1);
                border: 1px solid rgba(0, 122, 255, 0.3);
                border-radius: 16px;
                font-size: 14px;
                color: #007aff;
            }
            #taskActionButton:hover {
                background-color: rgba(0, 122, 255, 0.2);
            }
            #taskActionButton:pressed {
                background-color: rgba(0, 122, 255, 0.3);
            }
        """)
        layout.addWidget(self.action_button)
        
    def setup_connections(self):
        """设置信号连接"""
        self.action_button.clicked.connect(self.handle_action_button)
        
    def contextMenuEvent(self, event):
        """3D Touch式右键菜单"""
        menu = TouchContextMenu(self)
        
        # 任务控制组
        control_group = menu.add_group("任务控制")
        if self.status == "downloading":
            control_group.add_action("⏸", "暂停", lambda: self.action_requested.emit("pause"))
        elif self.status == "paused":
            control_group.add_action("▶", "继续", lambda: self.action_requested.emit("resume"))
        else:
            control_group.add_action("▶", "开始", lambda: self.action_requested.emit("start"))
            
        control_group.add_action("🔄", "重新开始", lambda: self.action_requested.emit("restart"))
        
        # 批量操作组
        batch_group = menu.add_group("批量操作")
        batch_group.add_action("▶▶", "开始全部", lambda: self.action_requested.emit("start_all"))
        batch_group.add_action("⏸⏸", "暂停全部", lambda: self.action_requested.emit("pause_all"))
        
        # 文件操作组
        if self.status == "completed":
            file_group = menu.add_group("文件操作")
            file_group.add_action("📄", "打开文件", lambda: self.action_requested.emit("open_file"))
            file_group.add_action("📁", "打开文件夹", lambda: self.action_requested.emit("open_folder"))
            
        # 列表管理组
        manage_group = menu.add_group("列表管理")
        manage_group.add_action("🗑", "删除任务", lambda: self.action_requested.emit("delete"))
        if self.status == "completed":
            manage_group.add_action("✅", "标记完成", lambda: self.action_requested.emit("mark_complete"))
        
        menu.exec(event.globalPos())
        
    def handle_action_button(self):
        """处理操作按钮点击"""
        if self.status == "downloading":
            self.action_requested.emit("pause")
        elif self.status == "paused":
            self.action_requested.emit("resume")
        else:
            self.action_requested.emit("start")
            
    def update_progress(self, progress: float, speed: str = ""):
        """更新进度"""
        self.progress = progress
        self.progress_bar.setValue(int(progress))
        
        if speed:
            self.speed_label.setText(speed)
            # 提取速度数值用于波形图
            try:
                speed_value = float(speed.split()[0])
                self.progress_bar.add_speed_point(speed_value)
            except:
                pass
                
    def update_status(self, status: str):
        """更新状态"""
        self.status = status
        self.status_indicator.set_status(status)
        
        # 更新状态文本
        status_texts = {
            "waiting": "等待中",
            "downloading": "下载中",
            "completed": "已完成",
            "paused": "已暂停",
            "error": "出错"
        }
        self.status_label.setText(status_texts.get(status, status))
        
        # 更新操作按钮
        button_texts = {
            "waiting": "▶",
            "downloading": "⏸",
            "completed": "✓",
            "paused": "▶",
            "error": "⚠"
        }
        self.action_button.setText(button_texts.get(status, "▶"))
        
    def update_metadata(self, metadata: dict):
        """更新元数据"""
        self.metadata.update(metadata)
        
        if 'title' in metadata:
            self.title_label.setText(metadata['title'])
            
        if 'author' in metadata:
            self.author_label.setText(metadata['author'])
            
        if 'thumbnail' in metadata:
            # 加载缩略图
            self.load_thumbnail(metadata['thumbnail'])
            
    def load_thumbnail(self, thumbnail_url: str):
        """加载缩略图"""
        # 这里应该异步加载缩略图
        # 暂时使用占位符
        self.thumbnail.setText("🎬")
        
    def is_completed(self) -> bool:
        """检查是否已完成"""
        return self.status == "completed"
        
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            self.selected.emit()
        super().mousePressEvent(event)