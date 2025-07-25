"""
设置对话框测试
"""
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ui.dialogs.settings_dialog import SettingsDialog, ProxyTestThread
from app.core.config import config_manager


class TestSettingsDialog:
    """设置对话框测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试设置"""
        if not QApplication.instance():
            self.app = QApplication([])
        else:
            self.app = QApplication.instance()
        
        self.parent = QWidget()
        self.dialog = SettingsDialog(self.parent)
        
    def test_dialog_initialization(self):
        """测试对话框初始化"""
        assert self.dialog.windowTitle() == "设置"
        assert self.dialog.isModal()
        assert self.dialog.minimumSize().width() == 700
        assert self.dialog.minimumSize().height() == 500
        
    def test_tab_widget_creation(self):
        """测试标签页创建"""
        tab_widget = self.dialog.tab_widget
        assert tab_widget.count() == 5
        
        # 检查标签页标题
        expected_tabs = ["通用", "下载", "网络", "外观", "高级"]
        for i, expected_title in enumerate(expected_tabs):
            assert tab_widget.tabText(i) == expected_title
            
    def test_general_tab_components(self):
        """测试通用设置标签页组件"""
        # 检查复选框
        assert hasattr(self.dialog, 'startup_check')
        assert hasattr(self.dialog, 'tray_check')
        assert hasattr(self.dialog, 'close_to_tray_check')
        assert hasattr(self.dialog, 'auto_update_check')
        
        # 检查下拉框
        assert hasattr(self.dialog, 'language_combo')
        assert self.dialog.language_combo.count() == 3
        
    def test_download_tab_components(self):
        """测试下载设置标签页组件"""
        # 检查路径设置
        assert hasattr(self.dialog, 'download_path_edit')
        assert hasattr(self.dialog, 'browse_path_btn')
        
        # 检查文件命名模板
        assert hasattr(self.dialog, 'naming_template_edit')
        assert hasattr(self.dialog, 'template_preview_label')
        assert hasattr(self.dialog, 'template_help_btn')
        
        # 检查下载选项
        assert hasattr(self.dialog, 'concurrent_spin')
        assert hasattr(self.dialog, 'quality_combo')
        assert hasattr(self.dialog, 'format_combo')
        
    def test_network_tab_components(self):
        """测试网络设置标签页组件"""
        # 检查连接设置
        assert hasattr(self.dialog, 'connection_timeout_spin')
        assert hasattr(self.dialog, 'read_timeout_spin')
        assert hasattr(self.dialog, 'retry_spin')
        
        # 检查代理设置
        assert hasattr(self.dialog, 'proxy_group_btn')
        assert hasattr(self.dialog, 'no_proxy_radio')
        assert hasattr(self.dialog, 'http_proxy_radio')
        assert hasattr(self.dialog, 'socks5_proxy_radio')
        assert hasattr(self.dialog, 'proxy_host_edit')
        assert hasattr(self.dialog, 'proxy_port_spin')
        assert hasattr(self.dialog, 'proxy_test_btn')
        
    def test_appearance_tab_components(self):
        """测试外观设置标签页组件"""
        # 检查主题设置
        assert hasattr(self.dialog, 'theme_group_btn')
        assert hasattr(self.dialog, 'light_theme_radio')
        assert hasattr(self.dialog, 'dark_theme_radio')
        assert hasattr(self.dialog, 'auto_theme_radio')
        
        # 检查界面设置
        assert hasattr(self.dialog, 'font_size_slider')
        assert hasattr(self.dialog, 'ui_scale_slider')
        assert hasattr(self.dialog, 'animation_check')
        assert hasattr(self.dialog, 'transparency_check')
        
    def test_advanced_tab_components(self):
        """测试高级设置标签页组件"""
        # 检查性能设置
        assert hasattr(self.dialog, 'memory_cache_spin')
        assert hasattr(self.dialog, 'disk_cache_spin')
        assert hasattr(self.dialog, 'hardware_accel_check')
        
        # 检查数据管理
        assert hasattr(self.dialog, 'export_config_btn')
        assert hasattr(self.dialog, 'import_config_btn')
        assert hasattr(self.dialog, 'clear_history_btn')
        assert hasattr(self.dialog, 'clear_cache_btn')
        
    def test_load_settings(self):
        """测试设置加载"""
        # 模拟配置
        with patch.object(config_manager, 'config') as mock_config:
            mock_config.download_path = "/test/path"
            mock_config.max_concurrent_downloads = 5
            mock_config.connection_timeout = 45
            mock_config.read_timeout = 90
            mock_config.max_retries = 2
            mock_config.theme = "dark"
            
            self.dialog.load_settings()
            
            assert self.dialog.download_path_edit.text() == "/test/path"
            assert self.dialog.concurrent_spin.value() == 5
            assert self.dialog.connection_timeout_spin.value() == 45
            assert self.dialog.read_timeout_spin.value() == 90
            assert self.dialog.retry_spin.value() == 2
            assert self.dialog.dark_theme_radio.isChecked()
            
    def test_get_current_settings(self):
        """测试获取当前设置"""
        # 设置一些值
        self.dialog.download_path_edit.setText("/custom/path")
        self.dialog.concurrent_spin.setValue(4)
        self.dialog.dark_theme_radio.setChecked(True)
        self.dialog.proxy_host_edit.setText("proxy.example.com")
        self.dialog.proxy_port_spin.setValue(8080)
        self.dialog.http_proxy_radio.setChecked(True)
        
        settings = self.dialog.get_current_settings()
        
        assert settings['download_path'] == "/custom/path"
        assert settings['max_concurrent_downloads'] == 4
        assert settings['theme'] == 'dark'
        assert settings['proxy_host'] == "proxy.example.com"
        assert settings['proxy_port'] == 8080
        assert settings['proxy_type'] == 'http'
        
    def test_template_preview_update(self):
        """测试模板预览更新"""
        # 设置模板
        self.dialog.naming_template_edit.setText("{title} - {author}")
        self.dialog.update_template_preview()
        
        preview_text = self.dialog.template_preview_label.text()
        assert "示例视频标题 - 示例作者.mp4" == preview_text
        
        # 测试错误模板
        self.dialog.naming_template_edit.setText("{invalid_var}")
        self.dialog.update_template_preview()
        
        preview_text = self.dialog.template_preview_label.text()
        assert "错误" in preview_text
        
    def test_proxy_type_change(self):
        """测试代理类型改变"""
        # 初始状态 - 无代理
        assert not self.dialog.proxy_host_edit.isEnabled()
        assert not self.dialog.proxy_port_spin.isEnabled()
        assert not self.dialog.proxy_test_btn.isEnabled()
        
        # 启用HTTP代理
        self.dialog.http_proxy_radio.setChecked(True)
        self.dialog.on_proxy_type_changed(self.dialog.http_proxy_radio, True)
        
        assert self.dialog.proxy_host_edit.isEnabled()
        assert self.dialog.proxy_port_spin.isEnabled()
        assert self.dialog.proxy_test_btn.isEnabled()
        
    def test_browse_download_path(self):
        """测试浏览下载路径"""
        with patch('PySide6.QtWidgets.QFileDialog.getExistingDirectory') as mock_dialog:
            mock_dialog.return_value = "/new/download/path"
            
            self.dialog.browse_download_path()
            
            assert self.dialog.download_path_edit.text() == "/new/download/path"
            
    def test_slider_value_updates(self):
        """测试滑块值更新"""
        # 测试字体大小滑块
        self.dialog.font_size_slider.setValue(14)
        # 模拟信号触发
        self.dialog.font_size_slider.valueChanged.emit(14)
        assert self.dialog.font_size_value.text() == "14"
        
        # 测试界面缩放滑块
        self.dialog.ui_scale_slider.setValue(120)
        # 模拟信号触发
        self.dialog.ui_scale_slider.valueChanged.emit(120)
        assert self.dialog.ui_scale_value.text() == "120%"
        
    def test_speed_limit_toggle(self):
        """测试速度限制切换"""
        # 初始状态
        assert not self.dialog.speed_limit_spin.isEnabled()
        
        # 启用速度限制
        self.dialog.speed_limit_check.setChecked(True)
        self.dialog.speed_limit_check.toggled.emit(True)
        
        assert self.dialog.speed_limit_spin.isEnabled()
        
    @patch('app.ui.dialogs.settings_dialog.QMessageBox.question')
    def test_reset_settings(self, mock_question):
        """测试重置设置"""
        mock_question.return_value = Mock()
        mock_question.return_value = 16384  # QMessageBox.Yes
        
        with patch.object(config_manager, 'reset_to_defaults') as mock_reset:
            with patch.object(self.dialog, 'load_settings') as mock_load:
                self.dialog.reset_settings()
                
                mock_reset.assert_called_once()
                mock_load.assert_called_once()
                
    def test_accept_settings(self):
        """测试接受设置"""
        with patch.object(self.dialog, 'get_current_settings') as mock_get:
            with patch.object(self.dialog, 'save_settings') as mock_save:
                with patch.object(self.dialog, 'accept') as mock_accept:
                    mock_get.return_value = {'test': 'value'}
                    
                    self.dialog.accept_settings()
                    
                    mock_get.assert_called_once()
                    mock_save.assert_called_once_with({'test': 'value'})
                    mock_accept.assert_called_once()


