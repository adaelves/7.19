"""
Changelog dialog for displaying release notes and update history.
"""

import asyncio
from typing import List, Dict, Any
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QScrollArea, QWidget, QFrame, QSplitter,
    QListWidget, QListWidgetItem, QTabWidget, QGroupBox
)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QFont, QTextDocument, QTextCursor

from app.services.update_service import UpdateService, ReleaseInfo


class ChangelogFetcher(QThread):
    """Thread for fetching changelog data"""
    
    changelog_fetched = Signal(list)  # List of ReleaseInfo
    error_occurred = Signal(str)
    
    def __init__(self, update_service: UpdateService):
        super().__init__()
        self.update_service = update_service
    
    def run(self):
        """Fetch changelog data"""
        try:
            # Create event loop for async operations
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Fetch release history
            releases = loop.run_until_complete(self._fetch_releases())
            self.changelog_fetched.emit(releases)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            loop.close()
    
    async def _fetch_releases(self) -> List[ReleaseInfo]:
        """Fetch release history from GitHub"""
        import aiohttp
        
        releases = []
        
        try:
            async with aiohttp.ClientSession() as session:
                # Get all releases
                url = f"{self.update_service.api_base_url}/releases"
                
                async with session.get(url) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to fetch releases: HTTP {response.status}")
                    
                    data = await response.json()
                    
                    # Parse releases
                    for release_data in data[:10]:  # Limit to last 10 releases
                        try:
                            release_info = await self.update_service._parse_release_data(release_data, session)
                            releases.append(release_info)
                        except Exception:
                            continue  # Skip invalid releases
            
            return releases
            
        except Exception as e:
            raise Exception(f"获取更新日志失败: {str(e)}")


