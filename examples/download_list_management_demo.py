#!/usr/bin/env python3
"""
下载列表管理功能演示
演示拖拽排序、分组筛选、批量操作、虚拟列表优化、搜索过滤等功能
"""

import sys
import os
import random
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, QTimer
from app.ui.components.download_list import DownloadListWidget


class DownloadListDemo(QMainWindow):
    """下载列表管理演示窗口"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_demo_data()
        
    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("下载列表管理功能演示")
        self.setGeometry(100, 100, 1200, 800)
        
        # 中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 控制按钮区域
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(20, 10, 20, 10)
        
        # 添加任务按钮
        add_task_btn = QPushButton("添加随机任务")
        add_task_btn.clicked.connect(self.add_random_task)
        control_layout.addWidget(add_task_btn)
        
        # 添加多个任务按钮
        add_multiple_btn = QPushButton("添加10个任务")
        add_multiple_btn.clicked.connect(self.add_multiple_tasks)
        control_layout.addWidget(add_multiple_btn)
        
        # 模拟下载按钮
        simulate_btn = QPushButton("模拟下载进度")
        simulate_btn.clicked.connect(self.simulate_downloads)
        control_layout.addWidget(simulate_btn)
        
        # 清空任务按钮
        clear_btn = QPushButton("清空所有任务")
        clear_btn.clicked.connect(self.clear_all_tasks)
        control_layout.addWidget(clear_btn)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # 下载列表组件
        self.download_list = DownloadListWidget()
        self.download_list.task_selected.connect(self.on_task_selected)
        self.download_list.task_action.connect(self.on_task_action)
        layout.addWidget(self.download_list)
        
        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f7;
            }
            QPushButton {
                padding: 8px 16px;
                border: 1px solid rgba(0, 122, 255, 0.3);
                border-radius: 8px;
                background-color: rgba(0, 122, 255, 0.1);
                color: #007aff;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(0, 122, 255, 0.2);
            }
            QPushButton:pressed {
                background-color: rgba(0, 122, 255, 0.3);
            }
        """)
        
    def setup_demo_data(self):
        """设置演示数据"""
        self.demo_urls = [
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", {
                'title': 'Rick Astley - Never Gonna Give You Up',
                'author': 'Rick Astley',
                'platform': 'YouTube'
            }),
            ("https://www.bilibili.com/video/BV1xx411c7mD", {
                'title': '【官方MV】洛天依 言和《普通DISCO》',
                'author': '洛天依官方',
                'platform': 'B站'
            }),
            ("https://www.tiktok.com/@username/video/123456789", {
                'title': '搞笑短视频合集',
                'author': '@funny_user',
                'platform': '抖音'
            }),
            ("https://www.instagram.com/p/ABC123/", {
                'title': 'Beautiful sunset photo',
                'author': '@photographer',
                'platform': 'Instagram'
            }),
            ("https://example.com/video/sample1", {
                'title': '示例视频1 - 高清画质',
                'author': '示例作者1',
                'platform': '其他'
            }),
            ("https://example.com/video/sample2", {
                'title': '示例视频2 - 4K超清',
                'author': '示例作者2',
                'platform': '其他'
            })
        ]
        
        self.task_ids = []
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)
        
    def add_random_task(self):
        """添加随机任务"""
        url, metadata = random.choice(self.demo_urls)
        
        # 随机修改标题以避免重复
        metadata = metadata.copy()
        metadata['title'] += f" #{random.randint(1, 999)}"
        
        task_id = self.download_list.add_task(url, metadata)
        self.task_ids.append(task_id)
        
        print(f"添加任务: {task_id} - {metadata['title']}")
        
    def add_multiple_tasks(self):
        """添加多个任务"""
        for i in range(10):
            self.add_random_task()
            
    def simulate_downloads(self):
        """模拟下载进度"""
        if not self.progress_timer.isActive():
            self.progress_timer.start(500)  # 每500ms更新一次
            print("开始模拟下载进度...")
        else:
            self.progress_timer.stop()
            print("停止模拟下载进度")
            
    def update_progress(self):
        """更新下载进度"""
        for task_id in self.task_ids:
            # 随机更新状态和进度
            if random.random() < 0.1:  # 10%概率改变状态
                statuses = ['waiting', 'downloading', 'paused', 'completed', 'error']
                new_status = random.choice(statuses)
                self.download_list.update_task_status(task_id, new_status)
                
            if random.random() < 0.3:  # 30%概率更新进度
                progress = random.uniform(0, 100)
                speed = f"{random.uniform(0.5, 10.0):.1f} MB/s"
                self.download_list.update_task_progress(task_id, progress, speed)
                
    def clear_all_tasks(self):
        """清空所有任务"""
        for task_id in list(self.task_ids):
            self.download_list.remove_task(task_id)
        self.task_ids.clear()
        print("已清空所有任务")
        
    def on_task_selected(self, task_id: str):
        """任务选中事件"""
        print(f"任务被选中: {task_id}")
        
    def on_task_action(self, task_id: str, action: str):
        """任务操作事件"""
        print(f"任务操作: {task_id} -> {action}")
        
        # 模拟处理不同的操作
        if action == "start":
            self.download_list.update_task_status(task_id, "downloading")
        elif action == "pause":
            self.download_list.update_task_status(task_id, "paused")
        elif action == "resume":
            self.download_list.update_task_status(task_id, "downloading")
        elif action == "restart":
            self.download_list.update_task_status(task_id, "waiting")
            self.download_list.update_task_progress(task_id, 0.0, "")
        elif action == "delete":
            self.download_list.remove_task(task_id)
            if task_id in self.task_ids:
                self.task_ids.remove(task_id)
        elif action in ["start_all", "pause_all"]:
            # 批量操作
            for tid in self.task_ids:
                if action == "start_all":
                    self.download_list.update_task_status(tid, "downloading")
                elif action == "pause_all":
                    self.download_list.update_task_status(tid, "paused")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序属性
    app.setApplicationName("下载列表管理演示")
    app.setApplicationVersion("1.0.0")
    
    # 创建并显示主窗口
    window = DownloadListDemo()
    window.show()
    
    # 添加一些初始任务用于演示
    for i in range(5):
        window.add_random_task()
    
    print("=== 下载列表管理功能演示 ===")
    print("功能说明:")
    print("1. 拖拽排序: 直接拖拽任务卡片可以重新排序")
    print("2. 搜索筛选: 在搜索框中输入关键词筛选任务")
    print("3. 状态筛选: 使用状态下拉框筛选不同状态的任务")
    print("4. 平台筛选: 使用平台下拉框筛选不同平台的任务")
    print("5. 任务分组: 选择不同的分组方式查看任务")
    print("6. 批量操作: 使用全选和批量操作按钮管理多个任务")
    print("7. 右键菜单: 右键点击任务卡片查看更多操作")
    print("8. 虚拟列表: 支持大量任务的高性能显示")
    print()
    print("操作提示:")
    print("- 点击'添加随机任务'添加单个任务")
    print("- 点击'添加10个任务'快速添加多个任务测试性能")
    print("- 点击'模拟下载进度'开始/停止进度模拟")
    print("- 尝试不同的筛选和分组选项")
    print("- 使用批量操作管理多个任务")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()