class TestProxyTestThread:
    """代理测试线程测试类"""
    
    def test_proxy_test_thread_initialization(self):
        """测试代理测试线程初始化"""
        thread = ProxyTestThread("http", "proxy.example.com", 8080, "user", "pass")
        
        assert thread.proxy_type == "http"
        assert thread.host == "proxy.example.com"
        assert thread.port == 8080
        assert thread.username == "user"
        assert thread.password == "pass"
        
    @patch('requests.get')
    def test_proxy_test_success(self, mock_get):
        """测试代理测试成功"""
        # 模拟成功响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'origin': '192.168.1.1'}
        mock_get.return_value = mock_response
        
        thread = ProxyTestThread("http", "proxy.example.com", 8080)
        
        # 模拟信号连接
        results = []
        thread.test_completed.connect(lambda success, msg: results.append((success, msg)))
        
        thread.run()
        
        assert len(results) == 1
        assert results[0][0] is True  # success
        assert "192.168.1.1" in results[0][1]  # message contains IP
        
    @patch('requests.get')
    def test_proxy_test_failure(self, mock_get):
        """测试代理测试失败"""
        # 模拟异常
        mock_get.side_effect = Exception("Connection failed")
        
        thread = ProxyTestThread("http", "proxy.example.com", 8080)
        
        # 模拟信号连接
        results = []
        thread.test_completed.connect(lambda success, msg: results.append((success, msg)))
        
        thread.run()
        
        assert len(results) == 1
        assert results[0][0] is False  # failure
        assert "Connection failed" in results[0][1]  # error message


if __name__ == "__main__":
    pytest.main([__file__])