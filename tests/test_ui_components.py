"""
测试UI组件功能
"""
import sys
import pytest
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import QTimer
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt

# 导入UI组件
from app.ui.components.url_input import URLInputWidget
from app.ui.components.download_task_card import DownloadTaskCard, MagicProgressBar, StatusIndicator
from app.ui.components.download_list import DownloadListWidget, DraggableTaskList
from app.ui.components.status_bar import CustomStatusBar
from app.ui.components.touch_context_menu import TouchContextMenu


class TestUIComponents:
    """UI组件测试类"""
    
    @pytest.fixture(autouse=True)
    def setup_app(self):
        """设置测试应用"""
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        else:
            self.app = QApplication.instance()
        yield
        
    def test_url_input_widget(self):
        """测试URL输入组件"""
        widget = URLInputWidget()
        
        # 测试基本属性
        assert widget.objectName() == "urlInputWidget"
        assert widget.height() == 80
        
        # 测试设置URL
        test_url = "https://www.youtube.com/watch?v=test"
        widget.set_url(test_url)
        assert widget.url_input.text() == test_url
        
        # 测试清空
        widget.clear()
        assert widget.url_input.text() == ""
        
    def test_magic_progress_bar(self):
        """测试魔法进度条"""
        progress_bar = MagicProgressBar()
        
        # 测试基本属性
        assert progress_bar.height() == 8
        assert not progress_bar.isTextVisible()
        
        # 测试添加速度点
        progress_bar.add_speed_point(50.0)
        assert len(progress_bar.speed_history) == 1
        assert progress_bar.speed_history[0] == 50.0
        
        # 测试最大速度更新
        progress_bar.add_speed_point(100.0)
        assert progress_bar.max_speed >= 100.0
        
        # 测试历史记录限制
        for i in range(150):
            progress_bar.add_speed_point(float(i))
        assert len(progress_bar.speed_history) <= 100
        
    def test_status_indicator(self):
        """测试状态指示器"""
        indicator = StatusIndicator()
        
        # 测试基本属性
        assert indicator.width() == 12
        assert indicator.height() == 12
        assert indicator.status == "waiting"
        
        # 测试状态设置
        indicator.set_status("downloading")
        assert indicator.status == "downloading"
        assert indicator.animation_timer.isActive()
        
        # 测试动画停止
        indicator.set_status("completed")
        assert indicator.status == "completed"
        assert not indicator.animation_timer.isActive()
        
    def test_download_task_card(self):
        """测试下载任务卡片"""
        test_url = "https://www.youtube.com/watch?v=test"
        test_metadata = {
            'title': '测试视频',
            'author': '测试作者',
            'thumbnail': 'https://example.com/thumb.jpg'
        }
        
        card = DownloadTaskCard(test_url, test_metadata)
        
        # 测试基本属性
        assert card.url == test_url
        assert card.metadata == test_metadata
        assert card.status == "waiting"
        assert card.progress == 0.0
        
        # 测试进度更新
        card.update_progress(50.0, "1.5 MB/s")
        assert card.progress == 50.0
        assert card.progress_bar.value() == 50
        
        # 测试状态更新
        card.update_status("downloading")
        assert card.status == "downloading"
        assert card.status_indicator.status == "downloading"
        
        # 测试元数据更新
        new_metadata = {'title': '新标题', 'author': '新作者'}
        card.update_metadata(new_metadata)
        assert card.metadata['title'] == '新标题'
        assert card.title_label.text() == '新标题'
        
    def test_draggable_task_list(self):
        """测试可拖拽任务列表"""
        task_list = DraggableTaskList()
        
        # 测试基本属性
        from PySide6.QtWidgets import QListWidget
        assert task_list.dragDropMode() == QListWidget.InternalMove
        assert task_list.defaultDropAction() == Qt.MoveAction
        assert task_list.dragEnabled()
        assert task_list.acceptDrops()
        
        # 测试空状态
        assert task_list.count() == 0
        
    def test_download_list_widget(self):
        """测试下载列表组件"""
        list_widget = DownloadListWidget()
        
        # 测试基本属性
        assert list_widget.objectName() == "downloadListWidget"
        assert len(list_widget.tasks) == 0
        
        # 测试添加任务
        test_url = "https://www.youtube.com/watch?v=test"
        task_id = list_widget.add_task(test_url)
        
        assert len(list_widget.tasks) == 1
        assert task_id in list_widget.tasks
        assert list_widget.get_task_count() == 1
        
        # 测试更新任务进度
        list_widget.update_task_progress(task_id, 75.0, "2.0 MB/s")
        task_card = list_widget.tasks[task_id]['card']
        assert task_card.progress == 75.0
        
        # 测试更新任务状态
        list_widget.update_task_status(task_id, "completed")
        assert task_card.status == "completed"
        
        # 测试移除任务
        list_widget.remove_task(task_id)
        assert len(list_widget.tasks) == 0
        assert list_widget.get_task_count() == 0
        
    def test_custom_status_bar(self):
        """测试自定义状态栏"""
        status_bar = CustomStatusBar()
        
        # 测试基本属性
        assert status_bar.objectName() == "customStatusBar"
        assert status_bar.height() == 32
        
        # 测试状态更新
        status_bar.update_status("测试消息", 50)
        assert status_bar.total_progress_label.text() == "测试消息"
        
        # 测试下载统计更新
        status_bar.update_download_stats("1.5 MB/s", "05:30", 3)
        assert status_bar.speed_label.text() == "1.5 MB/s"
        assert status_bar.time_label.text() == "05:30"
        assert status_bar.active_tasks_label.text() == "3 个任务"
        
        # 测试总进度设置
        status_bar.set_total_progress(7, 10)
        expected_text = "总进度: 7/10 (70%)"
        assert status_bar.total_progress_label.text() == expected_text
        
    def test_touch_context_menu(self):
        """测试3D Touch上下文菜单"""
        menu = TouchContextMenu()
        
        # 测试基本属性
        assert menu.objectName() == "touchContextMenu"
        assert len(menu.groups) == 0
        
        # 测试添加菜单组
        control_group = menu.add_group("任务控制")
        assert len(menu.groups) == 1
        assert control_group.title == "任务控制"
        
        # 测试添加菜单项
        action_called = False
        def test_callback():
            nonlocal action_called
            action_called = True
            
        control_group.add_action("▶", "开始", test_callback)
        assert len(control_group.actions) == 1
        
        # 测试多个组
        file_group = menu.add_group("文件操作")
        assert len(menu.groups) == 2