class ReleaseItemWidget(QWidget):
    """Widget for displaying a single release item"""
    
    def __init__(self, release_info: ReleaseInfo, is_current: bool = False, parent=None):
        super().__init__(parent)
        self.release_info = release_info
        self.is_current = is_current
        self.setup_ui()
    
    def setup_ui(self):
        """Setup release item UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        
        # Header
        header_layout = QHBoxLayout()
        
        # Version and status
        version_layout = QVBoxLayout()
        
        version_label = QLabel(f"版本 {self.release_info.version}")
        version_label.setFont(QFont("", 14, QFont.Bold))
        
        if self.is_current:
            version_label.setStyleSheet("color: #34C759;")
            current_badge = QLabel("当前版本")
            current_badge.setStyleSheet("""
                QLabel {
                    background-color: #34C759;
                    color: white;
                    padding: 2px 8px;
                    border-radius: 10px;
                    font-size: 10px;
                    font-weight: bold;
                }
            """)
            current_badge.setMaximumWidth(60)
            version_layout.addWidget(current_badge)
        elif self.release_info.is_prerelease:
            prerelease_badge = QLabel("预发布")
            prerelease_badge.setStyleSheet("""
                QLabel {
                    background-color: #FF9500;
                    color: white;
                    padding: 2px 8px;
                    border-radius: 10px;
                    font-size: 10px;
                    font-weight: bold;
                }
            """)
            prerelease_badge.setMaximumWidth(60)
            version_layout.addWidget(prerelease_badge)
        
        version_layout.addWidget(version_label)
        header_layout.addLayout(version_layout)
        
        header_layout.addStretch()
        
        # Release date
        date_label = QLabel(self.release_info.release_date.strftime("%Y年%m月%d日"))
        date_label.setStyleSheet("color: #666; font-size: 12px;")
        date_label.setAlignment(Qt.AlignRight)
        header_layout.addWidget(date_label)
        
        layout.addLayout(header_layout)
        
        # Changelog content
        if self.release_info.changelog.strip():
            changelog_text = QTextEdit()
            changelog_text.setPlainText(self.release_info.changelog)
            changelog_text.setReadOnly(True)
            changelog_text.setMaximumHeight(150)
            changelog_text.setStyleSheet("""
                QTextEdit {
                    border: 1px solid #E0E0E0;
                    border-radius: 6px;
                    background-color: #F8F9FA;
                    font-size: 11px;
                    padding: 8px;
                }
            """)
            layout.addWidget(changelog_text)
        else:
            no_changelog = QLabel("暂无更新说明")
            no_changelog.setStyleSheet("color: #999; font-style: italic; padding: 8px;")
            layout.addWidget(no_changelog)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("color: #E0E0E0;")
        layout.addWidget(separator)


class ChangelogDialog(QDialog):
    """Main changelog dialog"""
    
    def __init__(self, update_service: UpdateService, parent=None):
        super().__init__(parent)
        self.update_service = update_service
        self.releases = []
        self.current_version = update_service.current_version
        
        self.setup_ui()
        self.load_changelog()
    
    def setup_ui(self):
        """Setup changelog dialog UI"""
        self.setWindowTitle("更新日志")
        self.setMinimumSize(700, 600)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("更新日志")
        title_label.setFont(QFont("", 16, QFont.Bold))
        
        current_version_label = QLabel(f"当前版本: {self.current_version}")
        current_version_label.setStyleSheet("color: #666;")
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(current_version_label)
        
        layout.addLayout(header_layout)
        
        # Tab widget for different views
        self.tab_widget = QTabWidget()
        
        # Release history tab
        self.history_tab = self.create_history_tab()
        self.tab_widget.addTab(self.history_tab, "版本历史")
        
        # Current version tab
        self.current_tab = self.create_current_tab()
        self.tab_widget.addTab(self.current_tab, "当前版本")
        
        layout.addWidget(self.tab_widget)
        
        # Loading indicator
        self.loading_label = QLabel("正在加载更新日志...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet("color: #666; padding: 20px;")
        layout.addWidget(self.loading_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.load_changelog)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056CC;
            }
        """)
        
        button_layout.addWidget(refresh_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def create_history_tab(self) -> QWidget:
        """Create release history tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Scroll area for releases
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Container widget for releases
        self.releases_widget = QWidget()
        self.releases_layout = QVBoxLayout(self.releases_widget)
        self.releases_layout.setSpacing(0)
        
        self.scroll_area.setWidget(self.releases_widget)
        layout.addWidget(self.scroll_area)
        
        return tab
    
    def create_current_tab(self) -> QWidget:
        """Create current version tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Current version info
        info_group = QGroupBox("版本信息")
        info_layout = QVBoxLayout(info_group)
        
        version_label = QLabel(f"版本: {self.current_version}")
        version_label.setFont(QFont("", 12, QFont.Bold))
        
        # Try to get build date
        try:
            from pathlib import Path
            import os
            
            exe_path = Path(__file__).parent.parent.parent
            build_time = datetime.fromtimestamp(os.path.getmtime(exe_path))
            build_label = QLabel(f"构建时间: {build_time.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception:
            build_label = QLabel("构建时间: 未知")
        
        build_label.setStyleSheet("color: #666;")
        
        info_layout.addWidget(version_label)
        info_layout.addWidget(build_label)
        
        layout.addWidget(info_group)
        
        # Features in current version
        features_group = QGroupBox("主要功能")
        features_layout = QVBoxLayout(features_group)
        
        features_text = QTextEdit()
        features_text.setReadOnly(True)
        features_text.setPlainText("""
• 支持多平台视频下载 (YouTube, B站, 抖音, Instagram等)
• 高级下载功能 (多线程, 断点续传, M3U8流媒体)
• 插件系统支持扩展新平台
• macOS风格现代化界面
• 创作者监控和自动下载
• 完整的历史记录管理
• 跨平台兼容 (Windows, macOS, Linux)
• 自动更新功能
        """.strip())
        
        features_text.setMaximumHeight(200)
        features_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                background-color: #F8F9FA;
                font-size: 11px;
                padding: 12px;
            }
        """)
        
        features_layout.addWidget(features_text)
        layout.addWidget(features_group)
        
        layout.addStretch()
        
        return tab
    
    def load_changelog(self):
        """Load changelog data"""
        self.loading_label.setVisible(True)
        self.tab_widget.setEnabled(False)
        
        # Clear existing releases
        self.clear_releases()
        
        # Start fetcher thread
        self.fetcher = ChangelogFetcher(self.update_service)
        self.fetcher.changelog_fetched.connect(self.on_changelog_loaded)
        self.fetcher.error_occurred.connect(self.on_error)
        self.fetcher.start()
    
    def clear_releases(self):
        """Clear existing release widgets"""
        while self.releases_layout.count():
            child = self.releases_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def on_changelog_loaded(self, releases: List[ReleaseInfo]):
        """Handle loaded changelog data"""
        self.releases = releases
        self.loading_label.setVisible(False)
        self.tab_widget.setEnabled(True)
        
        # Add release widgets
        for release in releases:
            is_current = release.version == self.current_version
            release_widget = ReleaseItemWidget(release, is_current)
            self.releases_layout.addWidget(release_widget)
        
        # Add stretch at the end
        self.releases_layout.addStretch()
        
        # Scroll to current version if found
        self.scroll_to_current_version()
    
    def scroll_to_current_version(self):
        """Scroll to current version in the list"""
        for i in range(self.releases_layout.count()):
            widget = self.releases_layout.itemAt(i).widget()
            if isinstance(widget, ReleaseItemWidget) and widget.is_current:
                # Scroll to this widget
                self.scroll_area.ensureWidgetVisible(widget)
                break
    
    def on_error(self, error_message: str):
        """Handle error loading changelog"""
        self.loading_label.setText(f"加载失败: {error_message}")
        self.tab_widget.setEnabled(True)
        
        # Add retry option
        retry_btn = QPushButton("重试")
        retry_btn.clicked.connect(self.load_changelog)
        
        # Replace loading label with error message and retry button
        error_layout = QVBoxLayout()
        error_label = QLabel(f"❌ {error_message}")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setStyleSheet("color: #FF3B30; padding: 10px;")
        
        error_layout.addWidget(error_label)
        error_layout.addWidget(retry_btn)
        
        error_widget = QWidget()
        error_widget.setLayout(error_layout)
        
        # Replace loading label
        self.loading_label.setParent(None)
        self.layout().insertWidget(2, error_widget)


class QuickChangelogWidget(QWidget):
    """Quick changelog widget for showing recent changes"""
    
    def __init__(self, release_info: ReleaseInfo, parent=None):
        super().__init__(parent)
        self.release_info = release_info
        self.setup_ui()
    
    def setup_ui(self):
        """Setup quick changelog UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_label = QLabel(f"版本 {self.release_info.version} 更新内容")
        header_label.setFont(QFont("", 12, QFont.Bold))
        header_label.setStyleSheet("color: #007AFF; margin-bottom: 8px;")
        layout.addWidget(header_label)
        
        # Changelog content
        if self.release_info.changelog.strip():
            # Parse and format changelog
            formatted_changelog = self._format_changelog(self.release_info.changelog)
            
            changelog_label = QLabel(formatted_changelog)
            changelog_label.setWordWrap(True)
            changelog_label.setStyleSheet("font-size: 11px; line-height: 1.4;")
            changelog_label.setMaximumHeight(100)
            
            layout.addWidget(changelog_label)
        else:
            no_changelog = QLabel("暂无详细更新说明")
            no_changelog.setStyleSheet("color: #999; font-style: italic;")
            layout.addWidget(no_changelog)
    
    def _format_changelog(self, changelog: str) -> str:
        """Format changelog text for display"""
        lines = changelog.split('\n')
        formatted_lines = []
        
        for line in lines[:5]:  # Show only first 5 lines
            line = line.strip()
            if line:
                if line.startswith('- ') or line.startswith('* '):
                    formatted_lines.append(f"• {line[2:]}")
                elif line.startswith('#'):
                    # Skip headers in quick view
                    continue
                else:
                    formatted_lines.append(line)
        
        result = '\n'.join(formatted_lines)
        if len(lines) > 5:
            result += "\n\n点击查看完整更新日志..."
        
        return result