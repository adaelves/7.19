"""
专业级macOS风格主窗口 - 符合Apple Human Interface Guidelines
重新设计以达到真正的专业水准
"""
import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLineEdit, QPushButton, QScrollArea, QLabel,
    QStatusBar, QFrame, QSizePolicy, QTabWidget,
    QSplitter, QTextEdit, QComboBox, QCheckBox,
    QProgressBar, QListWidget, QListWidgetItem,
    QMenu, QMessageBox, QFileDialog, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QSize, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import (
    QIcon, QPixmap, QPainter, QBrush, QColor, QFont,
    QAction as QGuiAction, QPalette, QLinearGradient
)

from .components.url_input import URLInputWidget
from .components.download_list import DownloadListWidget
from .components.status_bar import CustomStatusBar
from .components.history_widget import HistoryWidget
from .styles.theme_manager import ThemeManager
from .dialogs.settings_dialog import SettingsDialog
from .dialogs.update_dialog import UpdateNotificationDialog, UpdateDialog, UpdateSettingsDialog
from .dialogs.changelog_dialog import ChangelogDialog
from .components.update_progress import CompactUpdateIndicator
from ..services.system_integration_service import SystemIntegrationService
from ..core.updater import UpdateManager


class MacOSMainWindow(QMainWindow):
    """macOS风格主窗口"""
    
    # 信号定义
    url_added = Signal(str)
    theme_changed = Signal(str)
    
    def __init__(self, history_service=None, config_service=None):
        super().__init__()
        self.theme_manager = ThemeManager()
        self.history_service = history_service
        self.config_service = config_service
        
        # Initialize system integration service
        self.system_integration = SystemIntegrationService(self)
        
        # Initialize update manager if config service is available
        self.update_manager = None
        self.auto_updater = None
        if config_service:
            try:
                self.update_manager = UpdateManager(config_service)
                self.auto_updater = self.update_manager.get_updater()
            except Exception as e:
                print(f"Failed to initialize update manager: {e}")
                self.update_manager = None
                self.auto_updater = None
        
        self.setup_window()
        self.setup_ui()
        self.setup_connections()
        self.setup_system_integration()
        self.setup_update_system()
        self.apply_theme()
        
    def setup_window(self):
        """设置窗口基本属性 - 100% macOS原生风格"""
        self.setWindowTitle("多平台视频下载器")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(800, 500)
        self.resize(1200, 800)
        
        # 毛玻璃效果实现
        self.background_frame = QFrame(self)
        self.background_frame.setObjectName("glassBackground")
        self.background_frame.setStyleSheet("""
            #glassBackground {
                background-color: rgba(255, 255, 255, 0.8);
                border-radius: 10px;
            }
        """)
        
        # 阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 51))  # 20%透明度
        self.background_frame.setGraphicsEffect(shadow)
        
        # 设置窗口图标
        self.setWindowIcon(QIcon(":/icons/app_icon.png"))
        
    def setup_ui(self):
        """设置用户界面"""
        # 设置背景框架的几何形状
        self.background_frame.setGeometry(self.rect())
        
        # 创建中央部件
        central_widget = QWidget(self.background_frame)
        central_widget.setObjectName("centralWidget")
        central_widget.setGeometry(self.background_frame.rect())
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 标题栏区域
        self.title_bar = self.create_title_bar()
        main_layout.addWidget(self.title_bar)
        
        # 导航标签栏
        self.nav_bar = self.create_navigation_bar()
        main_layout.addWidget(self.nav_bar)
        
        # 搜索和添加区域
        self.search_bar = self.create_search_bar()
        main_layout.addWidget(self.search_bar)
        
        # 主内容区域（使用堆叠布局切换不同页面）
        self.content_stack = self.create_content_stack()
        main_layout.addWidget(self.content_stack, 1)
        
        # 状态栏
        self.status_bar = self.create_enhanced_status_bar()
        main_layout.addWidget(self.status_bar)
        
    def create_title_bar(self):
        """创建macOS原生风格标题栏 - 完美复刻"""
        title_bar = QFrame()
        title_bar.setObjectName("macTitleBar")
        title_bar.setFixedHeight(29)  # 标准22pt高度
        title_bar.setStyleSheet("""
            #macTitleBar {
                background-color: transparent;
            }
        """)
        
        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(0)
        
        # 窗口控制按钮（精确尺寸和间距）
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(16, 0, 0, 0)
        controls_layout.setSpacing(8)
        
        # 关闭按钮（红色）
        self.close_btn = QPushButton()
        self.close_btn.setFixedSize(12, 12)
        self.close_btn.setStyleSheet("""
            QPushButton {
                border-radius: 6px;
                background-color: #FF3B30;
            }
            QPushButton:hover {
                background-color: #FF453A;
            }
            QPushButton:pressed {
                background-color: #E02020;
            }
        """)
        self.close_btn.clicked.connect(self.close)
        controls_layout.addWidget(self.close_btn)
        
        # 最小化按钮（黄色）
        self.min_btn = QPushButton()
        self.min_btn.setFixedSize(12, 12)
        self.min_btn.setStyleSheet("""
            QPushButton {
                border-radius: 6px;
                background-color: #FFCC00;
            }
            QPushButton:hover {
                background-color: #FFD60A;
            }
            QPushButton:pressed {
                background-color: #E6B800;
            }
        """)
        self.min_btn.clicked.connect(self.showMinimized)
        controls_layout.addWidget(self.min_btn)
        
        # 最大化按钮（绿色）
        self.max_btn = QPushButton()
        self.max_btn.setFixedSize(12, 12)
        self.max_btn.setStyleSheet("""
            QPushButton {
                border-radius: 6px;
                background-color: #34C759;
            }
            QPushButton:hover {
                background-color: #32D74B;
            }
            QPushButton:pressed {
                background-color: #2DB24E;
            }
        """)
        self.max_btn.clicked.connect(self.toggle_maximize)
        controls_layout.addWidget(self.max_btn)
        
        layout.addLayout(controls_layout)
        
        # 中间：标题（居中）
        layout.addStretch()
        title_label = QLabel("多平台视频下载器")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        layout.addStretch()
        
        # 右侧：功能按钮
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)
        
        # 主题切换按钮
        self.theme_btn = QPushButton("🌙")
        self.theme_btn.setObjectName("themeButton")
        self.theme_btn.setFixedSize(24, 24)
        self.theme_btn.setToolTip("切换主题")
        actions_layout.addWidget(self.theme_btn)
        
        # 设置按钮
        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setObjectName("settingsButton")
        self.settings_btn.setFixedSize(24, 24)
        self.settings_btn.setToolTip("设置")
        actions_layout.addWidget(self.settings_btn)
        
        # 文件夹按钮
        folder_btn = QPushButton("📁")
        folder_btn.setObjectName("folderButton")
        folder_btn.setFixedSize(24, 24)
        folder_btn.setToolTip("打开下载文件夹")
        actions_layout.addWidget(folder_btn)
        
        layout.addLayout(actions_layout)
        
        return title_bar
        
    def create_navigation_bar(self):
        """创建导航标签栏"""
        nav_bar = QFrame()
        nav_bar.setObjectName("navigationBar")
        nav_bar.setFixedHeight(36)
        
        layout = QHBoxLayout(nav_bar)
        layout.setContentsMargins(16, 6, 16, 6)
        layout.setSpacing(4)
        
        # 居中对齐
        layout.addStretch()
        
        # 历史记录按钮
        self.history_btn = QPushButton("📋 历史记录")
        self.history_btn.setObjectName("navButton")
        self.history_btn.setCheckable(True)
        self.history_btn.setChecked(True)  # 默认选中
        layout.addWidget(self.history_btn)
        
        # 创作者监控按钮
        self.creator_btn = QPushButton("👁 创作者监控")
        self.creator_btn.setObjectName("navButton")
        self.creator_btn.setCheckable(True)
        layout.addWidget(self.creator_btn)
        
        # 首选项按钮
        self.preferences_btn = QPushButton("⚙️ 首选项")
        self.preferences_btn.setObjectName("navButton")
        self.preferences_btn.setCheckable(True)
        layout.addWidget(self.preferences_btn)
        
        layout.addStretch()
        
        return nav_bar
        
    def create_search_bar(self):
        """创建搜索和添加区域"""
        search_bar = QFrame()
        search_bar.setObjectName("searchBar")
        search_bar.setFixedHeight(50)
        
        layout = QHBoxLayout(search_bar)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(8)
        
        # 搜索输入框
        search_container = QFrame()
        search_container.setObjectName("searchContainer")
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(12, 0, 12, 0)
        search_layout.setSpacing(8)
        
        # 搜索图标
        search_icon = QLabel("🔍")
        search_layout.addWidget(search_icon)
        
        # 输入框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索视频或粘贴链接")
        self.search_input.setObjectName("searchInput")
        search_layout.addWidget(self.search_input)
        
        layout.addWidget(search_container, 1)
        
        # 添加下载按钮
        self.add_download_btn = QPushButton("➕ 添加下载")
        self.add_download_btn.setObjectName("primaryButton")
        layout.addWidget(self.add_download_btn)
        
        # 添加队列按钮
        self.add_queue_btn = QPushButton("📋 添加队列")
        self.add_queue_btn.setObjectName("secondaryButton")
        layout.addWidget(self.add_queue_btn)
        
        return search_bar
        
    def create_content_stack(self):
        """创建主内容区域"""
        from PySide6.QtWidgets import QStackedWidget
        
        content_stack = QStackedWidget()
        content_stack.setObjectName("contentStack")
        
        # 历史记录页面（第一个页面）
        self.history_page = self.create_history_page()
        content_stack.addWidget(self.history_page)
        
        # 创作者监控页面
        self.creator_page = self.create_creator_page()
        content_stack.addWidget(self.creator_page)
        
        # 设置页面
        self.settings_page = self.create_settings_page()
        content_stack.addWidget(self.settings_page)
        
        return content_stack
        
    def create_download_page(self):
        """创建下载列表页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 下载列表
        self.download_list = DownloadListWidget()
        layout.addWidget(self.download_list)
        
        return page
        
    def create_creator_page(self):
        """创建创作者监控页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 标题
        title = QLabel("创作者监控")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        
        # 创作者列表
        self.creator_list = QListWidget()
        self.creator_list.setObjectName("creatorList")
        layout.addWidget(self.creator_list)
        
        # 添加一些示例创作者
        for creator in ["技术宅小明", "前端老司机", "全栈开发秘籍"]:
            item = QListWidgetItem(f"👤 {creator}")
            self.creator_list.addItem(item)
        
        return page
        
    def create_settings_page(self):
        """创建设置页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 标题
        title = QLabel("首选项")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        
        # 快速设置选项
        settings_frame = QFrame()
        settings_frame.setObjectName("settingsFrame")
        settings_layout = QVBoxLayout(settings_frame)
        settings_layout.setSpacing(12)
        
        # 主题设置
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("主题:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["浅色", "深色", "自动"])
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        settings_layout.addLayout(theme_layout)
        
        # 下载路径
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("下载路径:"))
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("选择下载文件夹...")
        path_layout.addWidget(self.path_edit)
        browse_btn = QPushButton("浏览...")
        path_layout.addWidget(browse_btn)
        settings_layout.addLayout(path_layout)
        
        # 并发下载数
        concurrent_layout = QHBoxLayout()
        concurrent_layout.addWidget(QLabel("同时下载数:"))
        self.concurrent_spin = QComboBox()
        self.concurrent_spin.addItems(["1", "2", "3", "4", "5"])
        self.concurrent_spin.setCurrentText("3")
        concurrent_layout.addWidget(self.concurrent_spin)
        concurrent_layout.addStretch()
        settings_layout.addLayout(concurrent_layout)
        
        layout.addWidget(settings_frame)
        
        # 高级设置按钮
        advanced_btn = QPushButton("高级设置...")
        advanced_btn.setObjectName("primaryButton")
        advanced_btn.clicked.connect(self.show_settings)
        layout.addWidget(advanced_btn)
        
        layout.addStretch()
        
        return page
    
    def create_history_page(self):
        """创建历史记录页面"""
        if self.history_service:
            return HistoryWidget(self.history_service)
        else:
            # 如果没有历史服务，显示占位页面
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setContentsMargins(20, 20, 20, 20)
            
            label = QLabel("历史记录功能需要初始化数据库服务")
            label.setObjectName("pageTitle")
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)
            
            return page
        
    def create_enhanced_status_bar(self):
        """创建增强状态栏"""
        status_bar = QFrame()
        status_bar.setObjectName("enhancedStatusBar")
        status_bar.setFixedHeight(32)
        
        layout = QHBoxLayout(status_bar)
        layout.setContentsMargins(16, 4, 16, 4)
        layout.setSpacing(12)
        
        # 左侧状态信息
        self.status_info = QLabel("总计: 0 个下载 • 活动: 0 个 • 已完成: 0 个")
        self.status_info.setObjectName("statusInfo")
        layout.addWidget(self.status_info)
        
        layout.addStretch()
        
        # 更新指示器
        if self.update_manager:
            self.update_indicator = CompactUpdateIndicator()
            self.update_indicator.clicked.connect(self.show_update_info)
            layout.addWidget(self.update_indicator)
            
            separator = QLabel("|")
            separator.setObjectName("statusSeparator")
            layout.addWidget(separator)
        
        # 右侧控制按钮
        self.pause_all_btn = QPushButton("全部暂停")
        self.pause_all_btn.setObjectName("statusButton")
        layout.addWidget(self.pause_all_btn)
        
        separator = QLabel("|")
        separator.setObjectName("statusSeparator")
        layout.addWidget(separator)
        
        self.start_all_btn = QPushButton("全部开始")
        self.start_all_btn.setObjectName("statusButton")
        layout.addWidget(self.start_all_btn)
        
        return status_bar
        
    def setup_connections(self):
        """设置信号连接"""
        # 搜索输入连接
        self.search_input.returnPressed.connect(self.on_search_submitted)
        
        # 主题切换连接
        self.theme_btn.clicked.connect(self.toggle_theme)
        
        # 设置按钮连接
        self.settings_btn.clicked.connect(self.show_settings)
        
        # 导航按钮连接
        self.history_btn.clicked.connect(lambda: self.switch_page(0))
        self.creator_btn.clicked.connect(lambda: self.switch_page(1))
        self.preferences_btn.clicked.connect(lambda: self.switch_page(2))
        
        # 添加按钮连接
        self.add_download_btn.clicked.connect(self.add_download)
        self.add_queue_btn.clicked.connect(self.add_queue)
        
        # 状态栏按钮连接
        self.pause_all_btn.clicked.connect(self.pause_all_downloads)
        self.start_all_btn.clicked.connect(self.start_all_downloads)
        
    def setup_system_integration(self):
        """设置系统集成功能"""
        # 连接系统集成服务的信号
        self.system_integration.show_window_requested.connect(self.show_and_raise)
        self.system_integration.hide_window_requested.connect(self.hide_to_tray)
        self.system_integration.quit_requested.connect(self.close)
        
        # 显示托盘图标
        self.system_integration.show_tray_icon()
        
        # 设置窗口关闭行为（最小化到托盘而不是退出）
        self.setAttribute(Qt.WA_QuitOnClose, False)
    
    def setup_update_system(self):
        """设置更新系统"""
        if not self.auto_updater:
            return
        
        # 连接更新系统信号
        self.auto_updater.update_available.connect(self.on_update_available)
        self.auto_updater.error_occurred.connect(self.on_update_error)
        
        # 启动自动检查
        self.auto_updater.start_auto_check()
        
        # 初始化更新指示器状态
        if hasattr(self, 'update_indicator'):
            version_info = self.update_manager.get_version_info()
            if version_info['update_available']:
                self.update_indicator.set_update_available(True, version_info['available_version'])
            else:
                self.update_indicator.set_update_available(False)
        
    def toggle_theme(self):
        """切换主题"""
        current_theme = self.theme_manager.current_theme
        new_theme = "dark" if current_theme == "light" else "light"
        self.theme_manager.set_theme(new_theme)
        self.apply_theme()
        self.theme_changed.emit(new_theme)
        
    def apply_theme(self):
        """应用主题样式"""
        stylesheet = self.theme_manager.get_stylesheet()
        self.setStyleSheet(stylesheet)
        
        # 更新主题按钮图标
        theme_icon = "🌙" if self.theme_manager.current_theme == "light" else "☀️"
        self.theme_btn.setText(theme_icon)
        
    def show_settings(self):
        """显示设置对话框"""
        settings_dialog = SettingsDialog(self)
        settings_dialog.settings_changed.connect(self.on_settings_changed)
        settings_dialog.exec()
        
    def on_settings_changed(self, settings):
        """设置改变时的处理"""
        # 如果主题改变，更新界面
        if 'theme' in settings:
            if settings['theme'] != self.theme_manager.current_theme:
                self.theme_manager.set_theme(settings['theme'])
                self.apply_theme()
                self.theme_changed.emit(settings['theme'])
        
        # 处理系统集成设置
        if 'startup_enabled' in settings:
            self.system_integration.enable_startup(settings['startup_enabled'])
            
        if 'boss_key' in settings:
            self.system_integration.set_boss_key(settings['boss_key'])
            
        if 'protocol_registered' in settings and settings['protocol_registered']:
            self.system_integration.register_protocol_handler()
            
        if 'file_associations_enabled' in settings and settings['file_associations_enabled']:
            self.system_integration.register_file_associations()
        
    def add_download_task(self, url: str, metadata: dict = None):
        """添加下载任务"""
        self.download_list.add_task(url, metadata)
        
    def update_status(self, message: str, progress: int = 0):
        """更新状态栏"""
        self.status_bar.update_status(message, progress)
        
    def switch_page(self, page_index):
        """切换页面"""
        # 更新导航按钮状态
        nav_buttons = [self.history_btn, self.creator_btn, self.preferences_btn]
        for i, btn in enumerate(nav_buttons):
            btn.setChecked(i == page_index)
        
        # 切换内容页面
        self.content_stack.setCurrentIndex(page_index)
        
    def on_search_submitted(self):
        """搜索提交处理"""
        search_text = self.search_input.text().strip()
        if search_text:
            # 如果是URL，直接添加下载
            if search_text.startswith(('http://', 'https://', 'www.')):
                self.add_download_from_url(search_text)
            else:
                # 否则进行搜索
                self.search_videos(search_text)
                
    def add_download(self):
        """添加下载"""
        url = self.search_input.text().strip()
        if url:
            self.add_download_from_url(url)
            self.search_input.clear()
        else:
            # 显示添加下载对话框
            self.show_add_download_dialog()
            
    def add_queue(self):
        """添加队列"""
        # 显示批量添加对话框
        self.show_batch_add_dialog()
        
    def add_download_from_url(self, url: str):
        """从URL添加下载"""
        # 这里会调用下载管理器添加任务
        self.url_added.emit(url)
        self.update_status_info()
        
    def search_videos(self, query: str):
        """搜索视频"""
        # 实现视频搜索功能
        print(f"搜索视频: {query}")
        
    def show_add_download_dialog(self):
        """显示添加下载对话框"""
        # 实现添加下载对话框
        print("显示添加下载对话框")
        
    def show_batch_add_dialog(self):
        """显示批量添加对话框"""
        # 实现批量添加对话框
        print("显示批量添加对话框")
        
    def pause_all_downloads(self):
        """暂停所有下载"""
        # 实现暂停所有下载功能
        print("暂停所有下载")
        self.update_status_info()
        
    def start_all_downloads(self):
        """开始所有下载"""
        # 实现开始所有下载功能
        print("开始所有下载")
        self.update_status_info()
        
    def update_status_info(self):
        """更新状态信息"""
        # 这里应该从下载管理器获取实际状态
        # 暂时使用示例数据
        total = 6
        active = 3
        paused = 1
        completed = 1
        failed = 1
        
        status_text = f"总计: {total} 个下载 • 活动: {active} 个 • 暂停: {paused} 个 • 已完成: {completed} 个 • 失败: {failed} 个"
        self.status_info.setText(status_text)
    
    # 更新系统相关方法
    def on_update_available(self, release_info):
        """处理发现更新"""
        if hasattr(self, 'update_indicator'):
            self.update_indicator.set_update_available(True, release_info.version)
        
        # 显示更新通知（如果不是静默模式）
        if not self.auto_updater.silent_mode:
            self.show_update_notification(release_info)
    
    def on_update_error(self, error_message):
        """处理更新错误"""
        if hasattr(self, 'update_indicator'):
            self.update_indicator.set_error(error_message)
        
        # 显示错误消息
        QMessageBox.warning(self, "更新错误", f"检查更新时发生错误：\n{error_message}")
    
    def show_update_info(self):
        """显示更新信息"""
        if not self.update_manager:
            QMessageBox.information(self, "更新", "更新功能未启用")
            return
        
        version_info = self.update_manager.get_version_info()
        
        if version_info['update_available']:
            # 显示更新对话框
            release_info = self.auto_updater.get_available_update()
            if release_info:
                dialog = UpdateDialog(release_info, self)
                dialog.set_update_service(self.auto_updater.update_service)
                dialog.exec()
        else:
            # 显示当前版本信息或强制检查更新
            self.show_version_info()
    
    def show_update_notification(self, release_info):
        """显示更新通知对话框"""
        dialog = UpdateNotificationDialog(release_info, self)
        if dialog.exec() == UpdateNotificationDialog.Accepted:
            # 用户选择更新
            update_dialog = UpdateDialog(release_info, self)
            update_dialog.set_update_service(self.auto_updater.update_service)
            update_dialog.exec()
    
    def show_version_info(self):
        """显示版本信息"""
        if not self.update_manager:
            return
        
        version_info = self.update_manager.get_version_info()
        current_version = version_info['current_version']
        last_check = version_info['last_check']
        
        last_check_str = "从未" if not last_check else last_check.strftime("%Y-%m-%d %H:%M")
        
        message = f"""当前版本: {current_version}
