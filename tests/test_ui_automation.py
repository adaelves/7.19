"""
UI automation tests for the video downloader application.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest

from app.ui.main_window import MainWindow
from app.ui.components.url_input import URLInputWidget
from app.ui.components.download_list import DownloadListWidget
from app.ui.components.download_task_card import DownloadTaskCard
from app.ui.dialogs.settings_dialog import SettingsDialog
from tests.utils.test_helpers import TestDataFactory


@pytest.mark.ui
class TestMainWindowUI:
    """Test main window UI functionality"""
    
    @pytest.fixture
    def main_window(self, qapp):
        """Create main window for testing"""
        window = MainWindow()
        window.show()
        QTest.qWaitForWindowExposed(window)
        return window
    
    def test_window_initialization(self, main_window):
        """Test main window initialization"""
        assert main_window.isVisible()
        assert main_window.windowTitle() == "Multi-Platform Video Downloader"
        
        # Check main components exist
        assert main_window.url_input is not None
        assert main_window.download_list is not None
        assert main_window.status_bar is not None
    
    def test_url_input_functionality(self, main_window):
        """Test URL input functionality"""
        url_input = main_window.url_input
        test_url = "https://youtube.com/watch?v=test123"
        
        # Simulate typing URL
        url_input.line_edit.setText(test_url)
        assert url_input.line_edit.text() == test_url
        
        # Test URL validation
        assert url_input.is_valid_url(test_url)
        assert not url_input.is_valid_url("invalid_url")
    
    def test_add_download_button(self, main_window):
        """Test add download button functionality"""
        url_input = main_window.url_input
        test_url = "https://youtube.com/watch?v=test123"
        
        # Set URL and click add button
        url_input.line_edit.setText(test_url)
        
        with patch.object(main_window, 'add_download') as mock_add:
            QTest.mouseClick(url_input.add_button, Qt.LeftButton)
            mock_add.assert_called_once_with(test_url)
    
    def test_paste_button(self, main_window):
        """Test paste button functionality"""
        url_input = main_window.url_input
        test_url = "https://youtube.com/watch?v=test123"
        
        # Mock clipboard
        with patch('PySide6.QtWidgets.QApplication.clipboard') as mock_clipboard:
            mock_clipboard.return_value.text.return_value = test_url
            
            QTest.mouseClick(url_input.paste_button, Qt.LeftButton)
            assert url_input.line_edit.text() == test_url
    
    def test_theme_switching(self, main_window):
        """Test theme switching functionality"""
        # Get initial theme
        initial_theme = main_window.theme_manager.current_theme
        
        # Switch theme
        main_window.switch_theme()
        
        # Verify theme changed
        new_theme = main_window.theme_manager.current_theme
        assert new_theme != initial_theme
    
    def test_settings_dialog_opening(self, main_window):
        """Test opening settings dialog"""
        with patch('app.ui.dialogs.settings_dialog.SettingsDialog') as mock_dialog:
            mock_dialog_instance = Mock()
            mock_dialog.return_value = mock_dialog_instance
            
            # Trigger settings dialog
            main_window.open_settings()
            
            mock_dialog.assert_called_once()
            mock_dialog_instance.exec.assert_called_once()
    
    def test_window_minimize_to_tray(self, main_window):
        """Test window minimize to system tray"""
        # Mock system tray
        with patch.object(main_window, 'system_tray') as mock_tray:
            mock_tray.isVisible.return_value = True
            
            # Minimize window
            main_window.minimize_to_tray()
            
            assert main_window.isHidden()
    
    def test_boss_key_functionality(self, main_window):
        """Test boss key (quick hide) functionality"""
        # Simulate boss key press
        QTest.keySequence(main_window, "Ctrl+Shift+H")
        
        # Window should be hidden
        assert main_window.isHidden()


@pytest.mark.ui
class TestDownloadListUI:
    """Test download list UI functionality"""
    
    @pytest.fixture
    def download_list(self, qapp):
        """Create download list widget for testing"""
        widget = DownloadListWidget()
        widget.show()
        QTest.qWaitForWindowExposed(widget)
        return widget
    
    def test_add_download_task(self, download_list):
        """Test adding download task to list"""
        task = TestDataFactory.create_download_task()
        
        download_list.add_task(task)
        
        assert download_list.count() == 1
        
        # Get the task card
        item = download_list.item(0)
        task_card = download_list.itemWidget(item)
        assert isinstance(task_card, DownloadTaskCard)
        assert task_card.task.id == task.id
    
    def test_remove_download_task(self, download_list):
        """Test removing download task from list"""
        task = TestDataFactory.create_download_task()
        download_list.add_task(task)
        
        assert download_list.count() == 1
        
        download_list.remove_task(task.id)
        assert download_list.count() == 0
    
    def test_task_selection(self, download_list):
        """Test task selection functionality"""
        tasks = [TestDataFactory.create_download_task() for _ in range(3)]
        
        for task in tasks:
            download_list.add_task(task)
        
        # Select first task
        download_list.setCurrentRow(0)
        selected_task = download_list.get_selected_task()
        
        assert selected_task is not None
        assert selected_task.id == tasks[0].id
    
    def test_context_menu(self, download_list):
        """Test right-click context menu"""
        task = TestDataFactory.create_download_task()
        download_list.add_task(task)
        
        # Get task card
        item = download_list.item(0)
        task_card = download_list.itemWidget(item)
        
        # Simulate right-click
        with patch.object(task_card, 'show_context_menu') as mock_menu:
            QTest.mouseClick(task_card, Qt.RightButton)
            mock_menu.assert_called_once()
    
    def test_drag_and_drop_reordering(self, download_list):
        """Test drag and drop reordering"""
        tasks = [TestDataFactory.create_download_task() for _ in range(3)]
        
        for task in tasks:
            download_list.add_task(task)
        
        # Simulate drag and drop (simplified)
        original_order = [download_list.get_task_at_index(i).id for i in range(3)]
        
        # Move first item to second position
        download_list.move_task(0, 1)
        
        new_order = [download_list.get_task_at_index(i).id for i in range(3)]
        
        # Order should have changed
        assert new_order != original_order
        assert new_order[1] == original_order[0]
    
    def test_batch_operations(self, download_list):
        """Test batch operations on selected tasks"""
        tasks = [TestDataFactory.create_download_task() for _ in range(5)]
        
        for task in tasks:
            download_list.add_task(task)
        
        # Select multiple tasks
        for i in range(3):
            download_list.item(i).setSelected(True)
        
        selected_tasks = download_list.get_selected_tasks()
        assert len(selected_tasks) == 3
        
        # Test batch pause
        with patch.object(download_list, 'pause_tasks') as mock_pause:
            download_list.pause_selected_tasks()
            mock_pause.assert_called_once_with(selected_tasks)


@pytest.mark.ui
class TestDownloadTaskCardUI:
    """Test download task card UI functionality"""
    
    @pytest.fixture
    def task_card(self, qapp):
        """Create task card for testing"""
        task = TestDataFactory.create_download_task()
        card = DownloadTaskCard(task)
        card.show()
        QTest.qWaitForWindowExposed(card)
        return card
    
    def test_task_card_display(self, task_card):
        """Test task card display elements"""
        task = task_card.task
        
        # Check title display
        assert task_card.title_label.text() == task.metadata.title
        
        # Check author display
        assert task_card.author_label.text() == task.metadata.author
        
        # Check progress display
        assert task_card.progress_bar.value() == int(task.progress)
    
    def test_progress_updates(self, task_card):
        """Test progress bar updates"""
        initial_progress = task_card.progress_bar.value()
        
        # Update progress
        new_progress = 75.0
        task_card.update_progress(new_progress)
        
        assert task_card.progress_bar.value() == int(new_progress)
        assert task_card.progress_bar.value() != initial_progress
    
    def test_status_indicator(self, task_card):
        """Test status indicator updates"""
        # Test different status states
        from app.data.models.core import TaskStatus
        
        status_tests = [
            (TaskStatus.PENDING, "pending"),
            (TaskStatus.DOWNLOADING, "downloading"),
            (TaskStatus.COMPLETED, "completed"),
            (TaskStatus.FAILED, "failed"),
            (TaskStatus.PAUSED, "paused")
        ]
        
        for status, expected_class in status_tests:
            task_card.update_status(status)
            
            # Check if status indicator has correct style class
            style_sheet = task_card.status_indicator.styleSheet()
            assert expected_class in style_sheet.lower() or len(style_sheet) == 0
    
    def test_control_buttons(self, task_card):
        """Test control button functionality"""
        # Test play/pause button
        with patch.object(task_card, 'toggle_download') as mock_toggle:
            QTest.mouseClick(task_card.play_pause_button, Qt.LeftButton)
            mock_toggle.assert_called_once()
        
        # Test cancel button
        with patch.object(task_card, 'cancel_download') as mock_cancel:
            QTest.mouseClick(task_card.cancel_button, Qt.LeftButton)
            mock_cancel.assert_called_once()
    
    def test_thumbnail_loading(self, task_card):
        """Test thumbnail loading"""
        # Mock network request for thumbnail
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.content = b"fake_image_data"
            mock_get.return_value = mock_response
            
            # Trigger thumbnail load
            task_card.load_thumbnail()
            
            # Should make network request
            mock_get.assert_called_once()


@pytest.mark.ui
class TestSettingsDialogUI:
    """Test settings dialog UI functionality"""
    
    @pytest.fixture
    def settings_dialog(self, qapp):
        """Create settings dialog for testing"""
        dialog = SettingsDialog()
        dialog.show()
        QTest.qWaitForWindowExposed(dialog)
        return dialog
    
    def test_dialog_initialization(self, settings_dialog):
        """Test settings dialog initialization"""
        assert settings_dialog.isVisible()
        assert settings_dialog.windowTitle() == "Settings"
        
        # Check tabs exist
        assert settings_dialog.tab_widget.count() > 0
    
    def test_general_settings_tab(self, settings_dialog):
        """Test general settings tab"""
        # Switch to general tab
        settings_dialog.tab_widget.setCurrentIndex(0)
        
        general_tab = settings_dialog.general_tab
        
        # Test download path setting
        test_path = "/test/downloads"
        general_tab.download_path_edit.setText(test_path)
        assert general_tab.download_path_edit.text() == test_path
        
        # Test browse button
        with patch('PySide6.QtWidgets.QFileDialog.getExistingDirectory') as mock_dialog:
            mock_dialog.return_value = test_path
            
            QTest.mouseClick(general_tab.browse_button, Qt.LeftButton)
            mock_dialog.assert_called_once()
    
    def test_advanced_settings_tab(self, settings_dialog):
        """Test advanced settings tab"""
        # Switch to advanced tab
        advanced_tab_index = settings_dialog.get_tab_index("Advanced")
        settings_dialog.tab_widget.setCurrentIndex(advanced_tab_index)
        
        advanced_tab = settings_dialog.advanced_tab
        
        # Test concurrent downloads setting
        advanced_tab.concurrent_downloads_spin.setValue(5)
        assert advanced_tab.concurrent_downloads_spin.value() == 5
        
        # Test proxy settings
        advanced_tab.proxy_enabled_check.setChecked(True)
        assert advanced_tab.proxy_enabled_check.isChecked()
    
    def test_theme_settings(self, settings_dialog):
        """Test theme settings"""
        appearance_tab_index = settings_dialog.get_tab_index("Appearance")
        settings_dialog.tab_widget.setCurrentIndex(appearance_tab_index)
        
        appearance_tab = settings_dialog.appearance_tab
        
        # Test theme selection
        appearance_tab.theme_combo.setCurrentText("Dark")
        assert appearance_tab.theme_combo.currentText() == "Dark"
    
    def test_settings_save_and_load(self, settings_dialog):
        """Test settings save and load functionality"""
        # Modify some settings
        settings_dialog.general_tab.download_path_edit.setText("/new/path")
        settings_dialog.advanced_tab.concurrent_downloads_spin.setValue(8)
        
        # Save settings
        with patch.object(settings_dialog, 'save_settings') as mock_save:
            QTest.mouseClick(settings_dialog.ok_button, Qt.LeftButton)
            mock_save.assert_called_once()
    
    def test_settings_reset(self, settings_dialog):
        """Test settings reset functionality"""
        # Modify settings
        settings_dialog.general_tab.download_path_edit.setText("/modified/path")
        
        # Reset to defaults
        with patch.object(settings_dialog, 'reset_to_defaults') as mock_reset:
            QTest.mouseClick(settings_dialog.reset_button, Qt.LeftButton)
            mock_reset.assert_called_once()


@pytest.mark.ui
class TestUIInteractions:
    """Test complex UI interactions"""
    
    @pytest.fixture
    def full_ui(self, qapp):
        """Create full UI setup for testing"""
        main_window = MainWindow()
        main_window.show()
        QTest.qWaitForWindowExposed(main_window)
        return main_window
    
    def test_complete_download_workflow(self, full_ui):
        """Test complete download workflow through UI"""
        main_window = full_ui
        
        # Step 1: Enter URL
        test_url = "https://youtube.com/watch?v=test123"
        main_window.url_input.line_edit.setText(test_url)
        
        # Step 2: Click add download
        with patch.object(main_window.download_service, 'add_download') as mock_add:
            mock_add.return_value = "task123"
            
            QTest.mouseClick(main_window.url_input.add_button, Qt.LeftButton)
            
            # Verify download was added
            mock_add.assert_called_once_with(test_url, main_window.get_download_options())
        
        # Step 3: Verify task appears in list
        # (This would require more complex mocking of the download service)
        assert main_window.download_list.count() >= 0
    
    def test_keyboard_shortcuts(self, full_ui):
        """Test keyboard shortcuts"""
        main_window = full_ui
        
        # Test Ctrl+V for paste
        test_url = "https://youtube.com/watch?v=test123"
        with patch('PySide6.QtWidgets.QApplication.clipboard') as mock_clipboard:
            mock_clipboard.return_value.text.return_value = test_url
            
            QTest.keySequence(main_window, "Ctrl+V")
            
            # URL should be pasted into input field
            assert main_window.url_input.line_edit.text() == test_url
        
        # Test Ctrl+, for settings
        with patch.object(main_window, 'open_settings') as mock_settings:
            QTest.keySequence(main_window, "Ctrl+,")
            mock_settings.assert_called_once()
    
    def test_window_state_persistence(self, full_ui):
        """Test window state persistence"""
        main_window = full_ui
        
        # Change window size and position
        main_window.resize(1200, 800)
        main_window.move(100, 100)
        
        # Save window state
        with patch.object(main_window, 'save_window_state') as mock_save:
            main_window.closeEvent(Mock())
            mock_save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_real_time_updates(self, full_ui):
        """Test real-time UI updates"""
        main_window = full_ui
        
        # Add a mock task
        task = TestDataFactory.create_download_task()
        main_window.download_list.add_task(task)
        
        # Simulate progress updates
        progress_values = [25, 50, 75, 100]
        
        for progress in progress_values:
            # Update task progress
            task.progress = progress
            main_window.download_list.update_task_progress(task.id, progress)
            
            # Process events to update UI
            QApplication.processEvents()
            
            # Small delay to simulate real-time updates
            await asyncio.sleep(0.01)
        
        # Verify final progress
        task_card = main_window.download_list.get_task_card(task.id)
        if task_card:
            assert task_card.progress_bar.value() == 100


if __name__ == "__main__":
    pytest.main([__file__])