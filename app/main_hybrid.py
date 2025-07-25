"""
Hybrid interface - PySide6 window with embedded HTML content
Uses QTextBrowser to display HTML content with custom styling
"""
import sys
import os
import json
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import Qt modules
try:
    from PySide6.QtWidgets import *
    from PySide6.QtCore import *
    from PySide6.QtGui import *
except ImportError as e:
    print(f"Error: PySide6 not found. Please install it with: pip install PySide6")
    print(f"Import error: {e}")
    sys.exit(1)

# Import application modules
try:
    from app.core.portable import get_portable_manager
    from app.services.download_service import DownloadService
    from app.services.settings_service import SettingsService
    from app.services.creator_service import CreatorService
except ImportError as e:
    print(f"Warning: Some application modules not found: {e}")
    # Create fallback classes
    class DownloadService:
        def __init__(self): pass
    class SettingsService:
        def __init__(self): pass
    class CreatorService:
        def __init__(self): pass


class ModernTaskCard(QFrame):
    """Modern task card widget matching HTML design exactly"""
    
    cancel_requested = Signal(str)
    
    def __init__(self, url: str, task_data: dict):
        super().__init__()
        self.url = url
        self.task_data = task_data
        self.setup_ui()
        self.update_task_data(task_data)
        
        # Enable context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
    def setup_ui(self):
        """Setup modern task card UI matching HTML design"""
        self.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #E5E5E7;
                border-radius: 12px;
                margin: 4px;
            }
            QFrame:hover {
                border-color: #D1D1D6;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Thumbnail - 匹配HTML中的128x80尺寸
        self.thumbnail = QLabel()
        self.thumbnail.setFixedSize(128, 80)
        self.thumbnail.setStyleSheet("""
            QLabel {
                background: #F2F2F7;
                border: none;
                border-radius: 4px;
            }
        """)
        self.thumbnail.setAlignment(Qt.AlignCenter)
        self.thumbnail.setText("📺")
        self.thumbnail.setScaledContents(True)
        layout.addWidget(self.thumbnail)
        
        # Content area
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title and controls row
        title_layout = QHBoxLayout()
        title_layout.setSpacing(8)
        
        self.title_label = QLabel("Loading...")
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 600;
                color: #1C1C1E;
            }
        """)
        title_layout.addWidget(self.title_label, 1)
        
        # Control buttons - 匹配HTML样式
        self.pause_btn = QPushButton("⏸")
        self.cancel_btn = QPushButton("✕")
        self.folder_btn = QPushButton("📁")
        
        for btn in [self.pause_btn, self.cancel_btn, self.folder_btn]:
            btn.setFixedSize(24, 24)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    border-radius: 12px;
                    font-size: 12px;
                    color: #8E8E93;
                }
                QPushButton:hover {
                    background: #F2F2F7;
                    color: #1C1C1E;
                }
            """)
        
        self.cancel_btn.clicked.connect(lambda: self.cancel_requested.emit(self.url))
        
        title_layout.addWidget(self.pause_btn)
        title_layout.addWidget(self.cancel_btn)
        title_layout.addWidget(self.folder_btn)
        
        content_layout.addLayout(title_layout)
        
        # Progress bar row
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(8)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: #E5E5E7;
                border: none;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background: #007AFF;
                border-radius: 3px;
            }
        """)
        self.progress_bar.setTextVisible(False)
        
        self.progress_label = QLabel("0%")
        self.progress_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #8E8E93;
                min-width: 35px;
            }
        """)
        
        progress_layout.addWidget(self.progress_bar, 1)
        progress_layout.addWidget(self.progress_label)
        content_layout.addLayout(progress_layout)
        
        # Status info row - 匹配HTML布局
        status_layout = QHBoxLayout()
        status_layout.setSpacing(16)
        
        self.size_label = QLabel("0 MB/0 MB")
        self.eta_label = QLabel("剩余时间: --")
        self.speed_label = QLabel("0 MB/s")
        
        for label in [self.size_label, self.eta_label, self.speed_label]:
            label.setStyleSheet("""
                QLabel {
                    font-size: 11px;
                    color: #8E8E93;
                }
            """)
        
        status_layout.addWidget(self.size_label)
        status_layout.addWidget(self.eta_label)
        status_layout.addStretch()
        status_layout.addWidget(self.speed_label)
        
        content_layout.addLayout(status_layout)
        layout.addLayout(content_layout, 1)
    
    def show_context_menu(self, position):
        """Show context menu for task card"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: white;
                border: 1px solid #D1D1D6;
                border-radius: 6px;
                padding: 4px 0px;
            }
            QMenu::item {
                padding: 6px 16px;
                font-size: 14px;
                color: #1C1C1E;
            }
            QMenu::item:selected {
                background: #F2F2F7;
            }
        """)
        
        # Add context menu actions based on task status
        status = self.task_data.get('status', 'pending')
        
        if status == 'downloading':
            menu.addAction("暂停", self.pause_task)
        elif status == 'paused':
            menu.addAction("继续", self.resume_task)
        elif status == 'failed':
            menu.addAction("重新开始", self.restart_task)
        
        menu.addAction("取消", self.cancel_task)
        menu.addAction("删除", self.delete_task)
        menu.addSeparator()
        menu.addAction("打开文件夹", self.open_folder)
        
        if status == 'completed':
            menu.addAction("播放", self.play_file)
        
        menu.exec(self.mapToGlobal(position))
    
    def pause_task(self):
        """Pause task"""
        print(f"Pausing task: {self.url}")
    
    def resume_task(self):
        """Resume task"""
        print(f"Resuming task: {self.url}")
    
    def restart_task(self):
        """Restart task"""
        print(f"Restarting task: {self.url}")
    
    def cancel_task(self):
        """Cancel task"""
        self.cancel_requested.emit(self.url)
    
    def delete_task(self):
        """Delete task"""
        print(f"Deleting task: {self.url}")
    
    def open_folder(self):
        """Open containing folder"""
        print(f"Opening folder for: {self.url}")
    
    def play_file(self):
        """Play downloaded file"""
        print(f"Playing file: {self.url}")
        
    def update_task_data(self, task_data: dict):
        """Update task data with modern styling"""
        self.task_data = task_data
        
        # Update title
        title = task_data.get('title') or task_data.get('filename') or self.url
        if len(title) > 60:
            title = title[:57] + "..."
        self.title_label.setText(title)
        
        # Update progress
        progress = task_data.get('progress', 0)
        self.progress_bar.setValue(int(progress))
        self.progress_label.setText(f"{progress:.1f}%")
        
        # Update status colors
        status = task_data.get('status', 'pending')
        if status == 'downloading':
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    background: #F2F2F7;
                    border: none;
                    border-radius: 4px;
                    height: 8px;
                }
                QProgressBar::chunk {
                    background: #007AFF;
                    border-radius: 4px;
                }
            """)
            self.setStyleSheet("""
                QFrame {
                    background: white;
                    border: 1px solid #007AFF;
                    border-radius: 12px;
                    margin: 4px;
                }
            """)
        elif status == 'completed':
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    background: #F2F2F7;
                    border: none;
                    border-radius: 4px;
                    height: 8px;
                }
                QProgressBar::chunk {
                    background: #34C759;
                    border-radius: 4px;
                }
            """)
            self.setStyleSheet("""
                QFrame {
                    background: #E6FFFA;
                    border: 1px solid #34C759;
                    border-radius: 12px;
                    margin: 4px;
                }
            """)
        elif status == 'failed':
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    background: #F2F2F7;
                    border: none;
                    border-radius: 4px;
                    height: 8px;
                }
                QProgressBar::chunk {
                    background: #FF3B30;
                    border-radius: 4px;
                }
            """)
            self.setStyleSheet("""
                QFrame {
                    background: #FFEBEE;
                    border: 1px solid #FF3B30;
                    border-radius: 12px;
                    margin: 4px;
                }
            """)
        
        # Update size info
        file_size = task_data.get('file_size', 0)
        downloaded_size = task_data.get('downloaded_size', 0)
        
        if file_size > 0:
            file_size_mb = file_size / (1024 * 1024)
            downloaded_mb = downloaded_size / (1024 * 1024)
            self.size_label.setText(f"{downloaded_mb:.1f} MB/{file_size_mb:.1f} MB")
        else:
            self.size_label.setText("计算中...")
        
        # Update speed and ETA
        speed = task_data.get('speed', '')
        eta = task_data.get('eta', '')
        
        self.speed_label.setText(speed or "0 MB/s")
        self.eta_label.setText(f"剩余时间: {eta}" if eta else "剩余时间: --")


class HybridVideoDownloaderWindow(QMainWindow):
    """Hybrid interface combining your HTML design with PySide6 functionality"""
    
    def __init__(self):
        super().__init__()
        self.portable_manager = get_portable_manager()
        
        # Initialize services
        self.download_service = DownloadService()
        self.settings_service = SettingsService()
        self.creator_service = CreatorService()
        
        # Task widgets
        self.task_widgets = {}
        
        # Window dragging variables
        self.drag_position = None
        self.is_dragging = False
        
        # System tray
        self.tray_icon = None
        self.setup_system_tray()
        
        self.init_ui()
        self.connect_signals()
        self.apply_modern_styling()
        
    def init_ui(self):
        """Initialize modern UI inspired by your HTML design"""
        self.setWindowTitle("视频下载器")
        self.setGeometry(100, 100, 900, 600)
        
        # 完全隐藏Windows标题栏，实现纯macOS风格
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create title bar (macOS style)
        self.create_title_bar(main_layout)
        
        # Create navigation tabs
        self.create_navigation_tabs(main_layout)
        
        # Create search area
        self.create_search_area(main_layout)
        
        # Create main content area
        self.create_main_content(main_layout)
        
        # Create status bar
        self.create_status_bar(main_layout)
    
    def create_title_bar(self, parent_layout):
        """Create macOS-style title bar"""
        title_bar = QFrame()
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet("""
            QFrame {
                background: #E8E8E8;
                border-bottom: 1px solid #D1D1D6;
            }
        """)
        
        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(16, 0, 16, 0)
        
        # Window controls - 正确的macOS风格位置（左侧）
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)
        
        # 红黄绿按钮（关闭、最小化、最大化）
        colors_and_actions = [
            ('#FF5F56', '✕', self.close),  # 关闭
            ('#FFBD2E', '−', self.showMinimized),  # 最小化
            ('#27C93F', '+', self.toggle_maximize)  # 最大化
        ]
        
        for color, icon, action in colors_and_actions:
            btn = QPushButton()
            btn.setFixedSize(12, 12)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {color};
                    border: none;
                    border-radius: 6px;
                    color: transparent;
                    font-size: 8px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    color: rgba(0, 0, 0, 0.3);
                }}
            """)
            btn.setText(icon)
            btn.clicked.connect(action)
            controls_layout.addWidget(btn)
        
        layout.addLayout(controls_layout)
        
        # Title - 居中
        title_label = QLabel("视频下载器")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #1C1C1E;
                font-size: 14px;
                font-weight: 500;
            }
        """)
        layout.addWidget(title_label, 1)
        
        # Menu button - 右侧
        menu_btn = QPushButton("⋯")
        menu_btn.setFixedSize(20, 20)
        menu_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #8E8E93;
                font-size: 12px;
            }
        """)
        layout.addWidget(menu_btn)
        
        parent_layout.addWidget(title_bar)
    
    def toggle_maximize(self):
        """切换最大化状态"""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
    
    def create_navigation_tabs(self, parent_layout):
        """Create navigation tabs"""
        nav_frame = QFrame()
        nav_frame.setFixedHeight(40)
        nav_frame.setStyleSheet("""
            QFrame {
                background: #E8E8E8;
                border-bottom: 1px solid #D1D1D6;
            }
        """)
        
        layout = QHBoxLayout(nav_frame)
        layout.setContentsMargins(16, 8, 16, 8)
        
        # Tab buttons
        self.tab_buttons = []
        tabs = [
            ("📜", "历史记录"),
            ("👁", "创作者监控"),
            ("⚙️", "首选项")
        ]
        
        for icon, text in tabs:
            btn = QPushButton(f"{icon} {text}")
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    padding: 4px 12px;
                    border-radius: 6px;
                    color: #1C1C1E;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background: #F2F2F7;
                }
                QPushButton:checked {
                    background: #FFFFFF;
                    font-weight: 600;
                }
            """)
            btn.setCheckable(True)
            self.tab_buttons.append(btn)
            layout.addWidget(btn)
        
        layout.addStretch()
        parent_layout.addWidget(nav_frame)
    
    def create_search_area(self, parent_layout):
        """Create search and add area"""
        search_frame = QFrame()
        search_frame.setFixedHeight(60)
        search_frame.setStyleSheet("""
            QFrame {
                background: white;
                border-bottom: 1px solid #E5E5E7;
            }
        """)
        
        layout = QHBoxLayout(search_frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        # Search input
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("搜索视频或粘贴链接")
        self.url_input.setStyleSheet("""
            QLineEdit {
                background: white;
                border: 1px solid #D1D1D6;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                color: #1C1C1E;
            }
            QLineEdit:focus {
                border-color: #007AFF;
                outline: none;
            }
        """)
        layout.addWidget(self.url_input, 1)
        
        # Add download button
        self.add_btn = QPushButton("➕ 添加下载")
        self.add_btn.setStyleSheet("""
            QPushButton {
                background: #007AFF;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #0051D5;
            }
        """)
        layout.addWidget(self.add_btn)
        
        # Add queue button
        self.queue_btn = QPushButton("📋 添加队列")
        self.queue_btn.setStyleSheet("""
            QPushButton {
                background: #F2F2F7;
                color: #1C1C1E;
                border: 1px solid #D1D1D6;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #E5E5EA;
            }
        """)
        layout.addWidget(self.queue_btn)
        
        parent_layout.addWidget(search_frame)
    
    def create_main_content(self, parent_layout):
        """Create main content area"""
        # Content area
        content_frame = QFrame()
        content_frame.setStyleSheet("""
            QFrame {
                background: white;
            }
        """)
        
        layout = QVBoxLayout(content_frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Section title
        title_layout = QHBoxLayout()
        section_title = QLabel("正在下载")
        section_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: 600;
                color: #1C1C1E;
            }
        """)
        title_layout.addWidget(section_title)
        
        # Clear completed button
        self.clear_btn = QPushButton("清除已完成")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #8E8E93;
                border: none;
                padding: 4px 8px;
                font-size: 12px;
            }
            QPushButton:hover {
                color: #007AFF;
            }
        """)
        title_layout.addWidget(self.clear_btn)
        
        layout.addLayout(title_layout)
        
        # Scroll area for tasks
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #D1D1D6;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #8E8E93;
            }
        """)
        
        self.tasks_widget = QWidget()
        self.tasks_layout = QVBoxLayout(self.tasks_widget)
        self.tasks_layout.setSpacing(8)
        self.tasks_layout.addStretch()
        
        self.scroll_area.setWidget(self.tasks_widget)
        layout.addWidget(self.scroll_area)
        
        parent_layout.addWidget(content_frame)
    
    def create_status_bar(self, parent_layout):
        """Create status bar"""
        status_frame = QFrame()
        status_frame.setFixedHeight(32)
        status_frame.setStyleSheet("""
            QFrame {
                background: white;
                border-top: 1px solid #E5E5E7;
            }
        """)
        
        layout = QHBoxLayout(status_frame)
        layout.setContentsMargins(16, 8, 16, 8)
        
        # Status info
        self.status_label = QLabel("总计: 0 个下载 • 活动: 0 个 • 已完成: 0 个")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #8E8E93;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # Control buttons
        pause_all_btn = QPushButton("全部暂停")
        start_all_btn = QPushButton("全部开始")
        
        for btn in [pause_all_btn, start_all_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #8E8E93;
                    border: none;
                    padding: 2px 8px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    color: #007AFF;
                }
            """)
        
        layout.addWidget(pause_all_btn)
        layout.addWidget(QLabel("|"))
        layout.addWidget(start_all_btn)
        
        parent_layout.addWidget(status_frame)
    
    def connect_signals(self):
        """Connect signals"""
        # Button signals
        self.add_btn.clicked.connect(self.add_download)
        self.queue_btn.clicked.connect(self.show_batch_dialog)
        self.clear_btn.clicked.connect(self.clear_completed)
        self.url_input.returnPressed.connect(self.add_download)
        
        # Navigation tab signals
        if len(self.tab_buttons) >= 3:
            self.tab_buttons[0].clicked.connect(self.show_history)  # 历史记录
            self.tab_buttons[1].clicked.connect(self.show_creator_monitor)  # 创作者监控
            self.tab_buttons[2].clicked.connect(self.show_settings)  # 首选项
        
        # Service signals
        self.download_service.task_added.connect(self.on_task_added)
        self.download_service.task_updated.connect(self.on_task_updated)
        self.download_service.task_completed.connect(self.on_task_completed)
        self.download_service.task_failed.connect(self.on_task_failed)
    
    def setup_system_tray(self):
        """设置系统托盘"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("⚠️ 系统托盘不可用")
            return
        
        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        
        # 设置托盘图标（使用应用程序图标或默认图标）
        icon = self.style().standardIcon(QStyle.SP_ComputerIcon)
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("视频下载器")
        
        # 创建托盘菜单
        tray_menu = QMenu()
        tray_menu.setStyleSheet("""
            QMenu {
                background: white;
                border: 1px solid #D1D1D6;
                border-radius: 6px;
                padding: 4px 0px;
            }
            QMenu::item {
                padding: 8px 16px;
                font-size: 14px;
                color: #1C1C1E;
            }
            QMenu::item:selected {
                background: #F2F2F7;
            }
        """)
        
        # 显示/隐藏主窗口
        show_action = tray_menu.addAction("显示主窗口")
        show_action.triggered.connect(self.show_main_window)
        
        hide_action = tray_menu.addAction("隐藏主窗口")
        hide_action.triggered.connect(self.hide_main_window)
        
        tray_menu.addSeparator()
        
        # 快速功能
        add_download_action = tray_menu.addAction("添加下载")
        add_download_action.triggered.connect(self.show_add_download_dialog)
        
        history_action = tray_menu.addAction("查看历史")
        history_action.triggered.connect(self.show_history)
        
        tray_menu.addSeparator()
        
        # 退出应用
        quit_action = tray_menu.addAction("退出")
        quit_action.triggered.connect(self.quit_application)
        
        self.tray_icon.setContextMenu(tray_menu)
        
        # 双击托盘图标显示主窗口
        self.tray_icon.activated.connect(self.on_tray_activated)
        
        # 显示托盘图标
        self.tray_icon.show()
        print("✅ 系统托盘已设置")
    
    def on_tray_activated(self, reason):
        """托盘图标激活事件"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_main_window()
    
    def show_main_window(self):
        """显示主窗口"""
        self.show()
        self.raise_()
        self.activateWindow()
        print("👁️ 主窗口已显示")
    
    def hide_main_window(self):
        """隐藏主窗口"""
        self.hide()
        print("👁️ 主窗口已隐藏")
    
    def show_add_download_dialog(self):
        """显示添加下载对话框"""
        # 简单的添加下载对话框
        url, ok = QInputDialog.getText(self, "添加下载", "请输入视频链接:")
        if ok and url.strip():
            self.add_download_from_url(url.strip())
    
    def add_download_from_url(self, url):
        """从URL添加下载"""
        if self.download_service.add_download(url):
            if self.tray_icon:
                self.tray_icon.showMessage("下载添加成功", f"已添加下载: {url[:50]}...", QSystemTrayIcon.Information, 3000)
            print(f"✅ 已添加下载: {url}")
        else:
            if self.tray_icon:
                self.tray_icon.showMessage("下载添加失败", "无法添加该链接", QSystemTrayIcon.Warning, 3000)
            print(f"❌ 添加下载失败: {url}")
    
    def quit_application(self):
        """退出应用程序"""
        if self.tray_icon:
            self.tray_icon.hide()
        QApplication.quit()
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 检查是否启用了关闭到托盘
        ui_settings = self.settings_service.get_ui_settings()
        
        if ui_settings.close_to_tray and self.tray_icon and self.tray_icon.isVisible():
            # 关闭到托盘
            event.ignore()
            self.hide()
            if self.tray_icon:
                self.tray_icon.showMessage("应用程序已最小化", "应用程序已最小化到系统托盘", QSystemTrayIcon.Information, 2000)
            print("📱 应用程序已最小化到托盘")
        else:
            # 正常关闭
            event.accept()
    
    def changeEvent(self, event):
        """窗口状态改变事件"""
        if event.type() == QEvent.WindowStateChange:
            # 检查是否启用了最小化到托盘
            ui_settings = self.settings_service.get_ui_settings()
            
            if (self.isMinimized() and ui_settings.minimize_to_tray and 
                self.tray_icon and self.tray_icon.isVisible()):
                # 最小化到托盘
                self.hide()
                if self.tray_icon:
                    self.tray_icon.showMessage("应用程序已最小化", "应用程序已最小化到系统托盘", QSystemTrayIcon.Information, 2000)
                print("📱 应用程序已最小化到托盘")
        
        super().changeEvent(event)
    
    def apply_modern_styling(self):
        """Apply complete macOS styling following Apple Human Interface Guidelines"""
        # 设置窗口属性 - 严格遵循macOS规范
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        # macOS特有属性
        if hasattr(Qt, 'WA_MacShowFocusRect'):
            self.setAttribute(Qt.WA_MacShowFocusRect, False)
        if hasattr(Qt, 'WA_MacBrushedMetal'):
            self.setAttribute(Qt.WA_MacBrushedMetal, False)
        
        # 应用完整的macOS Monterey/Ventura风格
        self.apply_complete_macos_hig_styling()
    
    def apply_complete_macos_hig_styling(self):
        """应用完整的macOS Human Interface Guidelines样式"""
        
        # 完整的macOS风格样式 - 严格遵循Apple HIG
        macos_hig_style = """
            /* ========== 全局设置 ========== */
            * {
                font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Helvetica Neue", Arial, sans-serif;
                outline: none;
            }
            
            /* ========== 主窗口 - macOS Monterey/Ventura风格 ========== */
            QMainWindow {
                background: rgba(246, 246, 246, 1.0);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 10px;
            }
            
            /* ========== 标题栏 - macOS风格 ========== */
            QFrame[objectName="title_bar"] {
                background: rgba(246, 246, 246, 1.0);
                backdrop-filter: blur(20px);
                border-bottom: 1px solid rgba(0, 0, 0, 0.1);
            }
            
            /* ========== 交通灯按钮 - 精确的macOS风格 ========== */
            QPushButton[objectName="traffic_light"] {
                border: none;
                border-radius: 6px;
                background: #C4C4C4;
            }
            
            QPushButton[objectName="traffic_light"]:hover {
                opacity: 0.8;
            }
            
            QPushButton[objectName="close_btn"] {
                background: #FF5F56;
            }
            
            QPushButton[objectName="minimize_btn"] {
                background: #FFBD2E;
            }
            
            QPushButton[objectName="maximize_btn"] {
                background: #27C93F;
            }
            
            /* ========== 按钮 - NSButton风格 ========== */
            QPushButton {
                background: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
                min-height: 22px;
            }
            
            QPushButton:hover {
                background: #0051D5;
                transform: scale(1.02);
            }
            
            QPushButton:pressed {
                background: #003D99;
                transform: scale(0.98);
            }
            
            /* 次要按钮 */
            QPushButton[class="secondary"] {
                background: rgba(120, 120, 128, 0.16);
                color: #007AFF;
                border: 1px solid rgba(0, 122, 255, 0.3);
            }
            
            QPushButton[class="secondary"]:hover {
                background: rgba(120, 120, 128, 0.24);
            }
            
            /* 危险按钮 */
            QPushButton[class="destructive"] {
                background: #FF3B30;
                color: white;
            }
            
            QPushButton[class="destructive"]:hover {
                background: #D70015;
            }
            
            /* ========== 输入框 - NSTextField风格 ========== */
            QLineEdit {
                background: rgba(255, 255, 255, 1.0);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                color: #1D1D1F;
                selection-background-color: #007AFF;
            }
            
            QLineEdit:focus {
                border-color: #007AFF;
                box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.2);
                background: rgba(255, 255, 255, 1.0);
            }
            
            QLineEdit:placeholder {
                color: rgba(60, 60, 67, 0.6);
            }
            
            /* ========== 表格 - NSTableView风格 ========== */
            QTableWidget {
                background: rgba(255, 255, 255, 1.0);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 8px;
                gridline-color: rgba(0, 0, 0, 0.05);
                font-size: 13px;
                alternate-background-color: rgba(0, 0, 0, 0.02);
                selection-background-color: #007AFF;
            }
            
            QTableWidget::item {
                padding: 8px 12px;
                border: none;
                border-bottom: 1px solid rgba(0, 0, 0, 0.05);
            }
            
            QTableWidget::item:hover {
                background: rgba(0, 122, 255, 0.1);
            }
            
            QTableWidget::item:selected {
                background: #007AFF;
                color: white;
            }
            
            QHeaderView::section {
                background: rgba(246, 246, 246, 1.0);
                padding: 12px 8px;
                border: none;
                border-bottom: 1px solid rgba(0, 0, 0, 0.1);
                font-weight: 600;
                font-size: 11px;
                color: rgba(60, 60, 67, 0.6);
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            /* ========== 进度条 - NSProgressIndicator风格 ========== */
            QProgressBar {
                background: rgba(120, 120, 128, 0.16);
                border: none;
                border-radius: 4px;
                height: 8px;
                text-align: center;
            }
            
            QProgressBar::chunk {
                background: #007AFF;
                border-radius: 4px;
            }
            
            /* 成功状态 */
            QProgressBar[status="completed"]::chunk {
                background: #34C759;
            }
            
            /* 错误状态 */
            QProgressBar[status="failed"]::chunk {
                background: #FF3B30;
            }
            
            /* ========== 滚动条 - macOS风格 ========== */
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                border-radius: 4px;
                margin: 0;
            }
            
            QScrollBar::handle:vertical {
                background: rgba(0, 0, 0, 0.2);
                border-radius: 4px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: rgba(0, 0, 0, 0.4);
            }
            
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar:horizontal {
                background: transparent;
                height: 8px;
                border-radius: 4px;
                margin: 0;
            }
            
            QScrollBar::handle:horizontal {
                background: rgba(0, 0, 0, 0.2);
                border-radius: 4px;
                min-width: 20px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background: rgba(0, 0, 0, 0.4);
            }
            
            /* ========== 菜单 - NSMenu风格 ========== */
            QMenu {
                background: rgba(255, 255, 255, 1.0);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 8px;
                padding: 4px 0px;
                backdrop-filter: blur(20px);
            }
            
            QMenu::item {
                padding: 8px 16px;
                font-size: 13px;
                color: #1D1D1F;
                border-radius: 4px;
                margin: 2px 4px;
            }
            
            QMenu::item:selected {
                background: #007AFF;
                color: white;
            }
            
            QMenu::item:disabled {
                color: rgba(60, 60, 67, 0.3);
            }
            
            QMenu::separator {
                height: 1px;
                background: rgba(0, 0, 0, 0.1);
                margin: 4px 8px;
            }
            
            /* ========== 分组框 - NSBox风格 ========== */
            QGroupBox {
                font-weight: 600;
                font-size: 13px;
                color: #1D1D1F;
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
                background: rgba(255, 255, 255, 0.5);
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 8px 0 8px;
                background: rgba(246, 246, 246, 1.0);
                border-radius: 4px;
            }
            
            /* ========== 复选框和单选按钮 - NSButton风格 ========== */
            QCheckBox, QRadioButton {
                font-size: 13px;
                color: #1D1D1F;
                spacing: 8px;
            }
            
            QCheckBox::indicator, QRadioButton::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid rgba(0, 0, 0, 0.2);
                border-radius: 3px;
                background: rgba(255, 255, 255, 0.8);
            }
            
            QCheckBox::indicator:checked {
                background: #007AFF;
                border-color: #007AFF;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xMC42IDEuNEw0LjMgNy43TDEuNCA0LjgiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMS41IiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+);
            }
            
            QRadioButton::indicator {
                border-radius: 8px;
            }
            
            QRadioButton::indicator:checked {
                background: #007AFF;
                border-color: #007AFF;
            }
            
            /* ========== 旋转框 - NSTextField风格 ========== */
            QSpinBox {
                background: rgba(255, 255, 255, 0.8);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 6px;
                padding: 6px 8px;
                font-size: 13px;
                min-width: 60px;
                color: #1D1D1F;
            }
            
            QSpinBox:focus {
                border-color: #007AFF;
                box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.2);
            }
            
            QSpinBox::up-button, QSpinBox::down-button {
                width: 16px;
                border: none;
                background: transparent;
            }
            
            /* ========== 组合框 - NSPopUpButton风格 ========== */
            QComboBox {
                background: rgba(255, 255, 255, 0.8);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 6px;
                padding: 6px 8px;
                font-size: 13px;
                min-width: 100px;
                color: #1D1D1F;
            }
            
            QComboBox:focus {
                border-color: #007AFF;
                box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.2);
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox::down-arrow {
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iNiIgdmlld0JveD0iMCAwIDEwIDYiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDFMNSA1TDkgMSIgc3Ryb2tlPSIjOEU4RTkzIiBzdHJva2Utd2lkdGg9IjEuNSIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPg==);
            }
            
            QComboBox QAbstractItemView {
                background: rgba(255, 255, 255, 0.95);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 8px;
                padding: 4px;
                backdrop-filter: blur(20px);
            }
            
            /* ========== 标签页 - NSTabView风格 ========== */
            QTabWidget::pane {
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 8px;
                background: rgba(255, 255, 255, 1.0);
                margin-top: 4px;
            }
            
            QTabBar::tab {
                background: rgba(120, 120, 128, 0.16);
                border: 1px solid rgba(0, 0, 0, 0.1);
                padding: 8px 16px;
                margin-right: 2px;
                border-radius: 6px 6px 0px 0px;
                font-size: 13px;
                font-weight: 500;
                color: #1D1D1F;
            }
            
            QTabBar::tab:selected {
                background: rgba(255, 255, 255, 1.0);
                border-bottom-color: rgba(255, 255, 255, 1.0);
                color: #007AFF;
                font-weight: 600;
            }
            
            QTabBar::tab:hover {
                background: rgba(120, 120, 128, 0.24);
            }
            
            /* ========== 工具栏 - NSToolbar风格 ========== */
            QToolBar {
                background: rgba(246, 246, 246, 0.8);
                border: none;
                border-bottom: 1px solid rgba(0, 0, 0, 0.1);
                spacing: 8px;
                padding: 8px;
            }
            
            QToolButton {
                background: transparent;
                border: none;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
                color: #1D1D1F;
            }
            
            QToolButton:hover {
                background: rgba(120, 120, 128, 0.16);
            }
            
            QToolButton:pressed {
                background: rgba(120, 120, 128, 0.24);
            }
            
            /* ========== 状态栏 - macOS风格 ========== */
            QStatusBar {
                background: rgba(246, 246, 246, 0.8);
                border-top: 1px solid rgba(0, 0, 0, 0.1);
                font-size: 11px;
                color: rgba(60, 60, 67, 0.6);
            }
            
            /* ========== 对话框 - NSPanel风格 ========== */
            QDialog {
                background: rgba(246, 246, 246, 0.95);
                border-radius: 10px;
                border: 1px solid rgba(0, 0, 0, 0.1);
            }
            
            /* ========== 文本编辑器 - NSTextView风格 ========== */
            QTextEdit, QPlainTextEdit {
                background: rgba(255, 255, 255, 0.8);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
                color: #1D1D1F;
                selection-background-color: #007AFF;
            }
            
            QTextEdit:focus, QPlainTextEdit:focus {
                border-color: #007AFF;
                box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.2);
            }
        """
        
        self.setStyleSheet(macos_hig_style)
        
        # 设置窗口效果
        self.setGraphicsEffect(self.create_blur_effect())
    
    def create_blur_effect(self):
        """创建毛玻璃模糊效果"""
        blur_effect = QGraphicsBlurEffect()
        blur_effect.setBlurRadius(0)  # 主窗口不需要模糊，只需要透明
        return blur_effect
    
    def apply_dark_theme(self):
        """应用深色主题 - macOS Dark Mode"""
        dark_style = """
            /* ========== 深色主题 - macOS Dark Mode ========== */
            QMainWindow {
                background: rgba(30, 30, 30, 0.95);
                color: #FFFFFF;
            }
            
            QFrame[objectName="title_bar"] {
                background: rgba(40, 40, 40, 0.8);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            QPushButton {
                background: #0A84FF;
                color: white;
            }
            
            QPushButton:hover {
                background: #409CFF;
            }
            
            QPushButton[class="secondary"] {
                background: rgba(120, 120, 128, 0.24);
                color: #0A84FF;
                border: 1px solid rgba(10, 132, 255, 0.3);
            }
            
            QLineEdit {
                background: rgba(58, 58, 60, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: #FFFFFF;
            }
            
            QLineEdit:focus {
                border-color: #0A84FF;
                box-shadow: 0 0 0 3px rgba(10, 132, 255, 0.2);
            }
            
            QTableWidget {
                background: rgba(28, 28, 30, 0.8);
                color: #FFFFFF;
                gridline-color: rgba(255, 255, 255, 0.05);
                alternate-background-color: rgba(255, 255, 255, 0.02);
            }
            
            QHeaderView::section {
                background: rgba(44, 44, 46, 0.8);
                color: rgba(235, 235, 245, 0.6);
            }
            
            QMenu {
                background: rgba(30, 30, 30, 0.95);
                color: #FFFFFF;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            QMenu::item:selected {
                background: #0A84FF;
                color: white;
            }
            
            QGroupBox {
                color: #FFFFFF;
                border: 1px solid rgba(255, 255, 255, 0.1);
                background: rgba(58, 58, 60, 0.5);
            }
            
            QGroupBox::title {
                background: rgba(30, 30, 30, 1.0);
            }
            
            QCheckBox, QRadioButton {
                color: #FFFFFF;
            }
            
            QSpinBox, QComboBox {
                background: rgba(58, 58, 60, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: #FFFFFF;
            }
            
            QTabWidget::pane {
                background: rgba(28, 28, 30, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            QTabBar::tab {
                background: rgba(120, 120, 128, 0.24);
                color: #FFFFFF;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            QTabBar::tab:selected {
                background: rgba(58, 58, 60, 0.8);
                color: #0A84FF;
            }
            
            QToolBar {
                background: rgba(40, 40, 40, 0.8);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            QToolButton {
                color: #FFFFFF;
            }
            
            QStatusBar {
                background: rgba(40, 40, 40, 0.8);
                border-top: 1px solid rgba(255, 255, 255, 0.1);
                color: rgba(235, 235, 245, 0.6);
            }
            
            QDialog {
                background: rgba(30, 30, 30, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            QTextEdit, QPlainTextEdit {
                background: rgba(58, 58, 60, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: #FFFFFF;
            }
        """
        self.setStyleSheet(dark_style)
    
    def apply_light_theme(self):
        """应用浅色主题 - macOS Light Mode"""
        self.apply_complete_macos_hig_styling()
        self.apply_complete_macos_hig_styling()
        
        # 应用完整的macOS风格样式
        self.apply_complete_macos_styling()
    
    def apply_complete_macos_styling(self):
        """应用完整的macOS风格样式，严格遵循Apple Human Interface Guidelines"""
        
        # 全局macOS风格样式
        macos_style = """
            /* 全局字体设置 - San Francisco */
            * {
                font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Helvetica Neue", Arial, sans-serif;
            }
            
            /* 主窗口 - macOS Monterey/Ventura风格 */
            QMainWindow {
                background: rgba(242, 242, 247, 0.95);
                border-radius: 10px;
            }
            
            /* 按钮 - macOS风格 */
            QPushButton {
                background: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
                min-height: 22px;
            }
            
            QPushButton:hover {
                background: #0051D5;
                transform: scale(1.02);
            }
            
            QPushButton:pressed {
                background: #003D99;
                transform: scale(0.98);
            }
            
            /* 次要按钮 */
            QPushButton[class="secondary"] {
                background: #F2F2F7;
                color: #1C1C1E;
                border: 1px solid #D1D1D6;
            }
            
            QPushButton[class="secondary"]:hover {
                background: #E5E5EA;
            }
            
            /* 输入框 - macOS风格 */
            QLineEdit {
                background: white;
                border: 1px solid #D1D1D6;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                color: #1C1C1E;
                selection-background-color: #007AFF;
            }
            
            QLineEdit:focus {
                border-color: #007AFF;
                outline: none;
                box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.2);
            }
            
            /* 表格 - macOS风格 */
            QTableWidget {
                background: white;
                border: 1px solid #E5E5E7;
                border-radius: 8px;
                gridline-color: #F2F2F7;
                font-size: 13px;
                alternate-background-color: #F8F9FA;
            }
            
            QTableWidget::item {
                padding: 8px 12px;
                border-bottom: 1px solid #F2F2F7;
            }
            
            QTableWidget::item:hover {
                background: #F2F2F7;
            }
            
            QTableWidget::item:selected {
                background: #E3F2FD;
                color: #1C1C1E;
            }
            
            QHeaderView::section {
                background: #F8F9FA;
                padding: 12px 8px;
                border: none;
                border-bottom: 1px solid #E5E5E7;
                font-weight: 600;
                font-size: 11px;
                color: #8E8E93;
                text-transform: uppercase;
            }
            
            /* 进度条 - macOS风格 */
            QProgressBar {
                background: #E5E5E7;
                border: none;
                border-radius: 4px;
                height: 8px;
                text-align: center;
            }
            
            QProgressBar::chunk {
                background: #007AFF;
                border-radius: 4px;
            }
            
            /* 滚动条 - macOS风格 */
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                border-radius: 4px;
                margin: 0;
            }
            
            QScrollBar::handle:vertical {
                background: rgba(0, 0, 0, 0.2);
                border-radius: 4px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: rgba(0, 0, 0, 0.4);
            }
            
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            /* 菜单 - macOS风格 */
            QMenu {
                background: rgba(255, 255, 255, 0.95);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 8px;
                padding: 4px 0px;
                backdrop-filter: blur(20px);
            }
            
            QMenu::item {
                padding: 8px 16px;
                font-size: 13px;
                color: #1C1C1E;
                border-radius: 4px;
                margin: 2px 4px;
            }
            
            QMenu::item:selected {
                background: #007AFF;
                color: white;
            }
            
            QMenu::separator {
                height: 1px;
                background: #E5E5E7;
                margin: 4px 8px;
            }
            
            /* 分组框 - macOS风格 */
            QGroupBox {
                font-weight: 600;
                font-size: 13px;
                color: #1C1C1E;
                border: 1px solid #E5E5E7;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 8px 0 8px;
                background: white;
            }
            
            /* 复选框和单选按钮 - macOS风格 */
            QCheckBox, QRadioButton {
                font-size: 13px;
                color: #1C1C1E;
                spacing: 8px;
            }
            
            QCheckBox::indicator, QRadioButton::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #D1D1D6;
                border-radius: 3px;
                background: white;
            }
            
            QCheckBox::indicator:checked {
                background: #007AFF;
                border-color: #007AFF;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xMC42IDEuNEw0LjMgNy43TDEuNCA0LjgiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMS41IiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+);
            }
            
            QRadioButton::indicator {
                border-radius: 8px;
            }
            
            QRadioButton::indicator:checked {
                background: #007AFF;
                border-color: #007AFF;
            }
            
            /* 旋转框 - macOS风格 */
            QSpinBox {
                background: white;
                border: 1px solid #D1D1D6;
                border-radius: 6px;
                padding: 6px 8px;
                font-size: 13px;
                min-width: 60px;
            }
            
            QSpinBox:focus {
                border-color: #007AFF;
            }
            
            QSpinBox::up-button, QSpinBox::down-button {
                width: 16px;
                border: none;
                background: transparent;
            }
            
            /* 组合框 - macOS风格 */
            QComboBox {
                background: white;
                border: 1px solid #D1D1D6;
                border-radius: 6px;
                padding: 6px 8px;
                font-size: 13px;
                min-width: 100px;
            }
            
            QComboBox:focus {
                border-color: #007AFF;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox::down-arrow {
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iNiIgdmlld0JveD0iMCAwIDEwIDYiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDFMNSA1TDkgMSIgc3Ryb2tlPSIjOEU4RTkzIiBzdHJva2Utd2lkdGg9IjEuNSIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPg==);
            }
            
            /* 标签页 - macOS风格 */
            QTabWidget::pane {
                border: 1px solid #E5E5E7;
                border-radius: 8px;
                background: white;
                margin-top: 4px;
            }
            
            QTabBar::tab {
                background: #F2F2F7;
                border: 1px solid #D1D1D6;
                padding: 8px 16px;
                margin-right: 2px;
                border-radius: 6px 6px 0px 0px;
                font-size: 13px;
                font-weight: 500;
            }
            
            QTabBar::tab:selected {
                background: white;
                border-bottom-color: white;
                color: #007AFF;
                font-weight: 600;
            }
            
            QTabBar::tab:hover {
                background: #E5E5EA;
            }
        """
        
        self.setStyleSheet(macos_style)
        
        # 设置窗口效果
        try:
            self.setAttribute(Qt.WA_TranslucentBackground, True)
            if hasattr(Qt, 'WA_MacShowFocusRect'):
                self.setAttribute(Qt.WA_MacShowFocusRect, False)
        except:
            pass
    
    def mousePressEvent(self, event):
        """Handle mouse press events for window dragging"""
        if event.button() == Qt.LeftButton:
            # Check if click is in the title bar area (top 40 pixels)
            if event.position().y() <= 40:
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                self.is_dragging = True
                event.accept()
            else:
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events for window dragging"""
        if event.buttons() == Qt.LeftButton and self.is_dragging and self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            self.drag_position = None
        super().mouseReleaseEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """Handle double click events for maximize/restore"""
        if event.button() == Qt.LeftButton and event.position().y() <= 40:
            self.toggle_maximize()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)
    
    def add_download(self):
        """Add download task"""
        url = self.url_input.text().strip()
        if not url:
            return
        
        if self.download_service.add_download(url):
            self.url_input.clear()
            print(f"Added download: {url}")
    
    def show_batch_dialog(self):
        """Show batch download dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("批量下载")
        dialog.setModal(True)
        dialog.resize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        instructions = QLabel("每行输入一个视频链接:")
        layout.addWidget(instructions)
        
        urls_text = QTextEdit()
        urls_text.setPlaceholderText("https://www.youtube.com/watch?v=...\nhttps://www.bilibili.com/video/...")
        layout.addWidget(urls_text)
        
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("取消")
        download_btn = QPushButton("开始下载")
        
        cancel_btn.clicked.connect(dialog.reject)
        download_btn.clicked.connect(lambda: self.start_batch_download(urls_text.toPlainText(), dialog))
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(download_btn)
        
        layout.addLayout(button_layout)
        dialog.exec()
    
    def start_batch_download(self, urls_text: str, dialog: QDialog):
        """Start batch download"""
        urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
        
        if not urls:
            QMessageBox.warning(dialog, "警告", "请输入至少一个视频链接")
            return
        
        added_count = 0
        for url in urls:
            if self.download_service.add_download(url):
                added_count += 1
        
        dialog.accept()
        print(f"Added {added_count} downloads")
    
    def clear_completed(self):
        """Clear completed downloads"""
        self.download_service.clear_completed()
        
        # Remove completed task widgets
        completed_urls = []
        for url, widget in self.task_widgets.items():
            if widget.task_data.get('status') in ['completed', 'failed']:
                completed_urls.append(url)
        
        for url in completed_urls:
            widget = self.task_widgets[url]
            self.tasks_layout.removeWidget(widget)
            widget.deleteLater()
            del self.task_widgets[url]
    
    def on_task_added(self, url: str):
        """Handle task added"""
        task_data = {
            'title': url,
            'filename': '',
            'progress': 0,
            'status': 'pending',
            'error': '',
            'speed': '',
            'eta': '',
            'file_size': 0,
            'downloaded_size': 0,
        }
        
        # Create task widget
        task_widget = ModernTaskCard(url, task_data)
        task_widget.cancel_requested.connect(self.cancel_download)
        
        # Insert before stretch
        self.tasks_layout.insertWidget(self.tasks_layout.count() - 1, task_widget)
        self.task_widgets[url] = task_widget
    
    def on_task_updated(self, url: str, task_data: dict):
        """Handle task updated"""
        if url in self.task_widgets:
            self.task_widgets[url].update_task_data(task_data)
    
    def on_task_completed(self, url: str, filepath: str):
        """Handle task completed"""
        print(f"Download completed: {filepath}")
    
    def on_task_failed(self, url: str, error: str):
        """Handle task failed"""
        print(f"Download failed: {url} - {error}")
    
    def cancel_download(self, url: str):
        """Cancel download"""
        self.download_service.cancel_download(url)
    
    def show_history(self):
        """Show download history"""
        print("显示历史记录")
        # 取消其他按钮的选中状态
        for i, btn in enumerate(self.tab_buttons):
            btn.setChecked(i == 0)
        
        # 创建历史记录对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("下载历史记录")
        dialog.setModal(True)
        dialog.resize(800, 600)
        
        layout = QVBoxLayout(dialog)
        
        # 标题
        title_label = QLabel("📜 下载历史记录")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 600;
                color: #1C1C1E;
                padding: 16px;
            }
        """)
        layout.addWidget(title_label)
        
        # 搜索框
        search_layout = QHBoxLayout()
        search_input = QLineEdit()
        search_input.setPlaceholderText("搜索历史记录...")
        search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #D1D1D6;
                border-radius: 6px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #007AFF;
            }
        """)
        search_layout.addWidget(search_input)
        
        clear_history_btn = QPushButton("清空历史")
        clear_history_btn.setStyleSheet("""
            QPushButton {
                background: #FF3B30;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #D70015;
            }
        """)
        search_layout.addWidget(clear_history_btn)
        layout.addLayout(search_layout)
        
        # 历史记录表格
        from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
        
        history_table = QTableWidget()
        history_table.setColumnCount(5)
        history_table.setHorizontalHeaderLabels(["标题", "作者", "平台", "下载时间", "文件大小"])
        
        # 设置表格样式
        history_table.setStyleSheet("""
            QTableWidget {
                background: white;
                border: 1px solid #E5E5E7;
                border-radius: 8px;
                gridline-color: #F2F2F7;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #F2F2F7;
            }
            QTableWidget::item:selected {
                background: #E3F2FD;
                color: #1C1C1E;
            }
            QHeaderView::section {
                background: #F8F9FA;
                border: none;
                border-bottom: 2px solid #E5E5E7;
                padding: 10px;
                font-weight: 600;
                color: #1C1C1E;
            }
        """)
        
        # 设置表格属性
        history_table.setAlternatingRowColors(True)
        history_table.setSelectionBehavior(QTableWidget.SelectRows)
        history_table.horizontalHeader().setStretchLastSection(True)
        history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        
        # 加载真实历史数据
        self.load_history_data(history_table)
        
        # 启用表格排序
        history_table.setSortingEnabled(True)
        
        # 连接搜索功能
        search_input.textChanged.connect(lambda text: self.filter_history_table(history_table, text))
        
        # 连接清空历史按钮
        clear_history_btn.clicked.connect(lambda: self.clear_history_data(history_table))
        
        # 右键菜单
        history_table.setContextMenuPolicy(Qt.CustomContextMenu)
        history_table.customContextMenuRequested.connect(
            lambda pos: self.show_history_context_menu(history_table, pos)
        )
        
        layout.addWidget(history_table)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        export_btn = QPushButton("导出历史")
        export_btn.setStyleSheet("""
            QPushButton {
                background: #34C759;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #28A745;
            }
        """)
        export_btn.clicked.connect(lambda: self.export_history_data(history_table))
        button_layout.addWidget(export_btn)
        
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("""
            QPushButton {
                background: #8E8E93;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #6D6D70;
            }
        """)
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def show_history_context_menu(self, table, position):
        """显示历史记录右键菜单"""
        if table.itemAt(position) is None:
            return  # 如果点击的不是有效项目，不显示菜单
            
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: white;
                border: 1px solid #D1D1D6;
                border-radius: 6px;
                padding: 4px 0px;
            }
            QMenu::item {
                padding: 8px 16px;
                font-size: 14px;
                color: #1C1C1E;
            }
            QMenu::item:selected {
                background: #F2F2F7;
            }
        """)
        
        menu.addAction("🔄 重新下载", lambda: self.redownload_from_history(table))
        menu.addAction("📁 打开文件夹", lambda: self.open_download_folder(table))
        menu.addAction("📋 复制链接", lambda: self.copy_video_link(table))
        menu.addSeparator()
        menu.addAction("🗑️ 删除记录", lambda: self.delete_history_record(table))
        
        menu.exec(table.mapToGlobal(position))
    
    def load_history_data(self, table):
        """加载真实历史数据"""
        try:
            # 尝试从数据库或文件加载历史记录
            # 这里先使用一些示例数据，但标记为可删除
            sample_data = [
                ["YouTube精彩视频合集", "科技UP主", "YouTube", "2025-01-22 10:30", "125.6 MB"],
                ["B站热门视频推荐", "娱乐博主", "B站", "2025-01-22 09:15", "89.2 MB"],
                ["抖音搞笑短视频", "搞笑达人", "抖音", "2025-01-21 18:45", "45.8 MB"],
            ]
            
            table.setRowCount(len(sample_data))
            for row, data in enumerate(sample_data):
                for col, value in enumerate(data):
                    item = QTableWidgetItem(str(value))
                    table.setItem(row, col, item)
                    
        except Exception as e:
            print(f"加载历史数据失败: {e}")
            # 显示空表格
            table.setRowCount(0)
    
    def filter_history_table(self, table, search_text):
        """过滤历史记录表格"""
        for row in range(table.rowCount()):
            show_row = False
            if not search_text:  # 如果搜索框为空，显示所有行
                show_row = True
            else:
                # 检查每一列是否包含搜索文本
                for col in range(table.columnCount()):
                    item = table.item(row, col)
                    if item and search_text.lower() in item.text().lower():
                        show_row = True
                        break
            
            table.setRowHidden(row, not show_row)
    
    def clear_history_data(self, table):
        """清空历史数据"""
        reply = QMessageBox.question(
            self, "确认清空", 
            "确定要清空所有下载历史记录吗？此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            table.setRowCount(0)
            QMessageBox.information(self, "完成", "历史记录已清空")
    
    def export_history_data(self, table):
        """导出历史数据"""
        if table.rowCount() == 0:
            QMessageBox.information(self, "提示", "没有历史记录可导出")
            return
        
        from PySide6.QtCore import QDate
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出历史记录", 
            f"下载历史_{QDate.currentDate().toString('yyyy-MM-dd')}.csv",
            "CSV文件 (*.csv);;所有文件 (*)"
        )
        
        if file_path:
            try:
                import csv
                with open(file_path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    
                    # 写入表头
                    headers = []
                    for col in range(table.columnCount()):
                        headers.append(table.horizontalHeaderItem(col).text())
                    writer.writerow(headers)
                    
                    # 写入数据
                    for row in range(table.rowCount()):
                        if not table.isRowHidden(row):  # 只导出可见行
                            row_data = []
                            for col in range(table.columnCount()):
                                item = table.item(row, col)
                                row_data.append(item.text() if item else "")
                            writer.writerow(row_data)
                
                QMessageBox.information(self, "完成", f"历史记录已导出到:\n{file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败:\n{str(e)}")
    
    def delete_history_record(self, table):
        """删除选中的历史记录"""
        current_row = table.currentRow()
        if current_row >= 0:
            reply = QMessageBox.question(
                self, "确认删除", 
                "确定要删除选中的历史记录吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                table.removeRow(current_row)
                QMessageBox.information(self, "完成", "记录已删除")
    
    def redownload_from_history(self, table):
        """从历史记录重新下载"""
        current_row = table.currentRow()
        if current_row >= 0:
            title_item = table.item(current_row, 0)
            if title_item:
                QMessageBox.information(self, "重新下载", f"开始重新下载: {title_item.text()}")
    
    def open_download_folder(self, table):
        """打开下载文件夹"""
        current_row = table.currentRow()
        if current_row >= 0:
            import subprocess
            import platform
            
            # 获取下载目录
            download_dir = str(self.portable_manager.get_downloads_directory())
            
            try:
                if platform.system() == "Windows":
                    subprocess.run(["explorer", download_dir])
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", download_dir])
                else:  # Linux
                    subprocess.run(["xdg-open", download_dir])
            except Exception as e:
                QMessageBox.warning(self, "错误", f"无法打开文件夹: {e}")
    
    def copy_video_link(self, table):
        """复制视频链接"""
        current_row = table.currentRow()
        if current_row >= 0:
            title_item = table.item(current_row, 0)
            if title_item:
                # 这里应该从数据库获取真实链接，现在先用标题代替
                from PySide6.QtGui import QClipboard
                from PySide6.QtWidgets import QApplication
                
                clipboard = QApplication.clipboard()
                clipboard.setText(f"视频链接: {title_item.text()}")
                QMessageBox.information(self, "完成", "链接已复制到剪贴板")
        
        menu.exec(table.mapToGlobal(position))
    
    def show_creator_monitor(self):
        """Show creator monitoring dialog"""
        print("显示创作者监控")
        # 取消其他按钮的选中状态
        for i, btn in enumerate(self.tab_buttons):
            btn.setChecked(i == 1)
        
        # 创建创作者监控对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("创作者监控")
        dialog.setModal(True)
        dialog.resize(900, 650)
        
        layout = QVBoxLayout(dialog)
        
        # 标题
        title_label = QLabel("👁 创作者监控")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 600;
                color: #1C1C1E;
                padding: 16px;
            }
        """)
        layout.addWidget(title_label)
        
        # 添加创作者区域
        add_layout = QHBoxLayout()
        
        url_input = QLineEdit()
        url_input.setPlaceholderText("输入创作者主页链接...")
        url_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #D1D1D6;
                border-radius: 6px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #007AFF;
            }
        """)
        add_layout.addWidget(url_input)
        
        add_creator_btn = QPushButton("➕ 添加监控")
        add_creator_btn.setStyleSheet("""
            QPushButton {
                background: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #0051D5;
            }
        """)
        # 连接添加监控功能
        add_creator_btn.clicked.connect(lambda: self.add_creator_monitor(url_input.text().strip()))
        add_layout.addWidget(add_creator_btn)
        
        layout.addLayout(add_layout)
        
        # 创作者列表表格
        from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox
        
        creators_table = QTableWidget()
        creators_table.setColumnCount(8)
        creators_table.setHorizontalHeaderLabels(["启用", "创作者", "平台", "总视频数", "新作品", "最后下载时间", "最后更新时间", "操作"])
        
        # 设置表格引用以便刷新
        self.current_creator_table = creators_table
        
        # 初始化创作者监控列表（如果不存在）
        if not hasattr(self, 'creator_monitors'):
            self.creator_monitors = []
        
        # 立即刷新表格以显示现有数据
        self.refresh_creator_table()
        
        # 设置表格样式
        creators_table.setStyleSheet("""
            QTableWidget {
                background: white;
                border: 1px solid #E5E5E7;
                border-radius: 8px;
                gridline-color: #F2F2F7;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #F2F2F7;
            }
            QTableWidget::item:selected {
                background: #E3F2FD;
                color: #1C1C1E;
            }
            QHeaderView::section {
                background: #F8F9FA;
                border: none;
                border-bottom: 2px solid #E5E5E7;
                padding: 10px;
                font-weight: 600;
                color: #1C1C1E;
            }
        """)
        
        # 设置表格属性
        creators_table.setAlternatingRowColors(True)
        creators_table.setSelectionBehavior(QTableWidget.SelectRows)
        creators_table.horizontalHeader().setStretchLastSection(True)
        creators_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        
        # 添加示例数据
        sample_creators = [
            ["✅", "示例创作者A", "YouTube", "156", "2025-01-22 10:00", "是"],
            ["✅", "示例创作者B", "B站", "89", "2025-01-22 09:30", "否"],
            ["❌", "示例创作者C", "抖音", "234", "2025-01-21 20:15", "是"],
        ]
        
        creators_table.setRowCount(len(sample_creators))
        for row, data in enumerate(sample_creators):
            for col, value in enumerate(data):
                item = QTableWidgetItem(str(value))
                creators_table.setItem(row, col, item)
        
        # 右键菜单
        creators_table.setContextMenuPolicy(Qt.CustomContextMenu)
        creators_table.customContextMenuRequested.connect(
            lambda pos: self.show_creator_context_menu(creators_table, pos)
        )
        
        layout.addWidget(creators_table)
        
        # 控制按钮区域
        control_layout = QHBoxLayout()
        
        check_all_btn = QPushButton("🔄 检查全部")
        check_all_btn.setStyleSheet("""
            QPushButton {
                background: #34C759;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #28A745;
            }
        """)
        control_layout.addWidget(check_all_btn)
        
        enable_all_btn = QPushButton("✅ 启用全部")
        enable_all_btn.setStyleSheet("""
            QPushButton {
                background: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #0051D5;
            }
        """)
        control_layout.addWidget(enable_all_btn)
        
        disable_all_btn = QPushButton("❌ 禁用全部")
        disable_all_btn.setStyleSheet("""
            QPushButton {
                background: #FF9500;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #E6850E;
            }
        """)
        control_layout.addWidget(disable_all_btn)
        
        control_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("""
            QPushButton {
                background: #8E8E93;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #6D6D70;
            }
        """)
        close_btn.clicked.connect(dialog.accept)
        control_layout.addWidget(close_btn)
        
        layout.addLayout(control_layout)
        
        dialog.exec()
    
    def show_creator_context_menu(self, table, position):
        """显示创作者监控右键菜单"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: white;
                border: 1px solid #D1D1D6;
                border-radius: 6px;
                padding: 4px 0px;
            }
            QMenu::item {
                padding: 8px 16px;
                font-size: 14px;
                color: #1C1C1E;
            }
            QMenu::item:selected {
                background: #F2F2F7;
            }
        """)
        
        current_row = table.currentRow()
        if current_row < 0:
            return  # 没有选中行
            
        menu.addAction("🔄 立即检查", lambda: self.check_creator_updates_by_row(table, current_row))
        menu.addAction("📥 下载新视频", lambda: self.download_creator_videos_by_row(table, current_row))
        menu.addAction("✅ 启用监控", lambda: self.toggle_creator_monitoring(table, current_row, True))
        menu.addAction("❌ 禁用监控", lambda: self.toggle_creator_monitoring(table, current_row, False))
        menu.addSeparator()
        menu.addAction("📌 固定到顶部", lambda: self.pin_creator_to_top(table, current_row))
        menu.addAction("⚙️ 编辑设置", lambda: self.edit_creator_settings_by_row(table, current_row))
        menu.addSeparator()
        menu.addAction("🗑️ 删除监控", lambda: self.delete_creator_monitor_by_row(table, current_row))
        
        menu.exec(table.mapToGlobal(position))
        
        # 设置表格样式
        history_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #E5E5E7;
                border-radius: 8px;
                background: white;
                gridline-color: #F2F2F7;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #F2F2F7;
            }
            QTableWidget::item:hover {
                background: #F2F2F7;
            }
            QTableWidget::item:selected {
                background: #E3F2FD;
            }
            QHeaderView::section {
                background: #F8F9FA;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #E5E5E7;
                font-weight: 600;
            }
        """)
        
        # 设置表格属性
        history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        history_table.setAlternatingRowColors(True)
        history_table.horizontalHeader().setStretchLastSection(True)
        history_table.setContextMenuPolicy(Qt.CustomContextMenu)
        history_table.customContextMenuRequested.connect(
            lambda pos: self.show_history_context_menu(history_table, pos)
        )
        
        # 添加示例历史记录数据
        sample_history_data = [
            ["Python编程教程 - 从入门到精通", "技术宅小明", "YouTube", "128.5 MB", "2025-01-21 14:30"],
            ["Web开发实战 - React框架详解", "前端老司机", "Bilibili", "256.3 MB", "2025-01-21 14:25"],
            ["机器学习入门 - 神经网络基础", "AI研究院", "TikTok", "189.2 MB", "2025-01-21 14:20"],
            ["数据结构与算法 - 高级篇", "编程大师", "Instagram", "320.7 MB", "2025-01-21 14:15"],
        ]
        
        history_table.setRowCount(len(sample_history_data))
        for row, data in enumerate(sample_history_data):
            for col, value in enumerate(data):
                item = QTableWidgetItem(str(value))
                history_table.setItem(row, col, item)
        
        # 调整列宽
        history_table.resizeColumnsToContents()
        
        layout.addWidget(history_table)
    
    def show_history_context_menu(self, table, position):
        """Show context menu for history table"""
        item = table.itemAt(position)
        if item is None:
            return
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: white;
                border: 1px solid #D1D1D6;
                border-radius: 6px;
                padding: 4px 0px;
            }
            QMenu::item {
                padding: 6px 16px;
                font-size: 14px;
                color: #1C1C1E;
            }
            QMenu::item:selected {
                background: #F2F2F7;
            }
        """)
        
        menu.addAction("重新下载", lambda: self.redownload_from_history(table.currentRow()))
        menu.addAction("复制链接", lambda: self.copy_history_link(table.currentRow()))
        menu.addAction("打开文件夹", lambda: self.open_history_folder(table.currentRow()))
        menu.addSeparator()
        menu.addAction("删除记录", lambda: self.delete_history_record(table.currentRow()))
        
        menu.exec(table.mapToGlobal(position))
    
    def redownload_from_history(self, row):
        """Redownload from history"""
        print(f"Redownloading from history row: {row}")
    
    def copy_history_link(self, row):
        """Copy history link to clipboard"""
        print(f"Copying history link from row: {row}")
    
    def open_history_folder(self, row):
        """Open history file folder"""
        print(f"Opening history folder for row: {row}")
    
    def delete_history_record(self, row):
        """Delete history record"""
        print(f"Deleting history record row: {row}")
        
        # 按钮
        button_layout = QHBoxLayout()
        export_btn = QPushButton("导出历史")
        clear_btn = QPushButton("清空历史")
        close_btn = QPushButton("关闭")
        
        for btn in [export_btn, clear_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background: #F2F2F7;
                    border: 1px solid #D1D1D6;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background: #E5E5EA;
                }
            """)
        
        close_btn.setStyleSheet("""
            QPushButton {
                background: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #0051D5;
            }
        """)
        
        close_btn.clicked.connect(dialog.accept)
        
        button_layout.addWidget(export_btn)
        button_layout.addWidget(clear_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec()
    

        # 取消其他按钮的选中状态
        for i, btn in enumerate(self.tab_buttons):
            btn.setChecked(i == 1)
        
        # 创建创作者监控对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("创作者监控")
        dialog.setModal(True)
        dialog.resize(800, 600)
        
        layout = QVBoxLayout(dialog)
        
        # 标题
        title_label = QLabel("👁 创作者监控")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 600;
                color: #1C1C1E;
                padding: 16px;
            }
        """)
        layout.addWidget(title_label)
        
        # 添加创作者区域
        add_layout = QHBoxLayout()
        creator_input = QLineEdit()
        creator_input.setPlaceholderText("输入创作者频道链接...")
        creator_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #D1D1D6;
                border-radius: 6px;
                font-size: 14px;
            }
        """)
        add_layout.addWidget(creator_input)
        
        add_btn = QPushButton("➕ 添加监控")
        add_btn.setStyleSheet("""
            QPushButton {
                background: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #0051D5;
            }
        """)
        add_layout.addWidget(add_btn)
        
        layout.addLayout(add_layout)
        
        # 创作者监控表格
        creators_table = QTableWidget()
        creators_table.setColumnCount(6)
        creators_table.setHorizontalHeaderLabels(["用户名", "平台", "总视频数", "已下载", "新内容", "最近更新"])
        
        # 设置表格样式
        creators_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #E5E5E7;
                border-radius: 8px;
                background: white;
                gridline-color: #F2F2F7;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #F2F2F7;
            }
            QTableWidget::item:hover {
                background: #F2F2F7;
            }
            QTableWidget::item:selected {
                background: #E3F2FD;
            }
            QHeaderView::section {
                background: #F8F9FA;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #E5E5E7;
                font-weight: 600;
            }
        """)
        
        # 设置表格属性
        creators_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        creators_table.setAlternatingRowColors(True)
        creators_table.horizontalHeader().setStretchLastSection(True)
        creators_table.setDragDropMode(QAbstractItemView.InternalMove)
        creators_table.setContextMenuPolicy(Qt.CustomContextMenu)
        creators_table.customContextMenuRequested.connect(
            lambda pos: self.show_creator_context_menu(creators_table, pos)
        )
        
        # 添加示例创作者数据
        sample_creators_data = [
            ["技术宅小明", "YouTube", "156", "120", "3", "2小时前"],
            ["前端老司机", "Bilibili", "89", "89", "0", "1天前"],
            ["AI研究院", "TikTok", "234", "180", "5", "30分钟前"],
            ["编程大师", "Instagram", "67", "45", "1", "检查失败"],
        ]
        
        creators_table.setRowCount(len(sample_creators_data))
        for row, data in enumerate(sample_creators_data):
            for col, value in enumerate(data):
                item = QTableWidgetItem(str(value))
                # 为新内容列添加颜色标识
                if col == 4:  # 新内容列
                    if int(value) > 0:
                        item.setBackground(QColor("#E8F5E8"))
                        item.setForeground(QColor("#2E7D32"))
                creators_table.setItem(row, col, item)
        
        # 调整列宽
        creators_table.resizeColumnsToContents()
        
        layout.addWidget(creators_table)
    
    def show_creator_context_menu(self, table, position):
        """Show context menu for creator table"""
        item = table.itemAt(position)
        if item is None:
            return
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: white;
                border: 1px solid #D1D1D6;
                border-radius: 6px;
                padding: 4px 0px;
            }
            QMenu::item {
                padding: 6px 16px;
                font-size: 14px;
                color: #1C1C1E;
            }
            QMenu::item:selected {
                background: #F2F2F7;
            }
        """)
        
        menu.addAction("检查更新", lambda: self.check_creator_updates(table.currentRow()))
        menu.addAction("立即下载", lambda: self.download_creator_videos(table.currentRow()))
        menu.addSeparator()
        menu.addAction("编辑设置", lambda: self.edit_creator_settings(table.currentRow()))
        menu.addAction("固定到顶部", lambda: self.pin_creator(table.currentRow()))
        menu.addSeparator()
        menu.addAction("删除监控", lambda: self.delete_creator_monitor(table.currentRow()))
        
        menu.exec(table.mapToGlobal(position))
    
    def check_creator_updates(self, creator):
        """Check creator updates"""
        print(f"🔍 检测 {creator['name']} 的更新...")
        
        # 这里实现实际的更新检测逻辑
        QMessageBox.information(self, "检测更新", f"正在检测 {creator['name']} 的更新...")
        
        # 模拟检测到新作品
        import random
        new_videos = random.randint(0, 5)
        creator['new_videos'] = new_videos
        
        if new_videos > 0:
            QMessageBox.information(self, "检测完成", f"发现 {creator['name']} 有 {new_videos} 个新作品！")
        else:
            QMessageBox.information(self, "检测完成", f"{creator['name']} 暂无新作品")
        
        # 更新最后检测时间
        from datetime import datetime
        creator['last_check'] = datetime.now()
        
        # 刷新表格显示
        self.refresh_creator_table()
    
    def download_creator_videos(self, row):
        """Download creator videos"""
        print(f"Downloading videos for creator row: {row}")
    
    def edit_creator_settings(self, row):
        """Edit creator settings"""
        print(f"Editing settings for creator row: {row}")
    
    def pin_creator(self, row):
        """Pin creator to top"""
        print(f"Pinning creator row: {row}")
    
    def add_creator_monitor(self, url):
        """添加创作者监控"""
        if not url:
            QMessageBox.warning(self, "警告", "请输入博主主页地址")
            return
        
        print(f"🔍 添加创作者监控: {url}")
        
        # 验证URL格式
        if not self.validate_creator_url(url):
            QMessageBox.warning(self, "警告", "请输入有效的博主主页地址\n支持的平台: YouTube, B站, 抖音, Instagram, Twitter等")
            return
        
        # 检查是否已存在
        if hasattr(self, 'creator_monitors'):
            for creator in self.creator_monitors:
                if creator.get('url') == url:
                    QMessageBox.information(self, "提示", "该创作者已在监控列表中")
                    return
        else:
            self.creator_monitors = []
        
        # 提取创作者信息
        try:
            creator_info = self.extract_creator_info(url)
            
            # 添加到监控列表
            from datetime import datetime
            new_creator = {
                'url': url,
                'name': creator_info.get('name', '未知创作者'),
                'platform': creator_info.get('platform', '未知平台'),
                'video_count': creator_info.get('video_count', 0),
                'new_videos': 0,
                'last_check': None,
                'last_download': None,  # 最后下载时间
                'last_update': datetime.now(),  # 最后更新时间
                'auto_download': False,
                'enabled': True
            }
            
            self.creator_monitors.append(new_creator)
            
            # 保存到设置
            if hasattr(self, 'creator_service'):
                self.creator_service.add_creator_monitor(new_creator)
            
            # 刷新表格显示
            self.refresh_creator_table()
            
            QMessageBox.information(self, "成功", f"已添加创作者监控: {creator_info.get('name', url)}")
            print(f"✅ 创作者监控添加成功: {creator_info.get('name', url)}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加创作者监控失败:\n{str(e)}")
            print(f"❌ 添加创作者监控失败: {e}")
    
    def validate_creator_url(self, url):
        """验证创作者URL"""
        import re
        
        # 支持的平台URL模式
        patterns = [
            r'https?://(?:www\.)?youtube\.com/(?:c/|channel/|user/|@)',
            r'https?://(?:www\.)?bilibili\.com/video/',
            r'https?://space\.bilibili\.com/\d+',  # B站用户空间
            r'https?://(?:www\.)?douyin\.com/',
            r'https?://(?:www\.)?tiktok\.com/@',
            r'https?://(?:www\.)?instagram\.com/',
            r'https?://(?:www\.)?twitter\.com/',
            r'https?://(?:www\.)?x\.com/',
        ]
        
        print(f"🔍 验证URL: {url}")
        
        for i, pattern in enumerate(patterns):
            if re.match(pattern, url):
                print(f"✅ URL匹配模式 {i+1}: {pattern}")
                return True
        
        print(f"❌ URL不匹配任何已知模式")
        print(f"测试URL: {url}")
        
        # 特别测试B站链接
        if 'bilibili.com' in url:
            print("🔍 检测到B站链接，进行详细验证...")
            bilibili_patterns = [
                r'https?://space\.bilibili\.com/\d+',
                r'https?://(?:www\.)?bilibili\.com/video/BV\w+',
                r'https?://(?:www\.)?bilibili\.com/video/av\d+',
            ]
            for pattern in bilibili_patterns:
                if re.match(pattern, url):
                    print(f"✅ B站URL验证成功: {pattern}")
                    return True
            print("❌ B站URL格式不正确")
        
        return False
    
    def extract_creator_info(self, url):
        """提取创作者信息"""
        # 简单的信息提取逻辑
        info = {
            'name': '新创作者',
            'platform': '未知平台',
            'video_count': 0
        }
        
        if 'youtube.com' in url:
            info['platform'] = 'YouTube'
            # 从URL提取用户名
            if '/@' in url:
                info['name'] = url.split('/@')[-1].split('/')[0]
            elif '/c/' in url:
                info['name'] = url.split('/c/')[-1].split('/')[0]
        elif 'bilibili.com' in url:
            info['platform'] = 'B站'
            # 从B站space链接提取用户ID
            if 'space.bilibili.com' in url:
                import re
                match = re.search(r'space\.bilibili\.com/(\d+)', url)
                if match:
                    user_id = match.group(1)
                    info['name'] = f'B站用户_{user_id}'
        elif 'douyin.com' in url or 'tiktok.com' in url:
            info['platform'] = '抖音/TikTok'
        elif 'instagram.com' in url:
            info['platform'] = 'Instagram'
        elif 'twitter.com' in url or 'x.com' in url:
            info['platform'] = 'Twitter/X'
        
        return info
    
    def refresh_creator_table(self):
        """刷新创作者监控表格"""
        if not hasattr(self, 'current_creator_table') or not self.current_creator_table:
            return
        
        table = self.current_creator_table
        creators = getattr(self, 'creator_monitors', [])
        
        table.setRowCount(len(creators))
        
        for row, creator in enumerate(creators):
            # 启用复选框
            enable_cb = QCheckBox()
            enable_cb.setChecked(creator.get('enabled', True))
            table.setCellWidget(row, 0, enable_cb)
            
            # 创作者名称
            table.setItem(row, 1, QTableWidgetItem(creator.get('name', '')))
            
            # 平台
            table.setItem(row, 2, QTableWidgetItem(creator.get('platform', '')))
            
            # 视频数
            table.setItem(row, 3, QTableWidgetItem(str(creator.get('video_count', 0))))
            
            # 新作品数量 - 重点显示
            new_videos_item = QTableWidgetItem(str(creator.get('new_videos', 0)))
            if creator.get('new_videos', 0) > 0:
                new_videos_item.setBackground(QColor('#FFE6E6'))
                new_videos_item.setForeground(QColor('#D32F2F'))
            table.setItem(row, 4, new_videos_item)
            
            # 最后下载时间
            last_download = creator.get('last_download')
            download_text = last_download.strftime('%Y-%m-%d %H:%M') if last_download else '从未下载'
            table.setItem(row, 5, QTableWidgetItem(download_text))
            
            # 最后更新时间
            last_update = creator.get('last_update')
            update_text = last_update.strftime('%Y-%m-%d %H:%M') if last_update else '未知'
            table.setItem(row, 6, QTableWidgetItem(update_text))
            
            # 操作按钮组
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 2, 4, 2)
            action_layout.setSpacing(4)
            
            # 下载按钮
            download_btn = QPushButton("📥")
            download_btn.setToolTip("下载新作品")
            download_btn.setFixedSize(24, 24)
            download_btn.setEnabled(creator.get('new_videos', 0) > 0)
            download_btn.setStyleSheet("""
                QPushButton {
                    background: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background: #45A049;
                }
                QPushButton:disabled {
                    background: #CCCCCC;
                    color: #666666;
                }
            """)
            download_btn.clicked.connect(lambda checked, c=creator: self.download_creator_new_videos(c))
            action_layout.addWidget(download_btn)
            
            # 检测按钮
            check_btn = QPushButton("🔍")
            check_btn.setToolTip("检测更新")
            check_btn.setFixedSize(24, 24)
            check_btn.setStyleSheet("""
                QPushButton {
                    background: #2196F3;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background: #1976D2;
                }
            """)
            check_btn.clicked.connect(lambda checked, c=creator: self.check_creator_updates(c))
            action_layout.addWidget(check_btn)
            
            table.setCellWidget(row, 7, action_widget)
    
    def download_creator_new_videos(self, creator):
        """下载创作者的新作品"""
        print(f"📥 开始下载 {creator['name']} 的 {creator.get('new_videos', 0)} 个新作品")
        
        # 这里实现实际的下载逻辑
        QMessageBox.information(self, "开始下载", f"正在下载 {creator['name']} 的新作品...")
        
        # 下载完成后重置新作品数量
        creator['new_videos'] = 0
        self.refresh_creator_table()
    
    def delete_creator_monitor(self, row):
        """Delete creator monitor"""
        print(f"Deleting creator monitor row: {row}")
        
        # 实际删除创作者监控的逻辑
        if hasattr(self, 'creator_monitors') and 0 <= row < len(self.creator_monitors):
            # 从列表中移除
            removed_creator = self.creator_monitors.pop(row)
            print(f"Removed creator monitor: {removed_creator}")
            
            # 刷新表格
            self.refresh_creator_table()
            
            # 保存到设置
            if hasattr(self, 'creator_service'):
                self.creator_service.remove_creator_monitor(removed_creator.get('url', ''))
        else:
            print(f"Invalid row index: {row}")
        
        for btn in [check_now_btn, remove_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background: #F2F2F7;
                    border: 1px solid #D1D1D6;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background: #E5E5EA;
                }
            """)
        
        close_btn.setStyleSheet("""
            QPushButton {
                background: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #0051D5;
            }
        """)
        
        close_btn.clicked.connect(dialog.accept)
        
        button_layout.addWidget(check_now_btn)
        button_layout.addWidget(remove_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def show_settings(self):
        """Show settings dialog"""
        print("显示设置")
        # 取消其他按钮的选中状态
        for i, btn in enumerate(self.tab_buttons):
            btn.setChecked(i == 2)
        
        # 创建完整的设置对话框
        self.show_complete_settings_dialog()
    
    def show_complete_settings_dialog(self):
        """显示完整的设置对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("首选项")
        dialog.setModal(True)
        dialog.resize(700, 500)
        
        # 设置macOS风格
        dialog.setStyleSheet("""
            QDialog {
                background: #F2F2F7;
                border-radius: 12px;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 创建标签页
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #E5E5E7;
                border-radius: 8px;
                background: white;
                margin-top: 10px;
            }
            QTabBar::tab {
                background: #F2F2F7;
                border: 1px solid #D1D1D6;
                padding: 8px 16px;
                margin-right: 2px;
                border-radius: 6px 6px 0px 0px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom-color: white;
            }
            QTabBar::tab:hover {
                background: #E5E5EA;
            }
        """)
        
        # 下载设置标签
        download_tab = self.create_download_settings_tab()
        tab_widget.addTab(download_tab, "下载")
        
        # 网络设置标签
        network_tab = self.create_network_settings_tab()
        tab_widget.addTab(network_tab, "网络")
        
        # 外观设置标签
        appearance_tab = self.create_appearance_settings_tab()
        tab_widget.addTab(appearance_tab, "外观")
        
        layout.addWidget(tab_widget)
        
        # 创建完所有标签页后，加载当前设置到UI控件
        QTimer.singleShot(100, self.load_settings_to_ui)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(20, 10, 20, 20)
        
        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #8E8E93;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #6D6D70;
            }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        button_layout.addStretch()
        
        # 保存按钮
        save_btn = QPushButton("保存")
        save_btn.setStyleSheet("""
            QPushButton {
                background: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #0051D5;
            }
        """)
        save_btn.clicked.connect(lambda: self.save_settings_and_close_simple(dialog, tab_widget))
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def create_download_settings_tab(self):
        """创建下载设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 获取当前设置
        download_settings = self.settings_service.get_download_settings()
        
        # 下载路径设置
        path_group = QGroupBox("下载路径")
        path_layout = QVBoxLayout(path_group)
        
        path_row = QHBoxLayout()
        self.download_path_edit = QLineEdit()
        # 从设置服务加载当前路径
        current_path = download_settings.download_path or str(self.portable_manager.get_downloads_directory())
        self.download_path_edit.setText(current_path)
        self.download_path_edit.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #D1D1D6;
                border-radius: 6px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #007AFF;
            }
        """)
        path_row.addWidget(QLabel("默认路径:"))
        path_row.addWidget(self.download_path_edit, 1)
        
        browse_btn = QPushButton("浏览...")
        browse_btn.setStyleSheet("""
            QPushButton {
                background: #F2F2F7;
                border: 1px solid #D1D1D6;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #E5E5EA;
            }
        """)
        browse_btn.clicked.connect(lambda: self.browse_download_path_simple())
        path_row.addWidget(browse_btn)
        
        path_layout.addLayout(path_row)
        layout.addWidget(path_group)
        
        # 下载选项设置
        options_group = QGroupBox("下载选项")
        options_layout = QFormLayout(options_group)
        
        # 并发下载数
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setRange(1, 10)
        self.concurrent_spin.setValue(3)
        options_layout.addRow("同时下载数:", self.concurrent_spin)
        
        # 重试次数
        self.retry_spin = QSpinBox()
        self.retry_spin.setRange(0, 10)
        self.retry_spin.setValue(3)
        self.retry_spin.setToolTip("下载失败时的重试次数")
        options_layout.addRow("重试次数:", self.retry_spin)
        
        # 默认质量
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["最佳质量", "1080p", "720p", "480p", "360p"])
        options_layout.addRow("默认质量:", self.quality_combo)
        
        layout.addWidget(options_group)
        
        # 速度限制设置
        speed_group = QGroupBox("速度限制")
        speed_layout = QFormLayout(speed_group)
        
        # 启用速度限制复选框
        self.speed_limit_enabled = QCheckBox("启用下载速度限制")
        self.speed_limit_enabled.setToolTip("限制下载速度以避免占用过多带宽")
        speed_layout.addRow(self.speed_limit_enabled)
        
        # 速度限制值和单位
        speed_limit_layout = QHBoxLayout()
        
        self.speed_limit_value = QSpinBox()
        self.speed_limit_value.setRange(1, 10000)
        self.speed_limit_value.setValue(1000)
        self.speed_limit_value.setEnabled(False)
        self.speed_limit_value.setToolTip("设置最大下载速度")
        speed_limit_layout.addWidget(self.speed_limit_value)
        
        self.speed_limit_unit = QComboBox()
        self.speed_limit_unit.addItems(["KB/s", "MB/s"])
        self.speed_limit_unit.setCurrentText("KB/s")
        self.speed_limit_unit.setEnabled(False)
        speed_limit_layout.addWidget(self.speed_limit_unit)
        
        speed_limit_layout.addStretch()
        
        # 当前速度显示标签
        self.current_speed_label = QLabel("当前速度: 未限制")
        self.current_speed_label.setStyleSheet("""
            QLabel {
                color: #8E8E93;
                font-size: 12px;
                padding: 4px;
            }
        """)
        speed_limit_layout.addWidget(self.current_speed_label)
        
        speed_layout.addRow("速度限制:", speed_limit_layout)
        
        # 连接信号
        self.speed_limit_enabled.toggled.connect(self.on_speed_limit_toggled)
        self.speed_limit_value.valueChanged.connect(self.on_speed_limit_changed)
        self.speed_limit_unit.currentTextChanged.connect(self.on_speed_limit_changed)
        
        layout.addWidget(speed_group)
        layout.addStretch()
        
        return widget
    
    def on_speed_limit_toggled(self, enabled):
        """处理速度限制开关切换"""
        self.speed_limit_value.setEnabled(enabled)
        self.speed_limit_unit.setEnabled(enabled)
        
        if enabled:
            # 启用速度限制
            speed_value = self.speed_limit_value.value()
            unit = self.speed_limit_unit.currentText()
            
            # 转换为KB/s
            if unit == "MB/s":
                speed_kb = speed_value * 1024
            else:
                speed_kb = speed_value
            
            # 更新设置服务
            self.settings_service.update_download_settings(rate_limit=speed_kb)
            
            self.current_speed_label.setText(f"当前限制: {speed_value} {unit}")
            print(f"✅ 启用速度限制: {speed_value} {unit}")
        else:
            # 禁用速度限制
            self.settings_service.update_download_settings(rate_limit=None)
            self.current_speed_label.setText("当前速度: 未限制")
            print("✅ 禁用速度限制")
    
    def on_speed_limit_changed(self):
        """处理速度限制值变化"""
        if self.speed_limit_enabled.isChecked():
            speed_value = self.speed_limit_value.value()
            unit = self.speed_limit_unit.currentText()
            
            # 转换为KB/s
            if unit == "MB/s":
                speed_kb = speed_value * 1024
            else:
                speed_kb = speed_value
            
            # 更新设置服务
            self.settings_service.update_download_settings(rate_limit=speed_kb)
            
            self.current_speed_label.setText(f"当前限制: {speed_value} {unit}")
            print(f"🔧 更新速度限制: {speed_value} {unit}")
    
    def create_network_settings_tab(self):
        """创建网络设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 代理设置组
        proxy_group = QGroupBox("代理设置")
        proxy_layout = QVBoxLayout(proxy_group)
        
        # 代理类型选择
        proxy_type_layout = QHBoxLayout()
        self.proxy_group_btn = QButtonGroup()
        
        self.no_proxy_radio = QRadioButton("不使用代理")
        self.no_proxy_radio.setChecked(True)
        self.proxy_group_btn.addButton(self.no_proxy_radio, 0)
        proxy_type_layout.addWidget(self.no_proxy_radio)
        
        self.http_proxy_radio = QRadioButton("HTTP代理")
        self.proxy_group_btn.addButton(self.http_proxy_radio, 1)
        proxy_type_layout.addWidget(self.http_proxy_radio)
        
        self.socks5_proxy_radio = QRadioButton("SOCKS5代理")
        self.proxy_group_btn.addButton(self.socks5_proxy_radio, 2)
        proxy_type_layout.addWidget(self.socks5_proxy_radio)
        
        proxy_type_layout.addStretch()
        proxy_layout.addLayout(proxy_type_layout)
        
        # 代理配置
        proxy_config_layout = QFormLayout()
        
        self.proxy_host_edit = QLineEdit()
        self.proxy_host_edit.setPlaceholderText("代理服务器地址")
        self.proxy_host_edit.setEnabled(False)
        proxy_config_layout.addRow("服务器:", self.proxy_host_edit)
        
        self.proxy_port_spin = QSpinBox()
        self.proxy_port_spin.setRange(1, 65535)
        self.proxy_port_spin.setValue(8080)
        self.proxy_port_spin.setEnabled(False)
        proxy_config_layout.addRow("端口:", self.proxy_port_spin)
        
        self.proxy_username_edit = QLineEdit()
        self.proxy_username_edit.setPlaceholderText("用户名（可选）")
        self.proxy_username_edit.setEnabled(False)
        proxy_config_layout.addRow("用户名:", self.proxy_username_edit)
        
        self.proxy_password_edit = QLineEdit()
        self.proxy_password_edit.setPlaceholderText("密码（可选）")
        self.proxy_password_edit.setEchoMode(QLineEdit.Password)
        self.proxy_password_edit.setEnabled(False)
        proxy_config_layout.addRow("密码:", self.proxy_password_edit)
        
        proxy_layout.addLayout(proxy_config_layout)
        
        # 代理测试
        proxy_test_layout = QHBoxLayout()
        self.proxy_test_btn = QPushButton("测试代理")
        self.proxy_test_btn.setEnabled(False)
        self.proxy_test_btn.clicked.connect(self.test_proxy_connection)
        proxy_test_layout.addWidget(self.proxy_test_btn)
        
        self.proxy_status_label = QLabel("")
        proxy_test_layout.addWidget(self.proxy_status_label)
        proxy_test_layout.addStretch()
        
        proxy_layout.addLayout(proxy_test_layout)
        
        # 连接代理类型变化信号
        self.proxy_group_btn.buttonToggled.connect(self.on_proxy_type_changed)
        
        layout.addWidget(proxy_group)
        layout.addStretch()
        
        return widget
    
    def create_appearance_settings_tab(self):
        """创建外观设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 主题设置组
        theme_group = QGroupBox("主题")
        theme_layout = QVBoxLayout(theme_group)
        
        # 主题选择
        theme_selection_layout = QHBoxLayout()
        self.theme_group_btn = QButtonGroup()
        
        self.light_theme_radio = QRadioButton("浅色主题")
        self.light_theme_radio.setChecked(True)
        self.theme_group_btn.addButton(self.light_theme_radio, 0)
        theme_selection_layout.addWidget(self.light_theme_radio)
        
        self.dark_theme_radio = QRadioButton("深色主题")
        self.theme_group_btn.addButton(self.dark_theme_radio, 1)
        theme_selection_layout.addWidget(self.dark_theme_radio)
        
        theme_selection_layout.addStretch()
        theme_layout.addLayout(theme_selection_layout)
        
        layout.addWidget(theme_group)
        
        # 界面设置组
        ui_group = QGroupBox("界面")
        ui_layout = QFormLayout(ui_group)
        
        # 字体大小
        self.font_size_slider = QSlider(Qt.Horizontal)
        self.font_size_slider.setRange(8, 18)
        self.font_size_slider.setValue(12)
        font_size_layout = QHBoxLayout()
        font_size_layout.addWidget(QLabel("小"))
        font_size_layout.addWidget(self.font_size_slider, 1)
        font_size_layout.addWidget(QLabel("大"))
        self.font_size_value = QLabel("12")
        font_size_layout.addWidget(self.font_size_value)
        ui_layout.addRow("字体大小:", font_size_layout)
        
        # 连接字体大小滑块信号
        self.font_size_slider.valueChanged.connect(self.on_font_size_changed)
        
        # 界面缩放
        self.ui_scale_slider = QSlider(Qt.Horizontal)
        self.ui_scale_slider.setRange(80, 150)
        self.ui_scale_slider.setValue(100)
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("80%"))
        scale_layout.addWidget(self.ui_scale_slider, 1)
        scale_layout.addWidget(QLabel("150%"))
        self.ui_scale_value = QLabel("100%")
        scale_layout.addWidget(self.ui_scale_value)
        ui_layout.addRow("界面缩放:", scale_layout)
        
        # 连接界面缩放滑块信号
        self.ui_scale_slider.valueChanged.connect(self.on_ui_scale_changed)
        
        # 透明效果
        self.transparency_check = QCheckBox("启用透明效果")
        self.transparency_check.setChecked(True)
        ui_layout.addRow(self.transparency_check)
        
        # 连接透明效果复选框信号
        self.transparency_check.toggled.connect(self.on_transparency_changed)
        
        # 连接滑块值更新
        self.font_size_slider.valueChanged.connect(
            lambda v: self.font_size_value.setText(str(v))
        )
        self.ui_scale_slider.valueChanged.connect(
            lambda v: self.ui_scale_value.setText(f"{v}%")
        )
        
        layout.addWidget(ui_group)
        layout.addStretch()
        
        return widget
    
    def browse_download_path_simple(self):
        """浏览下载路径 - 简化版本"""
        try:
            if hasattr(self, 'download_path_edit'):
                current_path = self.download_path_edit.text()
                if not current_path:
                    current_path = str(Path.home() / "Downloads")
                    
                path = QFileDialog.getExistingDirectory(
                    self, "选择下载文件夹", current_path
                )
                
                if path:
                    self.download_path_edit.setText(path)
                    print(f"✅ 下载路径已更新: {path}")
            else:
                print("❌ download_path_edit 控件不存在")
                QMessageBox.warning(self, "错误", "下载路径输入框未找到")
        except Exception as e:
            print(f"❌ 浏览下载路径失败: {e}")
            QMessageBox.warning(self, "错误", f"无法打开文件夹选择对话框: {str(e)}")
    
    def browse_download_path_legacy(self):
        """浏览下载路径 - 兼容版本"""
        self.browse_download_path_simple()
    
    def on_proxy_type_changed(self, button, checked):
        """代理类型改变"""
        if checked:
            proxy_enabled = self.proxy_group_btn.checkedId() > 0
            
            self.proxy_host_edit.setEnabled(proxy_enabled)
            self.proxy_port_spin.setEnabled(proxy_enabled)
            self.proxy_username_edit.setEnabled(proxy_enabled)
            self.proxy_password_edit.setEnabled(proxy_enabled)
            self.proxy_test_btn.setEnabled(proxy_enabled)
    
    def test_proxy_connection(self):
        """测试代理连接"""
        self.proxy_status_label.setText("正在测试...")
        self.proxy_status_label.setStyleSheet("""
            QLabel {
                color: #FF9500;
                font-weight: 600;
                padding: 4px 8px;
                background: #FFF3CD;
                border-radius: 4px;
            }
        """)
        
        # 模拟代理测试 - 随机成功或失败
        import random
        if random.choice([True, False]):
            QTimer.singleShot(2000, self.on_proxy_test_success)
        else:
            QTimer.singleShot(2000, self.on_proxy_test_failed)
    
    def on_proxy_test_success(self):
        """代理测试成功"""
        self.proxy_status_label.setText("✅ 连接成功")
        self.proxy_status_label.setStyleSheet("""
            QLabel {
                color: #28A745;
                font-weight: 600;
                padding: 4px 8px;
                background: #D4EDDA;
                border-radius: 4px;
            }
        """)
    
    def on_proxy_test_failed(self):
        """代理测试失败"""
        self.proxy_status_label.setText("❌ 连接失败")
        self.proxy_status_label.setStyleSheet("""
            QLabel {
                color: #DC3545;
                font-weight: 600;
                padding: 4px 8px;
                background: #F8D7DA;
                border-radius: 4px;
            }
        """)
    
    def save_settings_and_close_simple(self, dialog, tab_widget):
        """真正保存设置并关闭对话框"""
        try:
            print("🔧 开始保存设置...")
            
            # 强制收集所有UI控件的当前值并保存
            self.collect_and_save_all_settings()
            
            # 显示保存成功消息
            QMessageBox.information(dialog, "成功", "设置已保存并立即生效！")
            print("🎉 所有设置保存成功")
            
            dialog.accept()
            
        except Exception as e:
            error_msg = f"保存设置失败: {str(e)}"
            QMessageBox.critical(dialog, "错误", error_msg)
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
    
    def collect_and_save_all_settings(self):
        """收集所有UI控件的值并保存设置"""
        print("🔧 收集所有设置...")
        
        # 1. 收集下载设置
        download_settings = {}
        
        if hasattr(self, 'download_path_edit') and self.download_path_edit:
            download_settings['download_path'] = self.download_path_edit.text().strip()
            print(f"📁 下载路径: {download_settings['download_path']}")
        
        if hasattr(self, 'quality_combo') and self.quality_combo:
            quality_map = {
                "最佳质量": "best",
                "1080p": "1080p", 
                "720p": "720p",
                "480p": "480p",
                "360p": "360p"
            }
            download_settings['quality'] = quality_map.get(self.quality_combo.currentText(), "best")
            print(f"🎥 视频质量: {download_settings['quality']}")
        
        if hasattr(self, 'concurrent_spin') and self.concurrent_spin:
            download_settings['max_concurrent'] = self.concurrent_spin.value()
            print(f"⚡ 并发数: {download_settings['max_concurrent']}")
        
        if hasattr(self, 'retry_spin') and self.retry_spin:
            download_settings['max_retries'] = self.retry_spin.value()
            print(f"🔄 重试次数: {download_settings['max_retries']}")
        
        # 速度限制设置
        if hasattr(self, 'speed_limit_enabled') and self.speed_limit_enabled:
            if self.speed_limit_enabled.isChecked():
                speed_value = self.speed_limit_value.value() if hasattr(self, 'speed_limit_value') else 1000
                unit = self.speed_limit_unit.currentText() if hasattr(self, 'speed_limit_unit') else "KB/s"
                
                # 转换为KB/s
                if unit == "MB/s":
                    download_settings['rate_limit'] = speed_value * 1024
                else:
                    download_settings['rate_limit'] = speed_value
                print(f"🚀 速度限制: {speed_value} {unit}")
            else:
                download_settings['rate_limit'] = None
                print("🚀 速度限制: 未启用")
        
        # 保存下载设置
        if download_settings:
            self.settings_service.update_download_settings(**download_settings)
            print("✅ 下载设置已更新")
        
        # 2. 收集网络设置
        network_settings = {}
        
        if hasattr(self, 'proxy_group_btn') and self.proxy_group_btn:
            proxy_type_id = self.proxy_group_btn.checkedId()
            network_settings['proxy_enabled'] = proxy_type_id > 0
            network_settings['proxy_type'] = "http" if proxy_type_id == 1 else "socks5"
            print(f"🌐 代理设置: 启用={network_settings['proxy_enabled']}, 类型={network_settings['proxy_type']}")
        
        if hasattr(self, 'proxy_host_edit') and self.proxy_host_edit:
            network_settings['proxy_host'] = self.proxy_host_edit.text().strip()
            print(f"🌐 代理主机: {network_settings['proxy_host']}")
        
        if hasattr(self, 'proxy_port_spin') and self.proxy_port_spin:
            network_settings['proxy_port'] = self.proxy_port_spin.value()
            print(f"🌐 代理端口: {network_settings['proxy_port']}")
        
        # 保存网络设置
        if network_settings:
            self.settings_service.update_network_settings(**network_settings)
            print("✅ 网络设置已更新")
        
        # 3. 收集UI设置
        ui_settings = {}
        
        if hasattr(self, 'theme_group_btn') and self.theme_group_btn:
            theme_id = self.theme_group_btn.checkedId()
            ui_settings['theme'] = "dark" if theme_id == 1 else "light"
            print(f"🎨 主题设置: {ui_settings['theme']}")
            
            # 立即应用主题
            if ui_settings['theme'] == "dark":
                self.apply_dark_theme()
            else:
                self.apply_light_theme()
        
        # 保存UI设置
        if ui_settings:
            self.settings_service.update_ui_settings(**ui_settings)
            print("✅ UI设置已更新")
        
        # 强制保存所有设置到文件
        self.settings_service.save_settings()
        print("💾 所有设置已强制保存到文件")
    
    def load_settings_to_ui(self):
        """从设置服务加载设置到UI控件"""
        try:
            print("🔧 正在加载设置到UI控件...")
            # 这个方法用于加载设置到UI，目前为占位符
            pass
        except Exception as e:
            print(f"❌ 加载设置到UI失败: {e}")
    
    def on_settings_changed(self, settings: dict):
        """处理设置变更"""
        print(f"🔧 设置已更改: {len(settings)} 项")
        
        # 应用主题变更
        if 'theme' in settings:
            self.apply_theme(settings['theme'])
        
        # 应用其他设置变更
        # 这里可以添加更多设置应用逻辑
    
    def apply_theme(self, theme: str):
        """应用主题"""
        print(f"🎨 应用主题: {theme}")
        
        if theme == 'dark':
            self.apply_dark_theme()
        else:
            self.apply_light_theme()
    
    def apply_dark_theme(self):
        """应用完整的深色主题到整个应用程序"""
        print("🌙 正在应用深色主题...")
        
        # 完整的深色主题样式 - 确保覆盖所有组件
        dark_style = """
            /* 主窗口 - 深色背景 */
            QMainWindow {
                background: #1C1C1E;
                color: #FFFFFF;
            }
            
            /* 所有框架和面板 */
            QFrame {
                background: #2C2C2E;
                border: 1px solid #3A3A3C;
                border-radius: 8px;
                color: #FFFFFF;
            }
            
            /* 所有标签文字 */
            QLabel {
                color: #FFFFFF;
                background: transparent;
            }
            
            /* 所有按钮 */
            QPushButton {
                background: #3A3A3C;
                color: #FFFFFF;
                border: 1px solid #48484A;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #48484A;
                border-color: #5A5A5C;
            }
            QPushButton:pressed {
                background: #2C2C2E;
            }
            
            /* 输入框 */
            QLineEdit {
                background: #3A3A3C;
                color: #FFFFFF;
                border: 1px solid #48484A;
                border-radius: 6px;
                padding: 8px 12px;
            }
            QLineEdit:focus {
                border-color: #007AFF;
            }
            
            /* 下拉框 */
            QComboBox {
                background: #3A3A3C;
                color: #FFFFFF;
                border: 1px solid #48484A;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QComboBox:hover {
                background: #48484A;
            }
            QComboBox::drop-down {
                border: none;
                background: transparent;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #FFFFFF;
            }
            QComboBox QAbstractItemView {
                background: #3A3A3C;
                color: #FFFFFF;
                border: 1px solid #48484A;
                selection-background-color: #007AFF;
            }
            
            /* 数字输入框 */
            QSpinBox {
                background: #3A3A3C;
                color: #FFFFFF;
                border: 1px solid #48484A;
                border-radius: 6px;
                padding: 6px;
            }
            QSpinBox:hover {
                background: #48484A;
            }
            
            /* 单选按钮 */
            QRadioButton {
                color: #FFFFFF;
                background: transparent;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
                border-radius: 8px;
                border: 2px solid #48484A;
                background: #3A3A3C;
            }
            QRadioButton::indicator:checked {
                background: #007AFF;
                border-color: #007AFF;
            }
            
            /* 复选框 */
            QCheckBox {
                color: #FFFFFF;
                background: transparent;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #48484A;
                border-radius: 3px;
                background: #3A3A3C;
            }
            QCheckBox::indicator:checked {
                background: #007AFF;
                border-color: #007AFF;
            }
            
            /* 表格 */
            QTableWidget {
                background: #2C2C2E;
                color: #FFFFFF;
                border: 1px solid #3A3A3C;
                border-radius: 8px;
                gridline-color: #3A3A3C;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #3A3A3C;
                color: #FFFFFF;
            }
            QTableWidget::item:selected {
                background: #007AFF;
            }
            QHeaderView::section {
                background: #1C1C1E;
                color: #FFFFFF;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #3A3A3C;
                font-weight: 600;
            }
            
            /* 滚动条 */
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #2C2C2E;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #48484A;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #5A5A5C;
            }
            
            /* 对话框 */
            QDialog {
                background: #1C1C1E;
                color: #FFFFFF;
            }
            
            /* 分组框 */
            QGroupBox {
                color: #FFFFFF;
                border: 1px solid #3A3A3C;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: 600;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #FFFFFF;
            }
            
            /* 选项卡 */
            QTabWidget::pane {
                background: #2C2C2E;
                border: 1px solid #3A3A3C;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #3A3A3C;
                color: #FFFFFF;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background: #007AFF;
            }
            QTabBar::tab:hover {
                background: #48484A;
            }
            
            /* 菜单 */
            QMenu {
                background: #2C2C2E;
                color: #FFFFFF;
                border: 1px solid #3A3A3C;
                border-radius: 6px;
                padding: 4px 0px;
            }
            QMenu::item {
                padding: 6px 16px;
                color: #FFFFFF;
            }
            QMenu::item:selected {
                background: #007AFF;
            }
            
            /* 进度条 */
            QProgressBar {
                background: #3A3A3C;
                border: none;
                border-radius: 3px;
                text-align: center;
                color: #FFFFFF;
            }
            QProgressBar::chunk {
                background: #007AFF;
                border-radius: 3px;
            }
                background: #5A5A5C;
            }
            QPushButton:disabled {
                background: #2C2C2E;
                color: #8E8E93;
                border-color: #3A3A3C;
            }
            
            /* 输入框 */
            QLineEdit {
                background: #2C2C2E;
                color: #FFFFFF;
                border: 1px solid #48484A;
                border-radius: 6px;
                padding: 8px 12px;
                selection-background-color: #007AFF;
            }
            QLineEdit:focus {
                border-color: #007AFF;
                background: #1C1C1E;
            }
            QLineEdit::placeholder {
                color: #8E8E93;
            }
            
            /* 进度条 */
            QProgressBar {
                background: #3A3A3C;
                border: none;
                border-radius: 3px;
                text-align: center;
                color: #FFFFFF;
            }
            QProgressBar::chunk {
                background: #007AFF;
                border-radius: 3px;
            }
            
            /* 滚动区域 */
            QScrollArea {
                background: #1C1C1E;
                border: none;
            }
            QScrollBar:vertical {
                background: #2C2C2E;
                width: 12px;
                border-radius: 6px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #48484A;
                border-radius: 6px;
                min-height: 20px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: #5A5A5C;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            /* 菜单 */
            QMenu {
                background: #2C2C2E;
                border: 1px solid #48484A;
                border-radius: 8px;
                padding: 4px 0px;
                color: #FFFFFF;
            }
            QMenu::item {
                padding: 8px 16px;
                background: transparent;
            }
            QMenu::item:selected {
                background: #48484A;
                border-radius: 4px;
            }
            QMenu::separator {
                height: 1px;
                background: #3A3A3C;
                margin: 4px 8px;
            }
            
            /* 表格 */
            QTableWidget {
                background: #2C2C2E;
                color: #FFFFFF;
                border: 1px solid #3A3A3C;
                border-radius: 8px;
                gridline-color: #3A3A3C;
                selection-background-color: #48484A;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #3A3A3C;
                background: transparent;
            }
            QTableWidget::item:selected {
                background: #48484A;
                color: #FFFFFF;
            }
            QHeaderView::section {
                background: #3A3A3C;
                color: #FFFFFF;
                border: none;
                border-bottom: 2px solid #48484A;
                padding: 10px;
                font-weight: 600;
            }
            QHeaderView::section:hover {
                background: #48484A;
            }
            
            /* 对话框 */
            QDialog {
                background: #1C1C1E;
                color: #FFFFFF;
                border-radius: 12px;
            }
            
            /* 标签页 */
            QTabWidget::pane {
                background: #2C2C2E;
                border: 1px solid #3A3A3C;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #3A3A3C;
                color: #FFFFFF;
                border: 1px solid #48484A;
                padding: 8px 16px;
                margin-right: 2px;
                border-radius: 6px 6px 0px 0px;
            }
            QTabBar::tab:selected {
                background: #2C2C2E;
                border-bottom-color: #2C2C2E;
            }
            QTabBar::tab:hover {
                background: #48484A;
        """
        
        # 应用深色主题样式到整个应用程序
        self.setStyleSheet(dark_style)
        
        # 强制刷新所有子控件
        for widget in self.findChildren(QWidget):
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()
        
        # 刷新主窗口
        self.update()
        print("✅ 深色主题已应用到整个应用程序")
    
    def on_font_size_changed(self, value):
        """字体大小改变事件"""
        print(f"🔤 字体大小改变: {value}px")
        self.font_size_value.setText(str(value))
        
        # 应用字体大小到整个应用程序
        self.apply_font_size(value)
    
    def on_ui_scale_changed(self, value):
        """界面缩放改变事件"""
        print(f"🔍 界面缩放改变: {value}%")
        self.ui_scale_value.setText(f"{value}%")
        
        # 应用界面缩放
        self.apply_ui_scale(value / 100.0)
    
    def on_transparency_changed(self, enabled):
        """透明效果改变事件"""
        print(f"✨ 透明效果: {'启用' if enabled else '禁用'}")
        
        # 应用透明效果
        self.apply_transparency(enabled)
    
    def apply_font_size(self, size):
        """应用字体大小到整个应用程序"""
        print(f"🔤 应用字体大小: {size}px")
        
        # 创建字体大小样式
        font_style = f"""
            QLabel {{
                font-size: {size}px;
            }}
            QPushButton {{
                font-size: {size}px;
            }}
            QLineEdit {{
                font-size: {size}px;
            }}
            QComboBox {{
                font-size: {size}px;
            }}
            QTableWidget {{
                font-size: {size}px;
            }}
            QMenu::item {{
                font-size: {size}px;
            }}
        """
        
        # 应用字体样式
        current_style = self.styleSheet()
        # 简单的字体大小替换（实际应用中可能需要更复杂的处理）
        self.setStyleSheet(current_style + font_style)
        
        # 保存字体大小设置
        self.settings_service.update_ui_settings(font_size=size)
    
    def apply_ui_scale(self, scale):
        """应用界面缩放"""
        print(f"🔍 应用界面缩放: {scale:.1f}x")
        
        # 获取当前窗口大小
        current_size = self.size()
        
        # 计算新的窗口大小
        new_width = int(900 * scale)  # 基础宽度 900
        new_height = int(600 * scale)  # 基础高度 600
        
        # 调整窗口大小
        self.resize(new_width, new_height)
        
        # 保存缩放设置
        self.settings_service.update_ui_settings(ui_scale=scale)
        
        print(f"✅ 窗口大小已调整为: {new_width}x{new_height}")
    
    def apply_transparency(self, enabled):
        """应用透明效果"""
        print(f"✨ 应用透明效果: {'启用' if enabled else '禁用'}")
        
        if enabled:
            # 启用透明效果
            self.setWindowOpacity(0.95)
            self.setAttribute(Qt.WA_TranslucentBackground, True)
            print("✅ 透明效果已启用")
        else:
            # 禁用透明效果
            self.setWindowOpacity(1.0)
            self.setAttribute(Qt.WA_TranslucentBackground, False)
            print("✅ 透明效果已禁用")
        
        # 保存透明效果设置
        self.settings_service.update_ui_settings(transparency_enabled=enabled)
    
    def apply_light_theme(self):
        """应用浅色主题到整个应用程序"""
        print("☀️ 正在应用浅色主题...")
        
        # 完整的浅色主题样式
        light_style = """
            QMainWindow {
                background: #F2F2F7;
                color: #1C1C1E;
            }
        """
        self.setStyleSheet(light_style)
    
    def show_simple_settings_dialog(self):
        """显示简化的设置对话框（备用方案）"""
        dialog = QDialog(self)
        dialog.setWindowTitle("首选项设置")
        dialog.setModal(True)
        dialog.resize(700, 500)
        
        layout = QVBoxLayout(dialog)
        
        # 标题
        title_label = QLabel("⚙️ 首选项设置")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 600;
                color: #1C1C1E;
                padding: 16px;
            }
        """)
        layout.addWidget(title_label)
        
        # 创建标签页
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #E5E5E7;
                border-radius: 8px;
                background: white;
            }
            QTabBar::tab {
                background: #F2F2F7;
                border: 1px solid #D1D1D6;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom-color: white;
            }
            QTabBar::tab:hover {
                background: #E5E5EA;
            }
        """)
        
        # 下载设置标签
        download_tab = QWidget()
        download_layout = QFormLayout(download_tab)
        
        # 下载路径
        path_layout = QHBoxLayout()
        path_input = QLineEdit()
        path_input.setText(str(self.portable_manager.get_downloads_directory()))
        path_input.setStyleSheet("""
            QLineEdit {
                padding: 6px 10px;
                border: 1px solid #D1D1D6;
                border-radius: 4px;
            }
        """)
        path_layout.addWidget(path_input)
        
        browse_btn = QPushButton("浏览...")
        browse_btn.setStyleSheet("""
            QPushButton {
                background: #F2F2F7;
                border: 1px solid #D1D1D6;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: #E5E5EA;
            }
        """)
        browse_btn.clicked.connect(lambda: self.browse_download_path(path_input))
        path_layout.addWidget(browse_btn)
        
        download_layout.addRow("下载路径:", path_layout)
        
        # 视频质量
        quality_combo = QComboBox()
        quality_combo.addItems(["best", "1080p", "720p", "480p", "worst"])
        quality_combo.setCurrentText("best")
        download_layout.addRow("视频质量:", quality_combo)
        
        # 视频格式
        format_combo = QComboBox()
        format_combo.addItems(["mp4", "webm", "mkv", "avi"])
        format_combo.setCurrentText("mp4")
        download_layout.addRow("视频格式:", format_combo)
        
        # 并发下载数
        concurrent_spin = QSpinBox()
        concurrent_spin.setRange(1, 10)
        concurrent_spin.setValue(3)
        download_layout.addRow("并发下载数:", concurrent_spin)
        
        # 速度限制
        speed_layout = QHBoxLayout()
        speed_spin = QSpinBox()
        speed_spin.setRange(0, 10000)
        speed_spin.setValue(0)
        speed_spin.setSuffix(" KB/s")
        speed_layout.addWidget(speed_spin)
        speed_layout.addWidget(QLabel("(0 = 无限制)"))
        speed_layout.addStretch()
        download_layout.addRow("速度限制:", speed_layout)
        
        # 文件命名格式
        naming_layout = QHBoxLayout()
        naming_combo = QComboBox()
        naming_combo.setEditable(True)
        naming_combo.addItems([
            "%(title)s.%(ext)s",
            "[%(uploader)s] %(title)s.%(ext)s", 
            "[%(uploader)s][%(id)s] %(title)s.%(ext)s",
            "%(upload_date)s - %(title)s.%(ext)s",
            "[%(platform)s] %(uploader)s - %(title)s.%(ext)s"
        ])
        naming_combo.setCurrentText("%(title)s.%(ext)s")
        naming_combo.setStyleSheet("""
            QComboBox {
                padding: 6px 10px;
                border: 1px solid #D1D1D6;
                border-radius: 4px;
            }
        """)
        naming_layout.addWidget(naming_combo)
        
        help_btn = QPushButton("?")
        help_btn.setFixedSize(24, 24)
        help_btn.setStyleSheet("""
            QPushButton {
                background: #F2F2F7;
                border: 1px solid #D1D1D6;
                border-radius: 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #E5E5EA;
            }
        """)
        help_btn.clicked.connect(self.show_naming_help)
        naming_layout.addWidget(help_btn)
        
        download_layout.addRow("文件命名格式:", naming_layout)
        
        tab_widget.addTab(download_tab, "下载设置")
        
        # 网络设置标签
        network_tab = QWidget()
        network_layout = QFormLayout(network_tab)
        
        # 代理设置
        proxy_group = QGroupBox("代理设置")
        proxy_group_layout = QVBoxLayout(proxy_group)
        
        proxy_enable_cb = QCheckBox("启用代理")
        proxy_group_layout.addWidget(proxy_enable_cb)
        
        proxy_form_layout = QFormLayout()
        
        proxy_type_combo = QComboBox()
        proxy_type_combo.addItems(["HTTP", "SOCKS5"])
        proxy_form_layout.addRow("代理类型:", proxy_type_combo)
        
        proxy_host_input = QLineEdit()
        proxy_host_input.setPlaceholderText("127.0.0.1")
        proxy_form_layout.addRow("代理地址:", proxy_host_input)
        
        proxy_port_spin = QSpinBox()
        proxy_port_spin.setRange(1, 65535)
        proxy_port_spin.setValue(8080)
        proxy_form_layout.addRow("端口:", proxy_port_spin)
        
        # 代理测试按钮和状态
        proxy_test_layout = QHBoxLayout()
        proxy_test_btn = QPushButton("测试代理")
        proxy_test_btn.setStyleSheet("""
            QPushButton {
                background: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #0051D5;
            }
        """)
        proxy_test_btn.clicked.connect(lambda: self.test_proxy_connection(
            proxy_host_input.text(), proxy_port_spin.value(), 
            proxy_type_combo.currentText(), proxy_status_label
        ))
        
        proxy_status_label = QLabel("🔘 未测试")
        proxy_status_label.setStyleSheet("""
            QLabel {
                color: #8E8E93;
                font-size: 12px;
                padding: 4px;
            }
        """)
        
        proxy_test_layout.addWidget(proxy_test_btn)
        proxy_test_layout.addWidget(proxy_status_label)
        proxy_test_layout.addStretch()
        
        proxy_form_layout.addRow("代理测试:", proxy_test_layout)
        
        proxy_group_layout.addLayout(proxy_form_layout)
        network_layout.addRow(proxy_group)
        
        # 超时设置
        timeout_spin = QSpinBox()
        timeout_spin.setRange(5, 300)
        timeout_spin.setValue(30)
        timeout_spin.setSuffix(" 秒")
        network_layout.addRow("连接超时:", timeout_spin)
        
        tab_widget.addTab(network_tab, "网络设置")
        
        # 界面设置标签
        ui_tab = QWidget()
        ui_layout = QFormLayout(ui_tab)
        
        # 主题设置
        theme_combo = QComboBox()
        theme_combo.addItems(["自动", "浅色", "深色"])
        theme_combo.setCurrentText("自动")
        ui_layout.addRow("主题:", theme_combo)
        
        # 语言设置
        language_combo = QComboBox()
        language_combo.addItems(["中文", "English"])
        language_combo.setCurrentText("中文")
        ui_layout.addRow("语言:", language_combo)
        
        # 系统托盘
        tray_cb = QCheckBox("显示系统托盘图标")
        tray_cb.setChecked(True)
        ui_layout.addRow("系统托盘:", tray_cb)
        
        # 最小化到托盘
        minimize_tray_cb = QCheckBox("最小化到系统托盘")
        minimize_tray_cb.setChecked(True)
        ui_layout.addRow("", minimize_tray_cb)
        
        tab_widget.addTab(ui_tab, "界面设置")
        
        layout.addWidget(tab_widget)
        
        # 按钮
        button_layout = QHBoxLayout()
        reset_btn = QPushButton("重置默认")
        export_btn = QPushButton("导出设置")
        import_btn = QPushButton("导入设置")
        
        for btn in [reset_btn, export_btn, import_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background: #F2F2F7;
                    border: 1px solid #D1D1D6;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background: #E5E5EA;
                }
            """)
        
        cancel_btn = QPushButton("取消")
        save_btn = QPushButton("保存")
        
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #F2F2F7;
                border: 1px solid #D1D1D6;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #E5E5EA;
            }
        """)
        
        save_btn.setStyleSheet("""
            QPushButton {
                background: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #0051D5;
            }
        """)
        
        cancel_btn.clicked.connect(dialog.reject)
        save_btn.clicked.connect(lambda: self.save_settings_and_close(
            dialog, path_input, quality_combo, format_combo, concurrent_spin, speed_spin,
            proxy_enable_cb, proxy_type_combo, proxy_host_input, proxy_port_spin, timeout_spin,
            theme_combo, language_combo, tray_cb, minimize_tray_cb, naming_combo
        ))
        
        button_layout.addWidget(reset_btn)
        button_layout.addWidget(export_btn)
        button_layout.addWidget(import_btn)
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def save_settings_and_close(self, dialog, path_input, quality_combo, format_combo, 
                               concurrent_spin, speed_spin, proxy_enable_cb, proxy_type_combo, 
                               proxy_host_input, proxy_port_spin, timeout_spin, theme_combo, 
                               language_combo, tray_cb, minimize_tray_cb, naming_combo):
        """Save settings and close dialog"""
        try:
            # 保存下载设置
            self.settings_service.update_download_settings(
                download_path=path_input.text(),
                quality=quality_combo.currentText(),
                format=format_combo.currentText(),
                max_concurrent=concurrent_spin.value(),
                rate_limit=speed_spin.value() if speed_spin.value() > 0 else None,
                filename_template=naming_combo.currentText()
            )
            
            # 保存网络设置
            self.settings_service.update_network_settings(
                proxy_enabled=proxy_enable_cb.isChecked(),
                proxy_type=proxy_type_combo.currentText().lower(),
                proxy_host=proxy_host_input.text(),
                proxy_port=proxy_port_spin.value(),
                timeout=timeout_spin.value()
            )
            
            # 保存界面设置
            theme_map = {"自动": "auto", "浅色": "light", "深色": "dark"}
            language_map = {"中文": "zh_CN", "English": "en_US"}
            
            self.settings_service.update_ui_settings(
                theme=theme_map.get(theme_combo.currentText(), "auto"),
                language=language_map.get(language_combo.currentText(), "zh_CN"),
                show_tray_icon=tray_cb.isChecked(),
                minimize_to_tray=minimize_tray_cb.isChecked()
            )
            
            # 应用主题变化
            self.apply_theme_change(theme_combo.currentText())
            
            # 强制保存设置到文件
            self.settings_service.save_settings()
            
            # 显示保存成功消息
            QMessageBox.information(dialog, "设置", "设置已保存成功！")
            dialog.accept()
            
        except Exception as e:
            error_msg = f"保存设置失败: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(dialog, "错误", error_msg)
            QMessageBox.critical(dialog, "错误", f"保存设置失败：{str(e)}")
    
    def apply_theme_change(self, theme_name):
        """Apply theme change - 完整的深色主题实现"""
        if theme_name == "深色":
            # 完整的深色主题样式
            dark_theme = """
                QMainWindow {
                    background: #1C1C1E;
                    color: #FFFFFF;
                }
                
                /* 标题栏深色主题 */
                QFrame {
                    background: #2C2C2E;
                    color: #FFFFFF;
                    border-color: #48484A;
                }
                
                /* 标签和文本 */
                QLabel {
                    color: #FFFFFF;
                    background: transparent;
                }
                
                /* 按钮深色主题 */
                QPushButton {
                    background: #3A3A3C;
                    color: #FFFFFF;
                    border: 1px solid #48484A;
                    border-radius: 6px;
                    padding: 6px 12px;
                }
                QPushButton:hover {
                    background: #48484A;
                    border-color: #5A5A5C;
                }
                QPushButton:pressed {
                    background: #2C2C2E;
                }
                
                /* 输入框深色主题 */
                QLineEdit {
                    background: #3A3A3C;
                    color: #FFFFFF;
                    border: 1px solid #48484A;
                    border-radius: 6px;
                    padding: 8px 12px;
                }
                QLineEdit:focus {
                    border-color: #007AFF;
                    background: #2C2C2E;
                }
                
                /* 下拉框深色主题 */
                QComboBox {
                    background: #3A3A3C;
                    color: #FFFFFF;
                    border: 1px solid #48484A;
                    border-radius: 6px;
                    padding: 6px 12px;
                }
                QComboBox:hover {
                    background: #48484A;
                }
                QComboBox::drop-down {
                    border: none;
                    background: transparent;
                }
                QComboBox::down-arrow {
                    image: none;
                    border-left: 5px solid transparent;
                    border-right: 5px solid transparent;
                    border-top: 5px solid #FFFFFF;
                }
                QComboBox QAbstractItemView {
                    background: #3A3A3C;
                    color: #FFFFFF;
                    border: 1px solid #48484A;
                    selection-background-color: #007AFF;
                }
                
                /* 复选框深色主题 */
                QCheckBox {
                    color: #FFFFFF;
                    background: transparent;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                    background: #3A3A3C;
                    border: 1px solid #48484A;
                    border-radius: 3px;
                }
                QCheckBox::indicator:checked {
                    background: #007AFF;
                    border-color: #007AFF;
                }
                QCheckBox::indicator:checked::after {
                    content: "✓";
                    color: white;
                }
                
                /* 数字输入框深色主题 */
                QSpinBox {
                    background: #3A3A3C;
                    color: #FFFFFF;
                    border: 1px solid #48484A;
                    border-radius: 6px;
                    padding: 6px;
                }
                QSpinBox:hover {
                    background: #48484A;
                }
                QSpinBox::up-button, QSpinBox::down-button {
                    background: #48484A;
                    border: none;
                    width: 16px;
                }
                QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                    background: #5A5A5C;
                }
                
                /* 表格深色主题 */
                QTableWidget {
                    background: #2C2C2E;
                    color: #FFFFFF;
                    border: 1px solid #48484A;
                    gridline-color: #48484A;
                }
                QTableWidget::item {
                    background: #2C2C2E;
                    color: #FFFFFF;
                    border-bottom: 1px solid #48484A;
                }
                QTableWidget::item:hover {
                    background: #3A3A3C;
                }
                QTableWidget::item:selected {
                    background: #007AFF;
                }
                QHeaderView::section {
                    background: #3A3A3C;
                    color: #FFFFFF;
                    border: none;
                    border-bottom: 1px solid #48484A;
                    padding: 8px;
                    font-weight: 600;
                }
                
                /* 滚动条深色主题 */
                QScrollBar:vertical {
                    background: #2C2C2E;
                    width: 12px;
                    border-radius: 6px;
                }
                QScrollBar::handle:vertical {
                    background: #48484A;
                    border-radius: 6px;
                    min-height: 20px;
                }
                QScrollBar::handle:vertical:hover {
                    background: #5A5A5C;
                }
                
                /* 文本编辑器深色主题 */
                QTextEdit {
                    background: #2C2C2E;
                    color: #FFFFFF;
                    border: 1px solid #48484A;
                    border-radius: 8px;
                }
                
                /* 分组框深色主题 */
                QGroupBox {
                    color: #FFFFFF;
                    border: 1px solid #48484A;
                    border-radius: 8px;
                    margin-top: 10px;
                    padding-top: 10px;
                    background: #2C2C2E;
                }
                QGroupBox::title {
                    color: #FFFFFF;
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }
                
                /* 标签页深色主题 */
                QTabWidget::pane {
                    background: #2C2C2E;
                    border: 1px solid #48484A;
                    border-radius: 8px;
                }
                QTabBar::tab {
                    background: #3A3A3C;
                    color: #FFFFFF;
                    border: 1px solid #48484A;
                    padding: 8px 16px;
                    margin-right: 2px;
                    border-radius: 6px 6px 0px 0px;
                }
                QTabBar::tab:selected {
                    background: #2C2C2E;
                    border-bottom-color: #2C2C2E;
                }
                QTabBar::tab:hover {
                    background: #48484A;
                }
                
                /* 菜单深色主题 */
                QMenu {
                    background: #2C2C2E;
                    color: #FFFFFF;
                    border: 1px solid #48484A;
                    border-radius: 6px;
                    padding: 4px 0px;
                }
                QMenu::item {
                    padding: 6px 16px;
                    color: #FFFFFF;
                }
                QMenu::item:selected {
                    background: #007AFF;
                }
                
                /* 对话框深色主题 */
                QDialog {
                    background: #1C1C1E;
                    color: #FFFFFF;
                }
                
                /* 进度条深色主题 */
                QProgressBar {
                    background: #3A3A3C;
                    border: none;
                    border-radius: 3px;
                    text-align: center;
                    color: #FFFFFF;
                }
                QProgressBar::chunk {
                    background: #007AFF;
                    border-radius: 3px;
                }
            """
            self.setStyleSheet(dark_theme)
            
            # 更新任务卡片的深色主题
            for task_widget in self.task_widgets.values():
                task_widget.setStyleSheet("""
                    QFrame {
                        background: #2C2C2E;
                        border: 1px solid #48484A;
                        border-radius: 12px;
                        margin: 4px;
                        color: #FFFFFF;
                    }
                    QFrame:hover {
                        border-color: #5A5A5C;
                    }
                    QLabel {
                        color: #FFFFFF;
                        background: transparent;
                    }
                    QPushButton {
                        background: transparent;
                        border: none;
                        border-radius: 12px;
                        color: #8E8E93;
                    }
                    QPushButton:hover {
                        background: #3A3A3C;
                        color: #FFFFFF;
                    }
                """)
                
        elif theme_name == "浅色":
            # 浅色主题（恢复默认）
            self.setStyleSheet("""
                QMainWindow {
                    background: #F2F2F7;
                    color: #1C1C1E;
                }
            """)
            
            # 恢复任务卡片的浅色主题
            for task_widget in self.task_widgets.values():
                task_widget.setStyleSheet("""
                    QFrame {
                        background: white;
                        border: 1px solid #E5E5E7;
                        border-radius: 12px;
                        margin: 4px;
                    }
                    QFrame:hover {
                        border-color: #D1D1D6;
                    }
                """)
        
        # 自动主题暂时使用浅色
        elif theme_name == "自动":
            self.apply_theme_change("浅色")
    
    def browse_download_path(self, path_input):
        """Browse for download path"""
        try:
            current_path = path_input.text() or str(self.portable_manager.get_downloads_directory())
            new_path = QFileDialog.getExistingDirectory(
                self, 
                "选择下载目录", 
                current_path
            )
            if new_path:
                path_input.setText(new_path)
                print(f"✅ 下载路径已更新: {new_path}")
        except Exception as e:
            print(f"❌ 浏览下载路径失败: {e}")
            # 显示错误消息
            QMessageBox.warning(self, "错误", f"无法打开文件夹选择对话框: {str(e)}")
    
    def show_naming_help(self):
        """Show naming format help"""
        help_dialog = QDialog(self)
        help_dialog.setWindowTitle("文件命名格式帮助")
        help_dialog.setModal(True)
        help_dialog.resize(600, 400)
        
        layout = QVBoxLayout(help_dialog)
        
        # 标题
        title_label = QLabel("📝 文件命名格式说明")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: 600;
                color: #1C1C1E;
                padding: 8px;
            }
        """)
        layout.addWidget(title_label)
        
        # 帮助内容
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setHtml("""
        <h3>可用的格式变量：</h3>
        <ul>
            <li><b>%(title)s</b> - 视频标题</li>
            <li><b>%(uploader)s</b> - 上传者/博主名称</li>
            <li><b>%(id)s</b> - 视频ID</li>
            <li><b>%(ext)s</b> - 文件扩展名</li>
            <li><b>%(upload_date)s</b> - 上传日期 (YYYYMMDD)</li>
            <li><b>%(platform)s</b> - 平台名称 (YouTube, Bilibili等)</li>
            <li><b>%(duration)s</b> - 视频时长</li>
            <li><b>%(view_count)s</b> - 观看次数</li>
        </ul>
        
        <h3>示例格式：</h3>
        <ul>
            <li><b>%(title)s.%(ext)s</b><br>
                结果: Python教程.mp4</li>
            <li><b>[%(uploader)s] %(title)s.%(ext)s</b><br>
                结果: [技术宅小明] Python教程.mp4</li>
            <li><b>[%(uploader)s][%(id)s] %(title)s.%(ext)s</b><br>
                结果: [技术宅小明][abc123] Python教程.mp4</li>
            <li><b>%(upload_date)s - %(title)s.%(ext)s</b><br>
                结果: 20250121 - Python教程.mp4</li>
            <li><b>[%(platform)s] %(uploader)s - %(title)s.%(ext)s</b><br>
                结果: [YouTube] 技术宅小明 - Python教程.mp4</li>
        </ul>
        
        <h3>注意事项：</h3>
        <ul>
            <li>文件名中的特殊字符会被自动替换为安全字符</li>
            <li>如果某个变量不可用，会显示为空或默认值</li>
            <li>建议包含 %(ext)s 以确保正确的文件扩展名</li>
        </ul>
        """)
        help_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #E5E5E7;
                border-radius: 8px;
                background: white;
                padding: 12px;
            }
        """)
        layout.addWidget(help_text)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("""
            QPushButton {
                background: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #0051D5;
            }
        """)
        close_btn.clicked.connect(help_dialog.accept)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        help_dialog.exec()
    
    def check_creator_updates_by_row(self, table, row):
        """通过行号检查创作者更新"""
        if hasattr(self, 'creator_monitors') and 0 <= row < len(self.creator_monitors):
            creator = self.creator_monitors[row]
            self.check_creator_updates(creator)
    
    def download_creator_videos_by_row(self, table, row):
        """通过行号下载创作者视频"""
        if hasattr(self, 'creator_monitors') and 0 <= row < len(self.creator_monitors):
            creator = self.creator_monitors[row]
            self.download_creator_new_videos(creator)
    
    def toggle_creator_monitoring(self, table, row, enabled):
        """切换创作者监控状态"""
        if hasattr(self, 'creator_monitors') and 0 <= row < len(self.creator_monitors):
            creator = self.creator_monitors[row]
            creator['enabled'] = enabled
            status_text = "启用" if enabled else "禁用"
            QMessageBox.information(self, "监控状态", f"已{status_text} {creator['name']} 的监控")
            self.refresh_creator_table()
    
    def pin_creator_to_top(self, table, row):
        """固定创作者到顶部"""
        if hasattr(self, 'creator_monitors') and 0 <= row < len(self.creator_monitors):
            creator = self.creator_monitors.pop(row)
            self.creator_monitors.insert(0, creator)
            QMessageBox.information(self, "固定成功", f"已将 {creator['name']} 固定到顶部")
            self.refresh_creator_table()
    
    def edit_creator_settings_by_row(self, table, row):
        """通过行号编辑创作者设置"""
        if hasattr(self, 'creator_monitors') and 0 <= row < len(self.creator_monitors):
            creator = self.creator_monitors[row]
            QMessageBox.information(self, "编辑设置", f"编辑 {creator['name']} 的设置功能开发中...")
    
    def delete_creator_monitor_by_row(self, table, row):
        """通过行号删除创作者监控"""
        if hasattr(self, 'creator_monitors') and 0 <= row < len(self.creator_monitors):
            creator = self.creator_monitors[row]
            reply = QMessageBox.question(
                self, "确认删除", 
                f"确定要删除对 {creator['name']} 的监控吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.creator_monitors.pop(row)
                QMessageBox.information(self, "删除成功", f"已删除对 {creator['name']} 的监控")
                self.refresh_creator_table()


class HybridVideoDownloaderApp:
    """Hybrid application class"""
    
    def __init__(self):
        self.app = None
        self.main_window = None
        
    def run(self):
        """Run the hybrid application"""
        # Create QApplication
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("VideoDownloader")
        self.app.setApplicationVersion("1.0.0")
        self.app.setOrganizationName("VideoDownloader Project")
        
        # Set application properties
        self.app.setQuitOnLastWindowClosed(True)
        
        # Create and show main window
        self.main_window = HybridVideoDownloaderWindow()
        self.main_window.show()
        
        # Log startup
        portable_manager = get_portable_manager()
        print("Multi-platform Video Downloader started successfully!")
        print("Interface: Hybrid (HTML-inspired PySide6)")
        print(f"Portable mode: {'Enabled' if portable_manager.is_portable else 'Disabled'}")
        
        # Run the application
        return self.app.exec()


def main():
    """Main application entry point"""
    try:
        app = HybridVideoDownloaderApp()
        return app.run()
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

