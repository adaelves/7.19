"""
UI组件演示 - 展示所有核心UI组件的功能
"""
import sys
import random
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QWidget, QPushButton, QLabel, QFrame, QGroupBox
)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont

# 添加项目根目录到路径
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入UI组件
from app.ui.components.url_input import URLInputWidget
from app.ui.components.download_task_card import DownloadTaskCard, MagicProgressBar, StatusIndicator
from app.ui.components.download_list import DownloadListWidget
from app.ui.components.status_bar import CustomStatusBar
from app.ui.components.touch_context_menu import TouchContextMenu


class UIComponentsDemo(QMainWindow):
    """UI组件演示窗口"""
    
    def __init__(self):
        super().__init__()
        self.task_counter = 0
        self.setup_ui()
        self.setup_demo_data()
        self.setup_timers()
        
    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("多平台视频下载器 - UI组件演示")
        self.setGeometry(100, 100, 1000, 700)
        
        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f7;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        # 主容器
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # 标题
        title_label = QLabel("🎬 多平台视频下载器 - 核心UI组件演示")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("""
            QLabel {
                color: #1d1d1f;
                padding: 10px;
                background-color: white;
                border-radius: 10px;
                border: 1px solid rgba(0, 0, 0, 0.1);
            }
        """)
        main_layout.addWidget(title_label)
        
        # 创建演示区域
        demo_layout = QHBoxLayout()
        
        # 左侧 - 主要组件
        left_panel = self.create_main_components_panel()
        demo_layout.addWidget(left_panel, 2)
        
        # 右侧 - 独立组件演示
        right_panel = self.create_individual_components_panel()
        demo_layout.addWidget(right_panel, 1)
        
        main_layout.addLayout(demo_layout)
        
        # 状态栏
        self.status_bar = CustomStatusBar()
        self.setStatusBar(self.status_bar)
        
    def create_main_components_panel(self):
        """创建主要组件面板"""
        group = QGroupBox("主要组件演示")
        layout = QVBoxLayout(group)
        
        # URL输入组件
        self.url_input = URLInputWidget()
        self.url_input.url_submitted.connect(self.on_url_submitted)
        layout.addWidget(self.url_input)
        
        # 下载列表组件
        self.download_list = DownloadListWidget()
        self.download_list.task_action.connect(self.on_task_action)
        layout.addWidget(self.download_list)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        
        add_demo_btn = QPushButton("添加演示任务")
        add_demo_btn.clicked.connect(self.add_demo_task)
        add_demo_btn.setStyleSheet("""
            QPushButton {
                background-color: #007aff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0056cc;
            }
        """)
        control_layout.addWidget(add_demo_btn)
        
        clear_btn = QPushButton("清空列表")
        clear_btn.clicked.connect(self.clear_tasks)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff3b30;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #d70015;
            }
        """)
        control_layout.addWidget(clear_btn)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        return group
        
    def create_individual_components_panel(self):
        """创建独立组件演示面板"""
        group = QGroupBox("独立组件演示")
        layout = QVBoxLayout(group)
        
        # 魔法进度条演示
        progress_group = QGroupBox("魔法进度条")
        progress_layout = QVBoxLayout(progress_group)
        
        self.demo_progress = MagicProgressBar()
        progress_layout.addWidget(self.demo_progress)
        
        progress_info = QLabel("实时波形图效果，显示下载速度变化")
        progress_info.setStyleSheet("color: #8e8e93; font-size: 12px;")
        progress_layout.addWidget(progress_info)
        
        layout.addWidget(progress_group)
        
        # 状态指示器演示
        status_group = QGroupBox("状态指示器")
        status_layout = QVBoxLayout(status_group)
        
        indicators_layout = QHBoxLayout()
        
        self.status_indicators = {}
        statuses = [
            ("waiting", "等待中"),
            ("downloading", "下载中"),
            ("completed", "已完成"),
            ("paused", "已暂停"),
            ("error", "出错")
        ]
        
        for status, label in statuses:
            indicator_layout = QVBoxLayout()
            
            indicator = StatusIndicator()
            indicator.set_status(status)
            self.status_indicators[status] = indicator
            
            indicator_layout.addWidget(indicator, alignment=Qt.AlignCenter)
            indicator_layout.addWidget(QLabel(label), alignment=Qt.AlignCenter)
            
            indicators_layout.addLayout(indicator_layout)
            
        status_layout.addLayout(indicators_layout)
        
        status_info = QLabel("不同状态的动画效果")
        status_info.setStyleSheet("color: #8e8e93; font-size: 12px;")
        status_layout.addWidget(status_info)
        
        layout.addWidget(status_group)
        
        # 3D Touch菜单演示
        menu_group = QGroupBox("3D Touch菜单")
        menu_layout = QVBoxLayout(menu_group)
        
        menu_demo_btn = QPushButton("右键显示菜单")
        menu_demo_btn.setContextMenuPolicy(Qt.CustomContextMenu)
        menu_demo_btn.customContextMenuRequested.connect(self.show_demo_menu)
        menu_demo_btn.setStyleSheet("""
            QPushButton {
                background-color: #34c759;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #248a3d;
            }
        """)
        menu_layout.addWidget(menu_demo_btn)
        
        menu_info = QLabel("右键点击按钮查看3D Touch式菜单")
        menu_info.setStyleSheet("color: #8e8e93; font-size: 12px;")
        menu_layout.addWidget(menu_info)
        
        layout.addWidget(menu_group)
        
        layout.addStretch()
        return group
        
    def setup_demo_data(self):
        """设置演示数据"""
        demo_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.bilibili.com/video/BV1xx411c7mu",
            "https://www.tiktok.com/@user/video/123456789"
        ]
        
        demo_metadata = [
            {
                'title': 'Rick Astley - Never Gonna Give You Up',
                'author': 'Rick Astley',
                'thumbnail': 'https://example.com/thumb1.jpg'
            },
            {
                'title': '【技术分享】Python GUI开发教程',
                'author': '技术UP主',
                'thumbnail': 'https://example.com/thumb2.jpg'
            },
            {
                'title': 'Funny Cat Video #shorts',
                'author': '@catlovers',
                'thumbnail': 'https://example.com/thumb3.jpg'
            }
        ]
        
        # 添加一些演示任务
        for url, metadata in zip(demo_urls, demo_metadata):
            task_id = self.download_list.add_task(url, metadata)
            
        # 设置不同的状态
        task_ids = list(self.download_list.tasks.keys())
        if len(task_ids) >= 3:
            self.download_list.update_task_status(task_ids[0], "completed")
            self.download_list.update_task_progress(task_ids[0], 100.0)
            
            self.download_list.update_task_status(task_ids[1], "downloading")
            self.download_list.update_task_progress(task_ids[1], 45.0, "2.5 MB/s")
            
            self.download_list.update_task_status(task_ids[2], "paused")
            self.download_list.update_task_progress(task_ids[2], 23.0)
            
    def setup_timers(self):
        """设置定时器"""
        # 进度条动画定时器
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_demo_progress)
        self.progress_timer.start(200)  # 5fps
        
        # 状态栏更新定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status_bar)
        self.status_timer.start(1000)  # 1fps
        
    def update_demo_progress(self):
        """更新演示进度条"""
        # 模拟随机速度变化
        speed = random.uniform(0.5, 10.0)  # 0.5-10 MB/s
        self.demo_progress.add_speed_point(speed)
        
        # 更新进度值
        current_value = self.demo_progress.value()
        new_value = (current_value + 1) % 101
        self.demo_progress.setValue(new_value)
        
    def update_status_bar(self):
        """更新状态栏"""
        active_tasks = len([t for t in self.download_list.tasks.values() 
                           if t['card'].status == "downloading"])
        total_tasks = len(self.download_list.tasks)
        
        speed = f"{random.uniform(1.0, 5.0):.1f} MB/s"
        remaining_time = f"{random.randint(1, 59):02d}:{random.randint(10, 59):02d}"
        
        self.status_bar.update_download_stats(speed, remaining_time, active_tasks)
        self.status_bar.set_total_progress(
            len([t for t in self.download_list.tasks.values() 
                if t['card'].status == "completed"]),
            total_tasks
        )
        
    def on_url_submitted(self, url):
        """处理URL提交"""
        self.task_counter += 1
        metadata = {
            'title': f'用户添加的视频 #{self.task_counter}',
            'author': '用户',
            'thumbnail': 'https://example.com/user_thumb.jpg'
        }
        
        task_id = self.download_list.add_task(url, metadata)
        self.status_bar.show_message(f"已添加新任务: {metadata['title']}")
        
    def on_task_action(self, task_id, action):
        """处理任务动作"""
        if action == "start":
            self.download_list.update_task_status(task_id, "downloading")
            self.status_bar.show_message("任务已开始")
        elif action == "pause":
            self.download_list.update_task_status(task_id, "paused")
            self.status_bar.show_message("任务已暂停")
        elif action == "resume":
            self.download_list.update_task_status(task_id, "downloading")
            self.status_bar.show_message("任务已继续")
        elif action == "delete":
            self.download_list.remove_task(task_id)
            self.status_bar.show_message("任务已删除")
            
    def add_demo_task(self):
        """添加演示任务"""
        demo_urls = [
            "https://www.instagram.com/p/demo123",
            "https://twitter.com/user/status/456789",
            "https://www.pixiv.net/artworks/987654"
        ]
        
        demo_titles = [
            "Instagram精美图片合集",
            "Twitter热门视频",
            "Pixiv高清插画作品"
        ]
        
        url = random.choice(demo_urls)
        title = random.choice(demo_titles)
        
        metadata = {
            'title': title,
            'author': '演示作者',
            'thumbnail': 'https://example.com/demo_thumb.jpg'
        }
        
        task_id = self.download_list.add_task(url, metadata)
        
        # 随机设置状态
        statuses = ["waiting", "downloading", "paused"]
        status = random.choice(statuses)
        self.download_list.update_task_status(task_id, status)
        
        if status == "downloading":
            progress = random.uniform(10, 90)
            speed = f"{random.uniform(0.5, 5.0):.1f} MB/s"
            self.download_list.update_task_progress(task_id, progress, speed)
            
    def clear_tasks(self):
        """清空任务列表"""
        task_ids = list(self.download_list.tasks.keys())
        for task_id in task_ids:
            self.download_list.remove_task(task_id)
        self.status_bar.show_message("已清空所有任务")
        
    def show_demo_menu(self, pos):
        """显示演示菜单"""
        menu = TouchContextMenu(self)
        
        # 任务控制组
        control_group = menu.add_group("任务控制")
        control_group.add_action("▶", "开始下载", lambda: self.status_bar.show_message("开始下载"))
        control_group.add_action("⏸", "暂停下载", lambda: self.status_bar.show_message("暂停下载"))
        control_group.add_action("🔄", "重新开始", lambda: self.status_bar.show_message("重新开始"))
        
        # 批量操作组
        batch_group = menu.add_group("批量操作")
        batch_group.add_action("▶▶", "开始全部", lambda: self.status_bar.show_message("开始全部任务"))
        batch_group.add_action("⏸⏸", "暂停全部", lambda: self.status_bar.show_message("暂停全部任务"))
        
        # 文件操作组
        file_group = menu.add_group("文件操作")
        file_group.add_action("📄", "打开文件", lambda: self.status_bar.show_message("打开文件"))
        file_group.add_action("📁", "打开文件夹", lambda: self.status_bar.show_message("打开文件夹"))
        
        # 列表管理组
        manage_group = menu.add_group("列表管理")
        manage_group.add_action("🗑", "删除任务", lambda: self.status_bar.show_message("删除任务"))
        manage_group.add_action("✅", "标记完成", lambda: self.status_bar.show_message("标记完成"))
        
        # 显示菜单
        sender = self.sender()
        global_pos = sender.mapToGlobal(pos)
        menu.exec(global_pos)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用属性
    app.setApplicationName("多平台视频下载器")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Demo")
    
    # 创建并显示演示窗口
    demo = UIComponentsDemo()
    demo.show()
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()