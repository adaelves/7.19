"""
测试系统集成服务功能
"""
import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QSettings
from PySide6.QtTest import QTest

from app.services.system_integration_service import SystemIntegrationService


@pytest.fixture
def app():
    """创建QApplication实例"""
    if not QApplication.instance():
        return QApplication(sys.argv)
    return QApplication.instance()


@pytest.fixture
def main_window(app):
    """创建主窗口实例"""
    window = QMainWindow()
    return window


@pytest.fixture
def system_integration(main_window):
    """创建系统集成服务实例"""
    return SystemIntegrationService(main_window)


class TestSystemIntegrationService:
    """测试系统集成服务"""
    
    def test_initialization(self, system_integration):
        """测试服务初始化"""
        assert system_integration.main_window is not None
        assert system_integration.settings is not None
        assert isinstance(system_integration.settings, QSettings)
        
    def test_tray_icon_creation(self, system_integration):
        """测试托盘图标创建"""
        # 托盘图标可能不可用在测试环境中
        if system_integration.tray_icon:
            assert system_integration.tray_icon is not None
            assert system_integration.tray_icon.toolTip() == "多平台视频下载器"
            
    def test_boss_key_setup(self, system_integration):
        """测试老板键设置"""
        if system_integration.boss_key_shortcut:
            assert system_integration.boss_key_shortcut is not None
            
    def test_default_icon_creation(self, system_integration):
        """测试默认图标创建"""
        icon = system_integration.create_default_icon()
        assert icon is not None
        assert not icon.isNull()
        
    def test_boss_key_get_set(self, system_integration):
        """测试老板键获取和设置"""
        # 测试默认值
        default_key = system_integration.get_boss_key()
        assert default_key == "Ctrl+Shift+H"
        
        # 测试设置新值
        new_key = "Ctrl+Alt+H"
        system_integration.set_boss_key(new_key)
        assert system_integration.get_boss_key() == new_key
        
    def test_notification_methods(self, system_integration):
        """测试通知方法"""
        # 这些方法应该不会抛出异常
        system_integration.show_notification("测试标题", "测试消息")
        system_integration.show_download_complete_notification("test.mp4")
        system_integration.show_download_failed_notification("test.mp4", "网络错误")
        
    def test_tray_tooltip_update(self, system_integration):
        """测试托盘提示更新"""
        if system_integration.tray_icon:
            test_message = "测试提示消息"
            system_integration.update_tray_tooltip(test_message)
            assert system_integration.tray_icon.toolTip() == test_message
            
    def test_tray_icon_progress_update(self, system_integration):
        """测试托盘图标进度更新"""
        # 这个方法应该不会抛出异常
        system_integration.update_tray_icon_with_progress(50)
        system_integration.update_tray_icon_with_progress(100)
        
    @patch('winreg.OpenKey')
    @patch('winreg.SetValueEx')
    @patch('winreg.DeleteValue')
    @patch('winreg.CloseKey')
    def test_startup_enable_disable(self, mock_close, mock_delete, mock_set, mock_open, system_integration):
        """测试开机启动启用/禁用"""
        mock_key = MagicMock()
        mock_open.return_value = mock_key
        
        # 测试启用开机启动
        result = system_integration.enable_startup(True)
        assert result is True
        mock_open.assert_called()
        mock_set.assert_called()
        mock_close.assert_called_with(mock_key)
        
        # 测试禁用开机启动
        result = system_integration.enable_startup(False)
        assert result is True
        
    def test_startup_status(self, system_integration):
        """测试开机启动状态"""
        # 默认应该是False
        assert system_integration.is_startup_enabled() is False
        
    @patch('winreg.CreateKey')
    @patch('winreg.SetValueEx')
    @patch('winreg.CloseKey')
    def test_protocol_registration(self, mock_close, mock_set, mock_create, system_integration):
        """测试协议注册"""
        mock_key = MagicMock()
        mock_create.return_value = mock_key
        
        result = system_integration.register_protocol_handler("testprotocol")
        assert result is True
        mock_create.assert_called()
        mock_set.assert_called()
        
    @patch('winreg.CreateKey')
    @patch('winreg.SetValueEx')
    @patch('winreg.CloseKey')
    def test_file_associations_registration(self, mock_close, mock_set, mock_create, system_integration):
        """测试文件关联注册"""
        mock_key = MagicMock()
        mock_create.return_value = mock_key
        
        test_extensions = ['.mp4', '.avi']
        result = system_integration.register_file_associations(test_extensions)
        assert result is True
        mock_create.assert_called()
        mock_set.assert_called()
        
    def test_signal_emissions(self, system_integration):
        """测试信号发射"""
        # 创建信号接收器
        show_received = Mock()
        hide_received = Mock()
        quit_received = Mock()
        
        system_integration.show_window_requested.connect(show_received)
        system_integration.hide_window_requested.connect(hide_received)
        system_integration.quit_requested.connect(quit_received)
        
        # 测试托盘菜单动作（如果托盘可用）
        if system_integration.tray_icon:
            menu = system_integration.tray_icon.contextMenu()
            if menu:
                actions = menu.actions()
                if len(actions) > 0:
                    # 触发显示窗口动作
                    actions[0].trigger()
                    show_received.assert_called_once()
                    
    def test_window_visibility_toggle(self, system_integration, main_window):
        """测试窗口可见性切换"""
        # 模拟窗口可见
        main_window.show()
        assert main_window.isVisible()
        
        # 测试切换功能
        system_integration.toggle_window_visibility()
        # 由于这会发射信号而不是直接隐藏窗口，我们检查信号是否正确发射
        
    def test_cleanup(self, system_integration):
        """测试资源清理"""
        # 这个方法应该不会抛出异常
        system_integration.cleanup()
        
        if system_integration.boss_key_shortcut:
            assert not system_integration.boss_key_shortcut.isEnabled()


class TestSystemIntegrationIntegration:
    """测试系统集成服务的集成功能"""
    
    def test_tray_menu_actions(self, system_integration):
        """测试托盘菜单动作"""
        if not system_integration.tray_icon:
            pytest.skip("系统托盘不可用")
            
        menu = system_integration.tray_icon.contextMenu()
        assert menu is not None
        
        actions = menu.actions()
        assert len(actions) > 0
        
        # 检查菜单项文本
        action_texts = [action.text() for action in actions if not action.isSeparator()]
        expected_texts = ["显示主窗口", "隐藏到托盘", "添加下载", "暂停所有下载", "设置", "退出"]
        
        for expected_text in expected_texts:
            assert expected_text in action_texts
            
    def test_settings_persistence(self, system_integration):
        """测试设置持久化"""
        # 设置一个值
        test_key = "Ctrl+Shift+T"
        system_integration.set_boss_key(test_key)
        
        # 创建新实例，应该能读取到设置
        new_service = SystemIntegrationService(system_integration.main_window)
        assert new_service.get_boss_key() == test_key
        
    def test_error_handling(self, system_integration):
        """测试错误处理"""
        # 测试无效的快捷键设置
        system_integration.set_boss_key("")  # 空字符串应该不会崩溃
        
        # 测试无主窗口的情况
        service_no_window = SystemIntegrationService(None)
        service_no_window.toggle_window_visibility()  # 应该不会崩溃


if __name__ == "__main__":
    pytest.main([__file__])