上次检查: {last_check_str}
状态: 已是最新版本

是否立即检查更新？"""
        
        reply = QMessageBox.question(
            self, "版本信息", message,
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.check_for_updates()
    
    def check_for_updates(self):
        """手动检查更新"""
        if not self.auto_updater:
            return
        
        if hasattr(self, 'update_indicator'):
            self.update_indicator.set_updating(True)
        
        # 强制检查更新
        self.auto_updater.force_check_update()
    
    def show_changelog(self):
        """显示更新日志"""
        if not self.auto_updater:
            return
        
        dialog = ChangelogDialog(self.auto_updater.update_service, self)
        dialog.exec()
    
    def show_update_settings(self):
        """显示更新设置"""
        if not self.auto_updater:
            return
        
        dialog = UpdateSettingsDialog(self.auto_updater.update_service, self)
        dialog.exec()
        
    def show_and_raise(self):
        """显示并激活窗口"""
        self.show()
        self.raise_()
        self.activateWindow()
        
    def hide_to_tray(self):
        """隐藏到系统托盘"""
        self.hide()
        if self.system_integration.tray_icon:
            self.system_integration.show_notification(
                "多平台视频下载器",
                "应用程序已最小化到系统托盘",
                2000
            )
    
    def toggle_maximize(self):
        """切换最大化状态"""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
    
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
    
    def resizeEvent(self, event):
        """窗口大小变化事件"""
        super().resizeEvent(event)
        # 调整背景框架大小
        if hasattr(self, 'background_frame'):
            self.background_frame.setGeometry(self.rect())
            # 调整中央部件大小
            central_widget = self.background_frame.findChild(QWidget, "centralWidget")
            if central_widget:
                central_widget.setGeometry(self.background_frame.rect())
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 如果系统托盘可用，最小化到托盘而不是退出
        if self.system_integration.tray_icon and self.system_integration.tray_icon.isVisible():
            event.ignore()
            self.hide_to_tray()
        else:
            # 保存当前主题设置
            self.theme_manager.save_settings()
            # 清理系统集成资源
            self.system_integration.cleanup()
            event.accept()

# Backward compatibility alias
MainWindow = MacOSMainWindow