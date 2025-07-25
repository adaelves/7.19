"""
Download history widget with search and filtering capabilities.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QPushButton, QComboBox, QLabel, QFrame, QHeaderView,
    QAbstractItemView, QMenu, QMessageBox, QFileDialog, QDateEdit,
    QCheckBox, QSplitter, QTextEdit, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QTimer, QDate, QThread
from PySide6.QtGui import QFont, QIcon, QPixmap, QAction
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json

class HistorySearchWidget(QWidget):
    """Search and filter widget for history"""
    
    search_requested = Signal(dict)  # Emit search parameters
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup search UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Search input row
        search_row = QHBoxLayout()
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索标题、作者或链接...")
        self.search_input.setObjectName("searchInput")
        search_row.addWidget(self.search_input, 1)
        
        # Platform filter
        self.platform_combo = QComboBox()
        self.platform_combo.addItems([
            "全部平台", "YouTube", "Bilibili", "TikTok", "Instagram", 
            "Twitter", "Pornhub", "其他"
        ])
        self.platform_combo.setObjectName("platformFilter")
        search_row.addWidget(self.platform_combo)
        
        # Search button
        self.search_btn = QPushButton("🔍 搜索")
        self.search_btn.setObjectName("searchButton")
        search_row.addWidget(self.search_btn)
        
        layout.addLayout(search_row)
        
        # Advanced filters row
        filters_row = QHBoxLayout()
        
        # Date range
        filters_row.addWidget(QLabel("日期范围:"))
        
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        filters_row.addWidget(self.date_from)
        
        filters_row.addWidget(QLabel("至"))
        
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        filters_row.addWidget(self.date_to)
        
        # Enable date filter checkbox
        self.date_filter_enabled = QCheckBox("启用日期过滤")
        filters_row.addWidget(self.date_filter_enabled)
        
        filters_row.addStretch()
        
        # Clear filters button
        self.clear_btn = QPushButton("清除过滤")
        self.clear_btn.setObjectName("clearButton")
        filters_row.addWidget(self.clear_btn)
        
        layout.addLayout(filters_row)
    
    def setup_connections(self):
        """Setup signal connections"""
        self.search_btn.clicked.connect(self.perform_search)
        self.search_input.returnPressed.connect(self.perform_search)
        self.platform_combo.currentTextChanged.connect(self.perform_search)
        self.clear_btn.clicked.connect(self.clear_filters)
        self.date_filter_enabled.toggled.connect(self.perform_search)
    
    def perform_search(self):
        """Perform search with current parameters"""
        search_params = {
            'keyword': self.search_input.text().strip(),
            'platform': None if self.platform_combo.currentText() == "全部平台" else self.platform_combo.currentText(),
            'date_from': self.date_from.date().toPython() if self.date_filter_enabled.isChecked() else None,
            'date_to': self.date_to.date().toPython() if self.date_filter_enabled.isChecked() else None
        }
        self.search_requested.emit(search_params)
    
    def clear_filters(self):
        """Clear all filters"""
        self.search_input.clear()
        self.platform_combo.setCurrentIndex(0)
        self.date_filter_enabled.setChecked(False)
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_to.setDate(QDate.currentDate())
        self.perform_search()


class HistoryTableWidget(QTableWidget):
    """Custom table widget for displaying download history"""
    
    record_selected = Signal(dict)
    export_requested = Signal()
    delete_requested = Signal(int)
    
    def __init__(self):
        super().__init__()
        self.setup_table()
        self.setup_context_menu()
        
    def setup_table(self):
        """Setup table properties"""
        # Set columns
        columns = [
            "ID", "标题", "作者", "平台", "下载日期", 
            "文件大小", "时长", "状态", "文件路径"
        ]
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        
        # Table properties
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        
        # Header properties
        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Title column
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Author
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Platform
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Date
        
        # Hide ID column
        self.setColumnHidden(0, True)
        
        # Style
        self.setObjectName("historyTable")
        
    def setup_context_menu(self):
        """Setup right-click context menu"""
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
    def show_context_menu(self, position):
        """Show context menu"""
        if not self.itemAt(position):
            return
            
        menu = QMenu(self)
        
        # Open file action
        open_file_action = QAction("打开文件", self)
        open_file_action.triggered.connect(self.open_selected_file)
        menu.addAction(open_file_action)
        
        # Open folder action
        open_folder_action = QAction("打开文件夹", self)
        open_folder_action.triggered.connect(self.open_selected_folder)
        menu.addAction(open_folder_action)
        
        menu.addSeparator()
        
        # Copy URL action
        copy_url_action = QAction("复制链接", self)
        copy_url_action.triggered.connect(self.copy_selected_url)
        menu.addAction(copy_url_action)
        
        # Copy title action
        copy_title_action = QAction("复制标题", self)
        copy_title_action.triggered.connect(self.copy_selected_title)
        menu.addAction(copy_title_action)
        
        menu.addSeparator()
        
        # Delete action
        delete_action = QAction("删除记录", self)
        delete_action.triggered.connect(self.delete_selected_record)
        menu.addAction(delete_action)
        
        menu.exec(self.mapToGlobal(position))
    
    def load_history_data(self, records: List[Dict[str, Any]]):
        """Load history records into table"""
        self.setRowCount(len(records))
        
        for row, record in enumerate(records):
            # ID (hidden)
            self.setItem(row, 0, QTableWidgetItem(str(record.get('id', ''))))
            
            # Title
            title_item = QTableWidgetItem(record.get('title', '未知标题'))
            title_item.setToolTip(record.get('title', ''))
            self.setItem(row, 1, title_item)
            
            # Author
            author_item = QTableWidgetItem(record.get('author', '未知作者'))
            self.setItem(row, 2, author_item)
            
            # Platform
            platform_item = QTableWidgetItem(record.get('platform', '未知'))
            self.setItem(row, 3, platform_item)
            
            # Download date
            download_date = record.get('download_date', '')
            if isinstance(download_date, str) and download_date:
                try:
                    date_obj = datetime.fromisoformat(download_date.replace(' ', 'T'))
                    formatted_date = date_obj.strftime('%Y-%m-%d %H:%M')
                except ValueError:
                    formatted_date = download_date
            else:
                formatted_date = '未知时间'
            date_item = QTableWidgetItem(formatted_date)
            self.setItem(row, 4, date_item)
            
            # File size
            file_size = record.get('file_size', 0)
            if file_size:
                size_text = self._format_file_size(file_size)
            else:
                size_text = '未知大小'
            size_item = QTableWidgetItem(size_text)
            self.setItem(row, 5, size_item)
            
            # Duration
            duration = record.get('duration', 0)
            if duration:
                duration_text = self._format_duration(duration)
            else:
                duration_text = '未知'
            duration_item = QTableWidgetItem(duration_text)
            self.setItem(row, 6, duration_item)
            
            # Status
            status = record.get('status', 'completed')
            status_item = QTableWidgetItem(self._translate_status(status))
            self.setItem(row, 7, status_item)
            
            # File path
            file_path = record.get('file_path', '')
            path_item = QTableWidgetItem(file_path)
            path_item.setToolTip(file_path)
            self.setItem(row, 8, path_item)
            
            # Store full record data in first item
            self.item(row, 0).setData(Qt.UserRole, record)
    
    def get_selected_record(self) -> Optional[Dict[str, Any]]:
        """Get currently selected record"""
        current_row = self.currentRow()
        if current_row >= 0:
            return self.item(current_row, 0).data(Qt.UserRole)
        return None
    
    def open_selected_file(self):
        """Open selected file"""
        record = self.get_selected_record()
        if record and record.get('file_path'):
            import os
            file_path = record['file_path']
            if os.path.exists(file_path):
                os.startfile(file_path)  # Windows
            else:
                QMessageBox.warning(self, "文件不存在", f"文件不存在: {file_path}")
    
    def open_selected_folder(self):
        """Open folder containing selected file"""
        record = self.get_selected_record()
        if record and record.get('file_path'):
            import os
            from pathlib import Path
            file_path = Path(record['file_path'])
            if file_path.exists():
                os.startfile(file_path.parent)  # Windows
            else:
                QMessageBox.warning(self, "文件不存在", f"文件不存在: {file_path}")
    
    def copy_selected_url(self):
        """Copy selected record URL to clipboard"""
        record = self.get_selected_record()
        if record and record.get('url'):
            from PySide6.QtGui import QGuiApplication
            QGuiApplication.clipboard().setText(record['url'])
    
    def copy_selected_title(self):
        """Copy selected record title to clipboard"""
        record = self.get_selected_record()
        if record and record.get('title'):
            from PySide6.QtGui import QGuiApplication
            QGuiApplication.clipboard().setText(record['title'])
    
    def delete_selected_record(self):
        """Delete selected record"""
        record = self.get_selected_record()
        if record:
            reply = QMessageBox.question(
                self, "确认删除", 
                f"确定要删除记录 '{record.get('title', '未知')}' 吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.delete_requested.emit(record['id'])
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        
        return f"{size:.1f} {size_names[i]}"
    
    def _format_duration(self, seconds: int) -> str:
        """Format duration in seconds to readable format"""
        if seconds < 60:
            return f"{seconds}秒"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}分{secs}秒"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}时{minutes}分"
    
    def _translate_status(self, status: str) -> str:
        """Translate status to Chinese"""
        status_map = {
            'completed': '已完成',
            'failed': '失败',
            'cancelled': '已取消',
            'downloading': '下载中',
            'pending': '等待中'
        }
        return status_map.get(status, status)


class HistoryWidget(QWidget):
    """Main history management widget"""
    
    def __init__(self, history_service):
        super().__init__()
        self.history_service = history_service
        self.setup_ui()
        self.setup_connections()
        self.load_initial_data()
    
    def setup_ui(self):
        """Setup main UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Search widget
        self.search_widget = HistorySearchWidget()
        layout.addWidget(self.search_widget)
        
        # Toolbar
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)
        
        # History table
        self.history_table = HistoryTableWidget()
        layout.addWidget(self.history_table, 1)
        
        # Status bar
        status_bar = self.create_status_bar()
        layout.addWidget(status_bar)
    
    def create_toolbar(self):
        """Create toolbar with action buttons"""
        toolbar = QFrame()
        toolbar.setObjectName("historyToolbar")
        toolbar.setFixedHeight(40)
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(8)
        
        # Refresh button
        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.setObjectName("toolbarButton")
        layout.addWidget(self.refresh_btn)
        
        # Export button
        self.export_btn = QPushButton("📤 导出")
        self.export_btn.setObjectName("toolbarButton")
        layout.addWidget(self.export_btn)
        
        # Statistics button
        self.stats_btn = QPushButton("📊 统计")
        self.stats_btn.setObjectName("toolbarButton")
        layout.addWidget(self.stats_btn)
        
        # Duplicate detection button
        self.duplicate_btn = QPushButton("🔍 重复检测")
        self.duplicate_btn.setObjectName("toolbarButton")
        layout.addWidget(self.duplicate_btn)
        
        layout.addStretch()
        
        # Cleanup button
        self.cleanup_btn = QPushButton("🗑️ 清理")
        self.cleanup_btn.setObjectName("dangerButton")
        layout.addWidget(self.cleanup_btn)
        
        return toolbar
    
    def create_status_bar(self):
        """Create status bar"""
        status_bar = QFrame()
        status_bar.setObjectName("historyStatusBar")
        status_bar.setFixedHeight(24)
        
        layout = QHBoxLayout(status_bar)
        layout.setContentsMargins(16, 4, 16, 4)
        
        self.status_label = QLabel("准备就绪")
        self.status_label.setObjectName("statusLabel")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        self.count_label = QLabel("总计: 0 条记录")
        self.count_label.setObjectName("countLabel")
        layout.addWidget(self.count_label)
        
        return status_bar
    
    def setup_connections(self):
        """Setup signal connections"""
        # Search widget connections
        self.search_widget.search_requested.connect(self.perform_search)
        
        # Table connections
        self.history_table.delete_requested.connect(self.delete_record)
        
        # Toolbar connections
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.export_btn.clicked.connect(self.export_history)
        self.stats_btn.clicked.connect(self.show_statistics)
        self.duplicate_btn.clicked.connect(self.detect_duplicates)
        self.cleanup_btn.clicked.connect(self.cleanup_old_records)
    
    def load_initial_data(self):
        """Load initial history data"""
        try:
            records = self.history_service.get_history(limit=100)
            self.history_table.load_history_data(records)
            self.update_status(f"加载了 {len(records)} 条记录")
            self.update_count(len(records))
        except Exception as e:
            self.update_status(f"加载数据失败: {str(e)}")
    
    def perform_search(self, search_params):
        """Perform search with given parameters"""
        try:
            keyword = search_params.get('keyword', '')
            platform = search_params.get('platform')
            date_from = search_params.get('date_from')
            date_to = search_params.get('date_to')
            
            if keyword or platform or date_from or date_to:
                records = self.history_service.search_history(
                    keyword=keyword,
                    platform=platform,
                    date_from=date_from,
                    date_to=date_to,
                    limit=1000
                )
                self.update_status(f"搜索到 {len(records)} 条记录")
            else:
                records = self.history_service.get_history(limit=100)
                self.update_status(f"显示最近 {len(records)} 条记录")
            
            self.history_table.load_history_data(records)
            self.update_count(len(records))
            
        except Exception as e:
            self.update_status(f"搜索失败: {str(e)}")
    
    def refresh_data(self):
        """Refresh history data"""
        self.load_initial_data()
    
    def delete_record(self, record_id):
        """Delete history record"""
        try:
            if self.history_service.delete_record(record_id):
                self.update_status("记录已删除")
                self.refresh_data()
            else:
                self.update_status("删除失败")
        except Exception as e:
            self.update_status(f"删除失败: {str(e)}")
    
    def export_history(self):
        """Export history to file"""
        try:
            # Show file dialog
            file_path, selected_filter = QFileDialog.getSaveFileName(
                self,
                "导出历史记录",
                "download_history.csv",
                "CSV文件 (*.csv);;JSON文件 (*.json)"
            )
            
            if file_path:
                # Determine format from extension
                format_type = 'json' if file_path.endswith('.json') else 'csv'
                
                # Get current search filters for export
                search_params = {
                    'keyword': self.search_widget.search_input.text().strip(),
                    'platform': None if self.search_widget.platform_combo.currentText() == "全部平台" else self.search_widget.platform_combo.currentText(),
                    'date_from': self.search_widget.date_from.date().toPython() if self.search_widget.date_filter_enabled.isChecked() else None,
                    'date_to': self.search_widget.date_to.date().toPython() if self.search_widget.date_filter_enabled.isChecked() else None
                }
                
                # Export with current filters
                filters = search_params if any(search_params.values()) else None
                
                if self.history_service.export_history(file_path, format_type, filters):
                    self.update_status(f"历史记录已导出到: {file_path}")
                    QMessageBox.information(self, "导出成功", f"历史记录已成功导出到:\n{file_path}")
                else:
                    self.update_status("导出失败")
                    QMessageBox.warning(self, "导出失败", "导出历史记录时发生错误")
                    
        except Exception as e:
            self.update_status(f"导出失败: {str(e)}")
            QMessageBox.critical(self, "导出错误", f"导出时发生错误:\n{str(e)}")
    
    def show_statistics(self):
        """Show download statistics"""
        try:
            stats = self.history_service.get_statistics()
            trends = self.history_service.get_download_trends(30)
            
            # Create statistics dialog
            dialog = QMessageBox(self)
            dialog.setWindowTitle("下载统计")
            dialog.setIcon(QMessageBox.Information)
            
            stats_text = f"""
下载统计信息:

总下载数: {stats.get('total_downloads', 0)}
总文件大小: {stats.get('total_size_formatted', '0 B')}
支持平台数: {stats.get('platforms_count', 0)}
最近7天下载: {stats.get('recent_downloads', 0)}

平台分布:
"""
            
            for platform, count in stats.get('by_platform', {}).items():
                stats_text += f"  {platform}: {count} 个\n"
            
            stats_text += f"\n最近30天趋势:\n"
            stats_text += f"平均每天: {trends.get('average_per_day', 0):.1f} 个\n"
            stats_text += f"总计: {trends.get('total_recent', 0)} 个"
            
            dialog.setText(stats_text)
            dialog.exec()
            
        except Exception as e:
            self.update_status(f"获取统计信息失败: {str(e)}")
    
    def detect_duplicates(self):
        """Detect and show duplicate files"""
        try:
            duplicates = self.history_service.detect_duplicates()
            
            if not duplicates:
                QMessageBox.information(self, "重复检测", "未发现重复文件")
                self.update_status("未发现重复文件")
                return
            
            # Show duplicates dialog
            dialog = QMessageBox(self)
            dialog.setWindowTitle("重复文件检测")
            dialog.setIcon(QMessageBox.Warning)
            
            duplicate_text = f"发现 {len(duplicates)} 组重复文件:\n\n"
            
            for i, (original, dups) in enumerate(duplicates[:5]):  # Show first 5 groups
                duplicate_text += f"组 {i+1}:\n"
                duplicate_text += f"  原始: {original.get('title', '未知')}\n"
                duplicate_text += f"  重复: {len(dups)} 个文件\n\n"
            
            if len(duplicates) > 5:
                duplicate_text += f"... 还有 {len(duplicates) - 5} 组重复文件"
            
            dialog.setText(duplicate_text)
            dialog.exec()
            
            self.update_status(f"发现 {len(duplicates)} 组重复文件")
            
        except Exception as e:
            self.update_status(f"重复检测失败: {str(e)}")
    
    def cleanup_old_records(self):
        """Clean up old download records"""
        try:
            reply = QMessageBox.question(
                self, "清理确认",
                "确定要清理365天前的下载记录吗？\n此操作不可撤销！",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                deleted_count = self.history_service.cleanup_old_records(365)
                self.update_status(f"已清理 {deleted_count} 条旧记录")
                QMessageBox.information(self, "清理完成", f"已清理 {deleted_count} 条旧记录")
                self.refresh_data()
                
        except Exception as e:
            self.update_status(f"清理失败: {str(e)}")
    
    def update_status(self, message):
        """Update status message"""
        self.status_label.setText(message)
    
    def update_count(self, count):
        """Update record count"""
        self.count_label.setText(f"总计: {count} 条记录")