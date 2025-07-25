"""
基于HTML设计的macOS风格视频下载器界面
完全按照video_downloader (1).html的设计实现
"""
import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLineEdit, QPushButton, QScrollArea, QLabel,
    QFrame, QSizePolicy, QTabWidget, QStackedWidget,
    QSplitter, QTextEdit, QComboBox, QCheckBox,
    QProgressBar, QListWidget, QListWidgetItem,
    QMenu, QMessageBox, QFileDialog, QGraphicsDropShadowEffect,
    QApplication
)
from PySide6.QtCore import Qt, QSize, Signal, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import (
    QIcon, QPixmap, QPainter, QBrush, QColor, QFont,
    QAction as QGuiAction, QPalette, QLinearGradient, QPainterPath
)


class HTMLStyleWindow(QMainWindow):
    """基于HTML设计的macOS风格主窗口"""
    
    # 信号定义
    url_added = Signal(str)
    theme_changed = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.current_theme = "light"
        self.setup_window()
        self.setup_ui()
        self.setup_connections()
        self.apply_html_styles()
        
    def setup_window(self):
        """设置窗口基本属性 - 按照HTML设计"""
        self.setWindowTitle("视频下载器")
        self.setFixedSize(900, 600)  # HTML中的固定尺寸
        
        # macOS风格窗口设置
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        
        # 窗口阴影效果 - 按照HTML的window-shadow样式
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(25)  # 对应HTML的0 10px 50px
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(10)
        self.shadow.setColor(QColor(0, 0, 0, 51))  # rgba(0, 0, 0, 0.2)
        self.setGraphicsEffect(self.shadow)
        
        # 居中显示
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)     
   
    def setup_ui(self):
        """设置用户界面 - 完全按照HTML布局"""
        # 创建主容器 - 对应HTML的mainWindow
        main_container = QWidget()
        main_container.setObjectName("mainWindow")
        self.setCentralWidget(main_container)
        
        # 主布局 - flex flex-col
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. macOS风格标题栏
        self.title_bar = self.create_html_title_bar()
        main_layout.addWidget(self.title_bar)
        
        # 2. 顶部导航按钮
        self.nav_bar = self.create_html_navigation()
        main_layout.addWidget(self.nav_bar)
        
        # 3. 搜索和添加区域
        self.search_bar = self.create_html_search_bar()
        main_layout.addWidget(self.search_bar)
        
        # 4. 下载列表区域 (flex-1)
        self.download_area = self.create_html_download_area()
        main_layout.addWidget(self.download_area, 1)
        
        # 5. 底部状态栏
        self.status_bar = self.create_html_status_bar()
        main_layout.addWidget(self.status_bar)
        
    def create_html_title_bar(self):
        """创建HTML风格的macOS标题栏"""
        title_bar = QFrame()
        title_bar.setObjectName("htmlTitleBar")
        title_bar.setFixedHeight(40)  # HTML中的h-10 (2.5rem = 40px)
        
        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(16, 0, 16, 0)  # px-4
        layout.setSpacing(0)
        
        # 左侧：窗口控制按钮 - 对应HTML的交通灯按钮
        controls_container = QWidget()
        controls_layout = QHBoxLayout(controls_container)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(8)  # space-x-2
        
        # 红色关闭按钮 - bg-macos-button-red
        self.close_btn = QPushButton()
        self.close_btn.setObjectName("macosButtonRed")
        self.close_btn.setFixedSize(20, 20)  # w-5 h-5
        self.close_btn.clicked.connect(self.close)
        controls_layout.addWidget(self.close_btn)
        
        # 黄色最小化按钮 - bg-macos-button-yellow
        self.minimize_btn = QPushButton()
        self.minimize_btn.setObjectName("macosButtonYellow")
        self.minimize_btn.setFixedSize(20, 20)
        self.minimize_btn.clicked.connect(self.showMinimized)
        controls_layout.addWidget(self.minimize_btn)
        
        # 绿色最大化按钮 - bg-macos-button-green
        self.maximize_btn = QPushButton()
        self.maximize_btn.setObjectName("macosButtonGreen")
        self.maximize_btn.setFixedSize(20, 20)
        self.maximize_btn.clicked.connect(self.toggle_maximize)
        controls_layout.addWidget(self.maximize_btn)
        
        layout.addWidget(controls_container)
        
        # 中间：窗口标题
        title_label = QLabel("视频下载器")
        title_label.setObjectName("windowTitle")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label, 1)
        
        # 右侧：菜单按钮 (装饰性)
        menu_btn = QLabel("⌄")  # 对应HTML的fa-chevron-down
        menu_btn.setObjectName("menuButton")
        layout.addWidget(menu_btn)
        
        return title_bar 
       
    def create_html_navigation(self):
        """创建HTML风格的导航栏"""
        nav_bar = QFrame()
        nav_bar.setObjectName("htmlNavBar")
        nav_bar.setFixedHeight(36)  # py-1.5 的高度
        
        layout = QHBoxLayout(nav_bar)
        layout.setContentsMargins(16, 6, 16, 6)  # px-4 py-1.5
        layout.setSpacing(4)  # ml-1
        
        # 居中布局
        layout.addStretch()
        
        # 历史记录按钮 - 默认激活
        self.history_btn = QPushButton("📋 历史记录")
        self.history_btn.setObjectName("navButtonActive")
        self.history_btn.setCheckable(True)
        self.history_btn.setChecked(True)
        layout.addWidget(self.history_btn)
        
        # 创作者监控按钮
        self.creator_btn = QPushButton("👁 创作者监控")
        self.creator_btn.setObjectName("navButton")
        self.creator_btn.setCheckable(True)
        layout.addWidget(self.creator_btn)
        
        # 首选项按钮
        self.settings_btn = QPushButton("⚙️ 首选项")
        self.settings_btn.setObjectName("navButton")
        self.settings_btn.setCheckable(True)
        layout.addWidget(self.settings_btn)
        
        layout.addStretch()
        
        return nav_bar
        
    def create_html_search_bar(self):
        """创建HTML风格的搜索和添加区域"""
        search_bar = QFrame()
        search_bar.setObjectName("htmlSearchBar")
        search_bar.setFixedHeight(50)  # p-2 的高度
        
        layout = QHBoxLayout(search_bar)
        layout.setContentsMargins(8, 8, 8, 8)  # p-2
        layout.setSpacing(8)  # space-x-2
        
        # 搜索输入框容器
        search_container = QFrame()
        search_container.setObjectName("searchContainer")
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(12, 0, 16, 0)  # pl-10 pr-4
        search_layout.setSpacing(8)
        
        # 搜索图标
        search_icon = QLabel("🔍")
        search_icon.setObjectName("searchIcon")
        search_layout.addWidget(search_icon)
        
        # 搜索输入框
        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("搜索视频或粘贴链接")
        search_layout.addWidget(self.search_input, 1)
        
        layout.addWidget(search_container, 1)
        
        # 按钮容器
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(6)  # space-x-1.5
        
        # 添加下载按钮 - 主要按钮
        self.add_download_btn = QPushButton("➕ 添加下载")
        self.add_download_btn.setObjectName("primaryButton")
        buttons_layout.addWidget(self.add_download_btn)
        
        # 添加队列按钮 - 次要按钮
        self.add_queue_btn = QPushButton("📋 添加队列")
        self.add_queue_btn.setObjectName("secondaryButton")
        buttons_layout.addWidget(self.add_queue_btn)
        
        layout.addWidget(buttons_container)
        
        return search_bar     
   
    def create_html_download_area(self):
        """创建HTML风格的下载列表区域"""
        download_area = QFrame()
        download_area.setObjectName("htmlDownloadArea")
        
        layout = QVBoxLayout(download_area)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setObjectName("downloadScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 滚动内容
        scroll_content = QWidget()
        scroll_content.setObjectName("scrollContent")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(8, 8, 8, 8)  # p-2
        scroll_layout.setSpacing(0)
        
        # 分组标题
        group_title = QLabel("正在下载")
        group_title.setObjectName("groupTitle")
        scroll_layout.addWidget(group_title)
        
        # 添加示例下载项
        self.add_sample_download_items(scroll_layout)
        
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        return download_area
        
    def add_sample_download_items(self, layout):
        """添加示例下载项"""
        # 下载项数据
        download_items = [
            {
                "title": "Python编程教程 - 从入门到精通",
                "progress": 78,
                "size": "99.8 MB/128.5 MB",
                "time": "剩余时间: 00:23",
                "speed": "1.2 MB/s",
                "status": "downloading"
            },
            {
                "title": "Web开发实战 - React框架详解",
                "progress": 45,
                "size": "115.3 MB/256.3 MB",
                "time": "剩余时间: 01:02",
                "speed": "2.4 MB/s",
                "status": "downloading"
            },
            {
                "title": "[Channel] 技术宅小明",
                "progress": 40,
                "size": "1.3 GB/3.2 GB",
                "time": "剩余时间: 08:45",
                "speed": "1.8 MB/s",
                "status": "downloading",
                "is_channel": True,
                "channel_progress": "5/20"
            },
            {
                "title": "机器学习入门 - 神经网络基础",
                "progress": 33,
                "size": "62.4 MB/189.2 MB",
                "time": "已暂停",
                "speed": "0.0 MB/s",
                "status": "paused"
            },
            {
                "title": "数据结构与算法 - 高级篇",
                "progress": 100,
                "size": "320.7 MB/320.7 MB",
                "time": "已完成",
                "speed": "3.5 MB/s",
                "status": "completed"
            },
            {
                "title": "前端工程化实战教程",
                "progress": 65,
                "size": "140.0 MB/215.4 MB",
                "time": "下载失败",
                "speed": "0.0 MB/s",
                "status": "failed"
            }
        ]
        
        for i, item in enumerate(download_items):
            download_item = self.create_download_item(item, i == 0)
            layout.addWidget(download_item)  
      
    def create_download_item(self, item_data, is_first=False):
        """创建单个下载项"""
        item = QFrame()
        item.setObjectName(f"downloadItem_{item_data['status']}")
        if is_first:
            item.setProperty("isFirst", True)
        
        layout = QHBoxLayout(item)
        layout.setContentsMargins(8, 8, 8, 8)  # p-2
        layout.setSpacing(8)  # ml-2
        
        # 缩略图
        thumbnail = QLabel("🎬")
        thumbnail.setObjectName("downloadThumbnail")
        thumbnail.setFixedSize(128, 80)  # w-32 h-20
        thumbnail.setAlignment(Qt.AlignCenter)
        thumbnail.setStyleSheet("background-color: #f0f0f0; border-radius: 4px;")
        layout.addWidget(thumbnail)
        
        # 信息区域
        info_container = QWidget()
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(4)
        
        # 标题和操作按钮行
        title_row = QWidget()
        title_layout = QHBoxLayout(title_row)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(8)
        
        # 标题
        title_label = QLabel(item_data["title"])
        title_label.setObjectName("downloadTitle")
        title_layout.addWidget(title_label, 1)
        
        # 操作按钮
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(4)
        
        # 根据状态显示不同按钮
        if item_data["status"] == "downloading":
            pause_btn = QPushButton("⏸")
        elif item_data["status"] == "paused":
            pause_btn = QPushButton("▶")
        elif item_data["status"] == "failed":
            pause_btn = QPushButton("🔄")
        else:
            pause_btn = QPushButton("▶")
        
        pause_btn.setObjectName("actionButton")
        pause_btn.setFixedSize(24, 24)
        buttons_layout.addWidget(pause_btn)
        
        cancel_btn = QPushButton("✕")
        cancel_btn.setObjectName("actionButton")
        cancel_btn.setFixedSize(24, 24)
        buttons_layout.addWidget(cancel_btn)
        
        folder_btn = QPushButton("📁")
        folder_btn.setObjectName("actionButton")
        folder_btn.setFixedSize(24, 24)
        buttons_layout.addWidget(folder_btn)
        
        title_layout.addWidget(buttons_container)
        info_layout.addWidget(title_row)
        
        # 进度条行
        progress_row = QWidget()
        progress_layout = QHBoxLayout(progress_row)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(8)
        
        # 进度条
        progress_bar = QProgressBar()
        progress_bar.setObjectName(f"progressBar_{item_data['status']}")
        progress_bar.setValue(item_data["progress"])
        progress_bar.setFixedHeight(6)  # h-1.5
        progress_bar.setTextVisible(False)
        progress_layout.addWidget(progress_bar, 1)
        
        # 进度百分比或频道进度
        if item_data.get("is_channel"):
            progress_text = item_data["channel_progress"]
        else:
            progress_text = f"{item_data['progress']}%"
        
        progress_label = QLabel(progress_text)
        progress_label.setObjectName(f"progressText_{item_data['status']}")
        progress_layout.addWidget(progress_label)
        
        info_layout.addWidget(progress_row)
        
        # 详细信息行
        details_row = QWidget()
        details_layout = QHBoxLayout(details_row)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(16)
        
        size_label = QLabel(item_data["size"])
        size_label.setObjectName("detailText")
        details_layout.addWidget(size_label)
        
        time_label = QLabel(item_data["time"])
        time_label.setObjectName("detailText")
        details_layout.addWidget(time_label)
        
        speed_label = QLabel(item_data["speed"])
        speed_label.setObjectName("detailText")
        details_layout.addWidget(speed_label)
        
        details_layout.addStretch()
        info_layout.addWidget(details_row)
        
        layout.addWidget(info_container, 1)
        
        return item        

    def create_html_status_bar(self):
        """创建HTML风格的状态栏"""
        status_bar = QFrame()
        status_bar.setObjectName("htmlStatusBar")
        status_bar.setFixedHeight(32)  # py-1.5 的高度
        
        layout = QHBoxLayout(status_bar)
        layout.setContentsMargins(12, 6, 12, 6)  # px-3 py-1.5
        layout.setSpacing(0)
        
        # 左侧：统计信息
        stats_container = QWidget()
        stats_layout = QHBoxLayout(stats_container)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(6)  # mx-1.5
        
        # 统计文本
        stats_texts = [
            "总计: 6 个下载",
            "活动: 3 个", 
            "暂停: 1 个",
            "已完成: 1 个",
            "失败: 1 个"
        ]
        
        for i, text in enumerate(stats_texts):
            if i > 0:
                separator = QLabel("•")
                separator.setObjectName("statusSeparator")
                stats_layout.addWidget(separator)
            
            label = QLabel(text)
            label.setObjectName("statusText")
            stats_layout.addWidget(label)
        
        layout.addWidget(stats_container)
        layout.addStretch()
        
        # 右侧：控制按钮
        controls_container = QWidget()
        controls_layout = QHBoxLayout(controls_container)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(6)
        
        pause_all_btn = QPushButton("全部暂停")
        pause_all_btn.setObjectName("statusButton")
        controls_layout.addWidget(pause_all_btn)
        
        separator = QLabel("|")
        separator.setObjectName("statusSeparator")
        controls_layout.addWidget(separator)
        
        start_all_btn = QPushButton("全部开始")
        start_all_btn.setObjectName("statusButton")
        controls_layout.addWidget(start_all_btn)
        
        layout.addWidget(controls_container)
        
        return status_bar
        
    def setup_connections(self):
        """设置信号连接"""
        self.history_btn.clicked.connect(lambda: self.switch_tab("history"))
        self.creator_btn.clicked.connect(lambda: self.switch_tab("creator"))
        self.settings_btn.clicked.connect(lambda: self.switch_tab("settings"))
        
        self.add_download_btn.clicked.connect(self.add_download)
        self.add_queue_btn.clicked.connect(self.add_queue)
        
    def switch_tab(self, tab_name):
        """切换标签页"""
        # 重置所有按钮状态
        buttons = [self.history_btn, self.creator_btn, self.settings_btn]
        for btn in buttons:
            btn.setChecked(False)
            btn.setObjectName("navButton")
        
        # 设置当前按钮为激活状态
        if tab_name == "history":
            self.history_btn.setChecked(True)
            self.history_btn.setObjectName("navButtonActive")
        elif tab_name == "creator":
            self.creator_btn.setChecked(True)
            self.creator_btn.setObjectName("navButtonActive")
        elif tab_name == "settings":
            self.settings_btn.setChecked(True)
            self.settings_btn.setObjectName("navButtonActive")
        
        # 重新应用样式
        self.apply_html_styles()
        
    def toggle_maximize(self):
        """切换最大化状态"""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
            
    def add_download(self):
        """添加下载"""
        url = self.search_input.text().strip()
        if url:
            print(f"添加下载: {url}")
            self.search_input.clear()
        
    def add_queue(self):
        """添加队列"""
        print("添加队列功能")
        
    def mousePressEvent(self, event):
        """鼠标按下事件 - 用于窗口拖拽"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 窗口拖拽"""
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_position'):
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()  
          
    def apply_html_styles(self):
        """应用HTML风格的样式"""
        stylesheet = '''
        /* 主窗口容器 - 对应HTML的mainWindow */
        #mainWindow {
            background-color: white;
            border-radius: 12px;
            border: 1px solid #e5e7eb;
        }
        
        /* macOS标题栏 - 对应HTML的macos-titlebar bg-macos-titlebar */
        #htmlTitleBar {
            background-color: #e8e8e8;
            border-bottom: 1px solid #d1d5db;
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
        }
        
        /* 窗口标题 */
        #windowTitle {
            color: #374151;
            font-size: 14px;
            font-weight: 500;
        }
        
        /* 菜单按钮 */
        #menuButton {
            color: #6b7280;
            font-size: 12px;
        }
        
        /* macOS交通灯按钮 */
        #macosButtonRed {
            background-color: #ff5f56;
            border: none;
            border-radius: 10px;
        }
        #macosButtonRed:hover {
            background-color: #ff4136;
        }
        
        #macosButtonYellow {
            background-color: #ffbd2e;
            border: none;
            border-radius: 10px;
        }
        #macosButtonYellow:hover {
            background-color: #ffaa00;
        }
        
        #macosButtonGreen {
            background-color: #27c93f;
            border: none;
            border-radius: 10px;
        }
        #macosButtonGreen:hover {
            background-color: #1db954;
        }
        
        /* 导航栏 */
        #htmlNavBar {
            background-color: #e8e8e8;
        }
        
        /* 导航按钮 */
        #navButton {
            background-color: transparent;
            border: none;
            border-radius: 6px;
            padding: 6px 16px;
            font-size: 14px;
            color: #374151;
        }
        #navButton:hover {
            background-color: #f3f4f6;
        }
        
        /* 激活的导航按钮 */
        #navButtonActive {
            background-color: #e5e7eb;
            border: none;
            border-radius: 6px;
            padding: 6px 16px;
            font-size: 14px;
            color: #374151;
            font-weight: 500;
        }
        
        /* 搜索栏 */
        #htmlSearchBar {
            background-color: white;
            border-bottom: 1px solid #e5e7eb;
        }
        
        /* 搜索容器 */
        #searchContainer {
            background-color: white;
            border: 1px solid #d1d5db;
            border-radius: 8px;
        }
        
        /* 搜索输入框 */
        #searchInput {
            background-color: transparent;
            border: none;
            font-size: 14px;
            color: #111827;
            padding: 6px 0;
        }
        #searchInput::placeholder {
            color: #9ca3af;
        }
        
        /* 搜索图标 */
        #searchIcon {
            color: #9ca3af;
            font-size: 14px;
        }
        
        /* 主要按钮 */
        #primaryButton {
            background-color: #0071e3;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 6px 12px;
            font-size: 14px;
            font-weight: 500;
        }
        #primaryButton:hover {
            background-color: #0051cc;
        }
        
        /* 次要按钮 */
        #secondaryButton {
            background-color: #f3f4f6;
            color: #374151;
            border: none;
            border-radius: 8px;
            padding: 6px 12px;
            font-size: 14px;
            font-weight: 500;
        }
        #secondaryButton:hover {
            background-color: #e5e7eb;
        }
        
        /* 下载区域 */
        #htmlDownloadArea {
            background-color: white;
        }
        
        /* 滚动区域 */
        #downloadScrollArea {
            background-color: white;
            border: none;
        }
        
        /* 分组标题 */
        #groupTitle {
            font-size: 14px;
            font-weight: 500;
            color: #374151;
            margin-bottom: 8px;
            padding: 0 8px;
        }
        
        /* 下载项 - 不同状态 */
        #downloadItem_downloading {
            background-color: white;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            margin-bottom: 0;
        }
        #downloadItem_downloading[isFirst="true"] {
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        }
        #downloadItem_downloading:hover {
            border-color: #d1d5db;
        }
        
        #downloadItem_paused {
            background-color: #fff7e6;
            border: 1px solid #e5e7eb;
            border-top: none;
            margin-bottom: 0;
        }
        #downloadItem_paused:hover {
            border-color: #d1d5db;
        }
        
        #downloadItem_completed {
            background-color: #e6fffa;
            border: 1px solid #e5e7eb;
            border-top: none;
            margin-bottom: 0;
        }
        #downloadItem_completed:hover {
            border-color: #d1d5db;
        }
        
        #downloadItem_failed {
            background-color: #ffebee;
            border: 1px solid #e5e7eb;
            border-top: none;
            margin-bottom: 0;
        }
        #downloadItem_failed:hover {
            border-color: #d1d5db;
        }
        
        /* 下载标题 */
        #downloadTitle {
            font-size: 14px;
            font-weight: 500;
            color: #111827;
        }
        
        /* 操作按钮 */
        #actionButton {
            background-color: transparent;
            border: none;
            color: #9ca3af;
            font-size: 14px;
            padding: 4px;
        }
        #actionButton:hover {
            color: #374151;
        }
        
        /* 进度条 - 不同状态 */
        #progressBar_downloading {
            background-color: #e5e7eb;
            border: none;
            border-radius: 3px;
        }
        #progressBar_downloading::chunk {
            background-color: #0071e3;
            border-radius: 3px;
        }
        
        #progressBar_paused::chunk {
            background-color: #ff9500;
            border-radius: 3px;
        }
        
        #progressBar_completed::chunk {
            background-color: #34c759;
            border-radius: 3px;
        }
        
        #progressBar_failed::chunk {
            background-color: #ff3b30;
            border-radius: 3px;
        }
        
        /* 进度文本 */
        #progressText_downloading {
            font-size: 12px;
            color: #6b7280;
        }
        #progressText_paused {
            font-size: 12px;
            color: #ff9500;
        }
        #progressText_completed {
            font-size: 12px;
            color: #34c759;
        }
        #progressText_failed {
            font-size: 12px;
            color: #ff3b30;
        }
        
        /* 详细信息文本 */
        #detailText {
            font-size: 12px;
            color: #6b7280;
        }
        
        /* 状态栏 */
        #htmlStatusBar {
            background-color: white;
            border-top: 1px solid #e5e7eb;
            border-bottom-left-radius: 12px;
            border-bottom-right-radius: 12px;
        }
        
        /* 状态文本 */
        #statusText {
            font-size: 12px;
            color: #6b7280;
        }
        
        /* 状态分隔符 */
        #statusSeparator {
            font-size: 12px;
            color: #d1d5db;
        }
        
        /* 状态按钮 */
        #statusButton {
            background-color: transparent;
            border: none;
            color: #0071e3;
            font-size: 12px;
            padding: 4px 8px;
        }
        #statusButton:hover {
            color: #0051cc;
        }
        
        /* 滚动条样式 */
        QScrollBar:vertical {
            background: transparent;
            width: 8px;
            border-radius: 4px;
        }
        QScrollBar::handle:vertical {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 4px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background: rgba(0, 0, 0, 0.3);
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        '''
        
        self.setStyleSheet(stylesheet)