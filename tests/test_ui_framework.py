#!/usr/bin/env python3
"""
macOS风格UI框架测试
"""
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from app.ui.main_window import MacOSMainWindow
from app.ui.styles.theme_manager import ThemeManager
from app.ui.components import (
    URLInputWidget, DownloadListWidget, DownloadTaskCard,
    MagicProgressBar, StatusIndicator, CustomStatusBar
)


@pytest.fixture(scope="session")
def qapp():
    """创建QApplication实例"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    # 不要退出应用，让其他测试继续使用


class TestThemeManager:
    """主题管理器测试"""
    
    def test_theme_manager_initialization(self):
        """测试主题管理器初始化"""
        theme_manager = ThemeManager()
        assert theme_manager.current_theme in ['light', 'dark']
        
    def test_theme_switching(self):
        """测试主题切换"""
        theme_manager = ThemeManager()
        original_theme = theme_manager.current_theme
        
        # 切换主题
        new_theme = "dark" if original_theme == "light" else "light"
        theme_manager.set_theme(new_theme)
        assert theme_manager.current_theme == new_theme
        
    def test_stylesheet_generation(self):
        """测试样式表生成"""
        theme_manager = ThemeManager()
        stylesheet = theme_manager.get_stylesheet()
        assert isinstance(stylesheet, str)
        assert len(stylesheet) > 0
        
    def test_theme_colors(self):
        """测试主题颜色配置"""
        theme_manager = ThemeManager()
        
        # 测试明亮主题颜色
        theme_manager.set_theme("light")
        light_colors = theme_manager.get_theme_colors()
        assert 'background' in light_colors
        assert 'primary' in light_colors
        
        # 测试暗黑主题颜色
        theme_manager.set_theme("dark")
        dark_colors = theme_manager.get_theme_colors()
        assert 'background' in dark_colors
        assert 'primary' in dark_colors
        
        # 确保两个主题的颜色不同
        assert light_colors['background'] != dark_colors['background']


class TestUIComponents:
    """UI组件测试"""
    
    def test_url_input_widget(self, qapp):
        """测试URL输入组件"""
        widget = URLInputWidget()
        
        # 测试基本属性
        assert widget.url_input is not None
        assert widget.add_button is not None
        assert widget.paste_button is not None
        
        # 测试URL设置和清空
        test_url = "https://www.youtube.com/watch?v=test"
        widget.set_url(test_url)
        assert widget.url_input.text() == test_url
        
        widget.clear()
        assert widget.url_input.text() == ""
        
    def test_status_indicator(self, qapp):
        """测试状态指示器"""
        indicator = StatusIndicator()
        
        # 测试状态设置
        test_statuses = ["waiting", "downloading", "completed", "paused", "error"]
        for status in test_statuses:
            indicator.set_status(status)
            assert indicator.status == status
            
    def test_magic_progress_bar(self, qapp):
        """测试魔法进度条"""
        progress_bar = MagicProgressBar()
        
        # 测试基本属性
        assert progress_bar.height() == 6
        assert not progress_bar.isTextVisible()
        
        # 测试速度点添加
        progress_bar.add_speed_point(50.0)
        assert len(progress_bar.speed_history) == 1
        assert progress_bar.speed_history[0] == 50.0
        
    def test_download_task_card(self, qapp):
        """测试下载任务卡片"""
        test_url = "https://www.youtube.com/watch?v=test"
        test_metadata = {
            'title': 'Test Video',
            'author': 'Test Author',
            'duration': 120
        }
        
        card = DownloadTaskCard(test_url, test_metadata)
        
        # 测试基本属性
        assert card.url == test_url
        assert card.metadata == test_metadata
        assert card.status == "waiting"
        assert card.progress == 0.0
        
        # 测试进度更新
        card.update_progress(50.0, "10.5 MB/s")
        assert card.progress == 50.0
        
        # 测试状态更新
        card.update_status("downloading")
        assert card.status == "downloading"
        
        # 测试元数据更新
        new_metadata = {'title': 'Updated Title'}
        card.update_metadata(new_metadata)
        assert card.metadata['title'] == 'Updated Title'
        
    def test_download_list_widget(self, qapp):
        """测试下载列表组件"""
        list_widget = DownloadListWidget()
        
        # 测试初始状态
        assert list_widget.get_task_count() == 0
        
        # 测试添加任务
        test_url = "https://www.youtube.com/watch?v=test"
        task_id = list_widget.add_task(test_url)
        assert list_widget.get_task_count() == 1
        assert task_id in list_widget.tasks
        
        # 测试更新任务
        list_widget.update_task_progress(task_id, 75.0, "15.2 MB/s")
        list_widget.update_task_status(task_id, "downloading")
        
        # 测试移除任务
        list_widget.remove_task(task_id)
        assert list_widget.get_task_count() == 0
        assert task_id not in list_widget.tasks
        
    def test_custom_status_bar(self, qapp):
        """测试自定义状态栏"""
        status_bar = CustomStatusBar()
        
        # 测试基本属性
        assert status_bar.height() == 32
        
        # 测试状态更新
        status_bar.update_status("测试消息", 50)
        status_bar.update_download_stats("10.5 MB/s", "05:30", 3)
        status_bar.set_total_progress(5, 10)
        
        # 测试消息显示
        status_bar.show_message("临时消息", 1000)


class TestMainWindow:
    """主窗口测试"""
    
    def test_main_window_initialization(self, qapp):
        """测试主窗口初始化"""
        window = MacOSMainWindow()
        
        # 测试基本属性
        assert window.windowTitle() == "多平台视频下载器"
        assert window.minimumSize().width() == 900
        assert window.minimumSize().height() == 600
        
        # 测试组件存在
        assert window.url_input is not None
        assert window.download_list is not None
        assert window.status_bar is not None
        assert window.theme_manager is not None
        
    def test_theme_switching(self, qapp):
        """测试主题切换"""
        window = MacOSMainWindow()
        original_theme = window.theme_manager.current_theme
        
        # 切换主题
        window.toggle_theme()
        new_theme = window.theme_manager.current_theme
        assert new_theme != original_theme
        
    def test_add_download_task(self, qapp):
        """测试添加下载任务"""
        window = MacOSMainWindow()
        
        test_url = "https://www.youtube.com/watch?v=test"
        test_metadata = {
            'title': 'Test Video',
            'author': 'Test Author'
        }
        
        # 添加任务
        window.add_download_task(test_url, test_metadata)
        assert window.download_list.get_task_count() == 1
        
    def test_status_update(self, qapp):
        """测试状态更新"""
        window = MacOSMainWindow()
        
        # 更新状态
        window.update_status("测试状态", 75)
        
        # 验证状态栏更新
        # 这里可以添加更多具体的验证逻辑


class TestUIIntegration:
    """UI集成测试"""
    
    def test_url_submission_flow(self, qapp):
        """测试URL提交流程"""
        window = MacOSMainWindow()
        
        # 模拟URL输入和提交
        test_url = "https://www.youtube.com/watch?v=integration_test"
        window.url_input.set_url(test_url)
        
        # 测试信号连接是否正确
        signal_received = []
        def capture_signal(url):
            signal_received.append(url)
            
        window.url_added.connect(capture_signal)
        window.url_input.url_submitted.emit(test_url)
        
        # 验证信号是否被正确传递
        assert len(signal_received) == 1
        assert signal_received[0] == test_url
            
    def test_theme_consistency(self, qapp):
        """测试主题一致性"""
        window = MacOSMainWindow()
        
        # 测试两个主题的样式表都能正常生成
        for theme in ['light', 'dark']:
            window.theme_manager.set_theme(theme)
            stylesheet = window.theme_manager.get_stylesheet()
            assert len(stylesheet) > 0
            
            # 应用样式表不应该出错
            window.apply_theme()


if __name__ == '__main__':
    # 运行测试
    pytest.main([__file__, '-v'])