class TestUIIntegration:
    """UI集成测试"""
    
    @pytest.fixture(autouse=True)
    def setup_app(self):
        """设置测试应用"""
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        else:
            self.app = QApplication.instance()
        yield
        
    def test_complete_ui_workflow(self):
        """测试完整的UI工作流程"""
        # 创建主窗口
        main_window = QMainWindow()
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        # 添加URL输入组件
        url_input = URLInputWidget()
        layout.addWidget(url_input)
        
        # 添加下载列表组件
        download_list = DownloadListWidget()
        layout.addWidget(download_list)
        
        # 添加状态栏
        status_bar = CustomStatusBar()
        main_window.setStatusBar(status_bar)
        
        main_window.setCentralWidget(central_widget)
        
        # 测试URL提交工作流程
        test_url = "https://www.youtube.com/watch?v=test"
        url_submitted = False
        
        def on_url_submitted(url):
            nonlocal url_submitted
            url_submitted = True
            # 添加到下载列表
            task_id = download_list.add_task(url)
            # 更新状态栏
            status_bar.update_status("已添加新任务")
            
        url_input.url_submitted.connect(on_url_submitted)
        
        # 模拟URL提交
        url_input.set_url(test_url)
        url_input.submit_url()
        
        assert url_submitted
        assert download_list.get_task_count() == 1
        
        # 测试任务操作工作流程
        task_action_received = False
        
        def on_task_action(task_id, action):
            nonlocal task_action_received
            task_action_received = True
            if action == "start":
                download_list.update_task_status(task_id, "downloading")
                status_bar.update_download_stats("1.0 MB/s", "10:00", 1)
                
        download_list.task_action.connect(on_task_action)
        
        # 模拟任务开始
        task_ids = list(download_list.tasks.keys())
        if task_ids:
            download_list.task_action.emit(task_ids[0], "start")
            
        assert task_action_received


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])