"""
下载列表组件 - macOS风格
支持拖拽排序、分组筛选、批量操作、虚拟列表优化、搜索过滤
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QListWidget, 
    QListWidgetItem, QLabel, QFrame, QLineEdit, QComboBox, 
    QPushButton, QCheckBox, QMenu, QAbstractItemView, QSplitter,
    QGroupBox, QButtonGroup, QRadioButton
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QColor, QBrush, QIcon
from .download_task_card import DownloadTaskCard
from typing import List, Dict, Set
import re


class VirtualTaskList(QListWidget):
    """虚拟化任务列表 - 支持大量任务的高性能显示"""
    
    item_order_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.drag_start_position = None
        self.visible_items = {}  # 可见项目缓存
        self.item_height = 88  # 固定项目高度
        self.setup_virtual_list()
        self.setup_drag_drop()
        
    def setup_virtual_list(self):
        """设置虚拟列表"""
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setUniformItemSizes(True)
        
    def setup_drag_drop(self):
        """设置拖拽功能"""
        self.setDragDropMode(QListWidget.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        
        # 设置拖拽样式
        self.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                outline: none;
                selection-background-color: rgba(0, 122, 255, 0.1);
            }
            QListWidget::item {
                background-color: transparent;
                border: none;
                padding: 0px;
                margin: 4px 0px;
                border-radius: 8px;
            }
            QListWidget::item:selected {
                background-color: rgba(0, 122, 255, 0.1);
                border: 1px solid rgba(0, 122, 255, 0.3);
            }
            QListWidget::item:hover {
                background-color: rgba(0, 0, 0, 0.05);
            }
        """)
        
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if not (event.buttons() & Qt.LeftButton):
            return
            
        if not self.drag_start_position:
            return
            
        # 检查是否达到拖拽距离
        from PySide6.QtGui import QGuiApplication
        if ((event.pos() - self.drag_start_position).manhattanLength() < 
            QGuiApplication.startDragDistance()):
            return
            
        super().mouseMoveEvent(event)
        
    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.accept()
        else:
            event.ignore()
            
    def dragMoveEvent(self, event):
        """拖拽移动事件"""
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.accept()
            self.update()
        else:
            event.ignore()
            
    def dropEvent(self, event):
        """拖拽放下事件"""
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.accept()
            super().dropEvent(event)
            self.item_order_changed.emit()
        else:
            event.ignore()
            
    def paintEvent(self, event):
        """绘制事件"""
        super().paintEvent(event)
        
        # 如果列表为空，显示提示信息
        if self.count() == 0:
            painter = QPainter(self.viewport())
            if painter.isActive():
                painter.setRenderHint(QPainter.Antialiasing)
                
                # 绘制空状态提示
                painter.setPen(QColor(142, 142, 147))
                font = painter.font()
                font.setPointSize(14)
                painter.setFont(font)
                
                text = "暂无下载任务\n请在上方输入视频链接开始下载"
                rect = self.viewport().rect()
                painter.drawText(rect, Qt.AlignCenter, text)
                
                painter.end()


class TaskFilterWidget(QWidget):
    """任务筛选控件"""
    
    filter_changed = Signal(dict)  # 筛选条件改变信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(12)
        
        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索任务...")
        self.search_input.setObjectName("taskSearchInput")
        self.search_input.setStyleSheet("""
            #taskSearchInput {
                padding: 8px 12px;
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 8px;
                background-color: rgba(0, 0, 0, 0.05);
                font-size: 13px;
            }
            #taskSearchInput:focus {
                border-color: #007aff;
                background-color: white;
            }
        """)
        layout.addWidget(self.search_input, 1)
        
        # 状态筛选
        self.status_filter = QComboBox()
        self.status_filter.setObjectName("statusFilter")
        self.status_filter.addItems([
            "全部状态", "等待中", "下载中", "已暂停", "已完成", "出错"
        ])
        self.status_filter.setStyleSheet("""
            #statusFilter {
                padding: 8px 12px;
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 8px;
                background-color: rgba(0, 0, 0, 0.05);
                font-size: 13px;
                min-width: 100px;
            }
            #statusFilter:focus {
                border-color: #007aff;
            }
        """)
        layout.addWidget(self.status_filter)
        
        # 平台筛选
        self.platform_filter = QComboBox()
        self.platform_filter.setObjectName("platformFilter")
        self.platform_filter.addItems([
            "全部平台", "YouTube", "B站", "抖音", "Instagram", "其他"
        ])
        self.platform_filter.setStyleSheet("""
            #platformFilter {
                padding: 8px 12px;
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 8px;
                background-color: rgba(0, 0, 0, 0.05);
                font-size: 13px;
                min-width: 100px;
            }
            #platformFilter:focus {
                border-color: #007aff;
            }
        """)
        layout.addWidget(self.platform_filter)
        
        # 连接信号
        self.search_input.textChanged.connect(self.emit_filter_changed)
        self.status_filter.currentTextChanged.connect(self.emit_filter_changed)
        self.platform_filter.currentTextChanged.connect(self.emit_filter_changed)
        
    def emit_filter_changed(self):
        """发送筛选条件改变信号"""
        filters = {
            'search': self.search_input.text(),
            'status': self.status_filter.currentText(),
            'platform': self.platform_filter.currentText()
        }
        self.filter_changed.emit(filters)
        
    def get_filters(self) -> dict:
        """获取当前筛选条件"""
        return {
            'search': self.search_input.text(),
            'status': self.status_filter.currentText(),
            'platform': self.platform_filter.currentText()
        }


class TaskGroupWidget(QWidget):
    """任务分组控件"""
    
    group_changed = Signal(str)  # 分组方式改变信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(8)
        
        # 分组标签
        group_label = QLabel("分组:")
        group_label.setStyleSheet("font-size: 13px; color: #8e8e93;")
        layout.addWidget(group_label)
        
        # 分组选项
        self.group_buttons = QButtonGroup(self)
        
        # 无分组
        no_group_btn = QRadioButton("无分组")
        no_group_btn.setChecked(True)
        no_group_btn.setObjectName("groupButton")
        self.group_buttons.addButton(no_group_btn, 0)
        layout.addWidget(no_group_btn)
        
        # 按状态分组
        status_group_btn = QRadioButton("按状态")
        status_group_btn.setObjectName("groupButton")
        self.group_buttons.addButton(status_group_btn, 1)
        layout.addWidget(status_group_btn)
        
        # 按平台分组
        platform_group_btn = QRadioButton("按平台")
        platform_group_btn.setObjectName("groupButton")
        self.group_buttons.addButton(platform_group_btn, 2)
        layout.addWidget(platform_group_btn)
        
        # 按日期分组
        date_group_btn = QRadioButton("按日期")
        date_group_btn.setObjectName("groupButton")
        self.group_buttons.addButton(date_group_btn, 3)
        layout.addWidget(date_group_btn)
        
        layout.addStretch()
        
        # 设置样式
        self.setStyleSheet("""
            QRadioButton#groupButton {
                font-size: 13px;
                color: #1d1d1f;
                spacing: 6px;
            }
            QRadioButton#groupButton::indicator {
                width: 16px;
                height: 16px;
            }
            QRadioButton#groupButton::indicator:unchecked {
                border: 2px solid #d1d1d6;
                border-radius: 8px;
                background-color: white;
            }
            QRadioButton#groupButton::indicator:checked {
                border: 2px solid #007aff;
                border-radius: 8px;
                background-color: #007aff;
            }
        """)
        
        # 连接信号
        self.group_buttons.idClicked.connect(self.handle_group_changed)
        
    def handle_group_changed(self, button_id: int):
        """处理分组方式改变"""
        group_types = ["none", "status", "platform", "date"]
        if 0 <= button_id < len(group_types):
            self.group_changed.emit(group_types[button_id])


class BatchOperationWidget(QWidget):
    """批量操作控件"""
    
    batch_action = Signal(str)  # 批量操作信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_count = 0
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(8)
        
        # 全选复选框
        self.select_all_checkbox = QCheckBox("全选")
        self.select_all_checkbox.setObjectName("selectAllCheckbox")
        self.select_all_checkbox.setStyleSheet("""
            #selectAllCheckbox {
                font-size: 13px;
                color: #1d1d1f;
                spacing: 6px;
            }
            #selectAllCheckbox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #d1d1d6;
                border-radius: 4px;
                background-color: white;
            }
            #selectAllCheckbox::indicator:checked {
                border-color: #007aff;
                background-color: #007aff;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xMC42IDEuNEw0LjIgNy44TDEuNCA1IiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
            }
        """)
        layout.addWidget(self.select_all_checkbox)
        
        # 选中数量标签
        self.selection_label = QLabel("已选中 0 个任务")
        self.selection_label.setStyleSheet("font-size: 13px; color: #8e8e93;")
        layout.addWidget(self.selection_label)
        
        layout.addStretch()
        
        # 批量操作按钮
        self.start_all_btn = QPushButton("开始全部")
        self.start_all_btn.setObjectName("batchButton")
        self.start_all_btn.clicked.connect(lambda: self.batch_action.emit("start_all"))
        layout.addWidget(self.start_all_btn)
        
        self.pause_all_btn = QPushButton("暂停全部")
        self.pause_all_btn.setObjectName("batchButton")
        self.pause_all_btn.clicked.connect(lambda: self.batch_action.emit("pause_all"))
        layout.addWidget(self.pause_all_btn)
        
        self.delete_selected_btn = QPushButton("删除选中")
        self.delete_selected_btn.setObjectName("batchButton")
        self.delete_selected_btn.clicked.connect(lambda: self.batch_action.emit("delete_selected"))
        layout.addWidget(self.delete_selected_btn)
        
        self.clear_completed_btn = QPushButton("清除已完成")
        self.clear_completed_btn.setObjectName("batchButton")
        self.clear_completed_btn.clicked.connect(lambda: self.batch_action.emit("clear_completed"))
        layout.addWidget(self.clear_completed_btn)
        
        # 设置按钮样式
        self.setStyleSheet("""
            QPushButton#batchButton {
                padding: 6px 12px;
                border: 1px solid rgba(0, 122, 255, 0.3);
                border-radius: 6px;
                background-color: rgba(0, 122, 255, 0.1);
                color: #007aff;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton#batchButton:hover {
                background-color: rgba(0, 122, 255, 0.2);
            }
            QPushButton#batchButton:pressed {
                background-color: rgba(0, 122, 255, 0.3);
            }
            QPushButton#batchButton:disabled {
                background-color: rgba(0, 0, 0, 0.05);
                color: #8e8e93;
                border-color: rgba(0, 0, 0, 0.1);
            }
        """)
        
        # 连接信号
        self.select_all_checkbox.toggled.connect(self.handle_select_all)
        
        # 初始状态
        self.update_button_states()
        
    def handle_select_all(self, checked: bool):
        """处理全选"""
        self.batch_action.emit("select_all" if checked else "deselect_all")
        
    def update_selection_count(self, count: int, total: int):
        """更新选中数量"""
        self.selected_count = count
        self.selection_label.setText(f"已选中 {count} 个任务 (共 {total} 个)")
        
        # 更新全选复选框状态
        if count == 0:
            self.select_all_checkbox.setCheckState(Qt.Unchecked)
        elif count == total:
            self.select_all_checkbox.setCheckState(Qt.Checked)
        else:
            self.select_all_checkbox.setCheckState(Qt.PartiallyChecked)
            
        self.update_button_states()
        
    def update_button_states(self):
        """更新按钮状态"""
        has_selection = self.selected_count > 0
        self.delete_selected_btn.setEnabled(has_selection)


class DownloadListWidget(QWidget):
    """增强的下载列表组件 - 支持分组、筛选、批量操作、虚拟列表优化"""
    
    task_selected = Signal(str)  # 任务ID
    task_action = Signal(str, str)  # 任务ID, 动作
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tasks = {}  # 存储任务卡片 {task_id: {'card': card, 'item': item, 'metadata': dict}}
        self.filtered_tasks = {}  # 筛选后的任务
        self.grouped_tasks = {}  # 分组后的任务
        self.current_filters = {}  # 当前筛选条件
        self.current_group = "none"  # 当前分组方式
        self.selected_tasks = set()  # 选中的任务ID
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """设置用户界面"""
        self.setObjectName("downloadListWidget")
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 20)
        layout.setSpacing(8)
        
        # 标题区域
        header = self.create_header()
        layout.addWidget(header)
        
        # 筛选控件
        self.filter_widget = TaskFilterWidget()
        layout.addWidget(self.filter_widget)
        
        # 分组控件
        self.group_widget = TaskGroupWidget()
        layout.addWidget(self.group_widget)
        
        # 批量操作控件
        self.batch_widget = BatchOperationWidget()
        layout.addWidget(self.batch_widget)
        
        # 分隔线
        separator = QFrame()
        separator.setProperty("class", "separator")
        separator.setFixedHeight(1)
        separator.setStyleSheet("""
            QFrame[class="separator"] {
                background-color: rgba(0, 0, 0, 0.1);
                border: none;
            }
        """)
        layout.addWidget(separator)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setObjectName("downloadScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("""
            QScrollArea#downloadScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: rgba(0, 0, 0, 0.05);
                width: 8px;
                border-radius: 4px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(0, 0, 0, 0.2);
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: rgba(0, 0, 0, 0.3);
            }
        """)
        
        # 虚拟任务列表
        self.task_list = VirtualTaskList()
        self.task_list.setObjectName("taskList")
        self.task_list.setSpacing(8)
        
        scroll_area.setWidget(self.task_list)
        layout.addWidget(scroll_area, 1)
        
    def setup_connections(self):
        """设置信号连接"""
        # 筛选信号
        self.filter_widget.filter_changed.connect(self.apply_filters)
        
        # 分组信号
        self.group_widget.group_changed.connect(self.apply_grouping)
        
        # 批量操作信号
        self.batch_widget.batch_action.connect(self.handle_batch_action)
        
        # 任务列表信号
        self.task_list.item_order_changed.connect(self.handle_order_changed)
        self.task_list.itemSelectionChanged.connect(self.handle_selection_changed)
        
    def create_header(self):
        """创建标题区域"""
        header = QFrame()
        header.setObjectName("downloadListHeader")
        header.setFixedHeight(40)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 8, 0, 8)
        
        title_label = QLabel("下载列表")
        title_label.setObjectName("downloadListTitle")
        title_label.setStyleSheet("""
            #downloadListTitle {
                font-size: 16px;
                font-weight: 600;
                color: #1d1d1f;
            }
        """)
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # 任务统计
        self.stats_label = QLabel("共 0 个任务")
        self.stats_label.setStyleSheet("font-size: 13px; color: #8e8e93;")
        layout.addWidget(self.stats_label)
        
        return header
        
    def add_task(self, url: str, metadata: dict = None):
        """添加下载任务"""
        # 创建任务卡片
        task_card = DownloadTaskCard(url, metadata)
        task_id = task_card.task_id
        
        # 提取平台信息
        platform = self.extract_platform_from_url(url)
        
        # 存储任务信息
        task_info = {
            'card': task_card,
            'item': None,
            'metadata': {
                'url': url,
                'platform': platform,
                'status': 'waiting',
                'created_at': __import__('datetime').datetime.now(),
                **(metadata or {})
            }
        }
        
        self.tasks[task_id] = task_info
        
        # 连接信号
        task_card.action_requested.connect(
            lambda action, tid=task_id: self.task_action.emit(tid, action)
        )
        task_card.selected.connect(
            lambda tid=task_id: self.task_selected.emit(tid)
        )
        
        # 刷新显示
        self.refresh_display()
        
        return task_id
        
    def remove_task(self, task_id: str):
        """移除任务"""
        if task_id in self.tasks:
            task_info = self.tasks[task_id]
            if task_info['item']:
                row = self.task_list.row(task_info['item'])
                if row >= 0:
                    self.task_list.takeItem(row)
            del self.tasks[task_id]
            
            # 从选中列表中移除
            self.selected_tasks.discard(task_id)
            
            # 刷新显示
            self.refresh_display()
            
    def update_task_progress(self, task_id: str, progress: float, speed: str = ""):
        """更新任务进度"""
        if task_id in self.tasks:
            self.tasks[task_id]['card'].update_progress(progress, speed)
            
    def update_task_status(self, task_id: str, status: str):
        """更新任务状态"""
        if task_id in self.tasks:
            self.tasks[task_id]['card'].update_status(status)
            self.tasks[task_id]['metadata']['status'] = status
            
            # 如果状态改变可能影响筛选结果，刷新显示
            if self.current_filters.get('status', '全部状态') != '全部状态':
                self.refresh_display()
                
    def apply_filters(self, filters: dict):
        """应用筛选条件"""
        self.current_filters = filters
        self.refresh_display()
        
    def apply_grouping(self, group_type: str):
        """应用分组"""
        self.current_group = group_type
        self.refresh_display()
        
    def handle_batch_action(self, action: str):
        """处理批量操作"""
        if action == "select_all":
            self.select_all_tasks(True)
        elif action == "deselect_all":
            self.select_all_tasks(False)
        elif action == "start_all":
            self.batch_start_tasks()
        elif action == "pause_all":
            self.batch_pause_tasks()
        elif action == "delete_selected":
            self.delete_selected_tasks()
        elif action == "clear_completed":
            self.clear_completed_tasks()
            
    def handle_order_changed(self):
        """处理任务顺序改变"""
        # 更新任务顺序
        new_order = []
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            widget = self.task_list.itemWidget(item)
            if widget and hasattr(widget, 'task_id'):
                new_order.append(widget.task_id)
                
        # 这里可以保存新的顺序到配置或数据库
        print(f"任务顺序已更改: {new_order}")
        
    def handle_selection_changed(self):
        """处理选择改变"""
        selected_items = self.task_list.selectedItems()
        self.selected_tasks.clear()
        
        for item in selected_items:
            widget = self.task_list.itemWidget(item)
            if widget and hasattr(widget, 'task_id'):
                self.selected_tasks.add(widget.task_id)
                
        # 更新批量操作控件
        self.batch_widget.update_selection_count(
            len(self.selected_tasks), 
            len(self.filtered_tasks)
        )
        
    def refresh_display(self):
        """刷新显示"""
        # 应用筛选
        self.apply_task_filters()
        
        # 应用分组
        self.apply_task_grouping()
        
        # 更新列表显示
        self.update_list_display()
        
        # 更新统计信息
        self.update_stats()
        
    def apply_task_filters(self):
        """应用任务筛选"""
        self.filtered_tasks = {}
        
        for task_id, task_info in self.tasks.items():
            if self.task_matches_filters(task_info):
                self.filtered_tasks[task_id] = task_info
                
    def task_matches_filters(self, task_info: dict) -> bool:
        """检查任务是否匹配筛选条件"""
        metadata = task_info['metadata']
        
        # 搜索筛选
        search_text = self.current_filters.get('search', '').lower()
        if search_text:
            title = metadata.get('title', '').lower()
            author = metadata.get('author', '').lower()
            url = metadata.get('url', '').lower()
            
            if not (search_text in title or search_text in author or search_text in url):
                return False
                
        # 状态筛选
        status_filter = self.current_filters.get('status', '全部状态')
        if status_filter != '全部状态':
            status_map = {
                '等待中': 'waiting',
                '下载中': 'downloading', 
                '已暂停': 'paused',
                '已完成': 'completed',
                '出错': 'error'
            }
            if metadata.get('status') != status_map.get(status_filter):
                return False
                
        # 平台筛选
        platform_filter = self.current_filters.get('platform', '全部平台')
        if platform_filter != '全部平台':
            if metadata.get('platform') != platform_filter:
                return False
                
        return True
        
    def apply_task_grouping(self):
        """应用任务分组"""
        self.grouped_tasks = {}
        
        if self.current_group == "none":
            self.grouped_tasks["所有任务"] = list(self.filtered_tasks.values())
        elif self.current_group == "status":
            self.group_by_status()
        elif self.current_group == "platform":
            self.group_by_platform()
        elif self.current_group == "date":
            self.group_by_date()
            
    def group_by_status(self):
        """按状态分组"""
        status_groups = {
            'waiting': '等待中',
            'downloading': '下载中',
            'paused': '已暂停', 
            'completed': '已完成',
            'error': '出错'
        }
        
        for task_info in self.filtered_tasks.values():
            status = task_info['metadata'].get('status', 'waiting')
            group_name = status_groups.get(status, '其他')
            
            if group_name not in self.grouped_tasks:
                self.grouped_tasks[group_name] = []
            self.grouped_tasks[group_name].append(task_info)
            
    def group_by_platform(self):
        """按平台分组"""
        for task_info in self.filtered_tasks.values():
            platform = task_info['metadata'].get('platform', '其他')
            
            if platform not in self.grouped_tasks:
                self.grouped_tasks[platform] = []
            self.grouped_tasks[platform].append(task_info)
            
    def group_by_date(self):
        """按日期分组"""
        import datetime
        today = datetime.date.today()
        
        for task_info in self.filtered_tasks.values():
            created_at = task_info['metadata'].get('created_at', datetime.datetime.now())
            if isinstance(created_at, datetime.datetime):
                task_date = created_at.date()
            else:
                task_date = today
                
            if task_date == today:
                group_name = "今天"
            elif task_date == today - datetime.timedelta(days=1):
                group_name = "昨天"
            elif task_date >= today - datetime.timedelta(days=7):
                group_name = "本周"
            else:
                group_name = "更早"
                
            if group_name not in self.grouped_tasks:
                self.grouped_tasks[group_name] = []
            self.grouped_tasks[group_name].append(task_info)
            
    def update_list_display(self):
        """更新列表显示"""
        # 清空当前列表
        self.task_list.clear()
        
        # 按分组添加任务
        for group_name, tasks in self.grouped_tasks.items():
            # 如果有分组且不是"所有任务"，添加分组标题
            if len(self.grouped_tasks) > 1 and group_name != "所有任务":
                self.add_group_header(group_name, len(tasks))
                
            # 添加任务卡片
            for task_info in tasks:
                self.add_task_to_list(task_info)
                
    def add_group_header(self, group_name: str, count: int):
        """添加分组标题"""
        header_widget = QWidget()
        header_widget.setObjectName("groupHeader")
        header_widget.setFixedHeight(32)
        header_widget.setStyleSheet("""
            QWidget#groupHeader {
                background-color: rgba(0, 0, 0, 0.05);
                border-radius: 6px;
                margin: 4px 0px;
            }
        """)
        
        layout = QHBoxLayout(header_widget)
        layout.setContentsMargins(12, 6, 12, 6)
        
        title_label = QLabel(f"{group_name} ({count})")
        title_label.setStyleSheet("""
            font-size: 13px;
            font-weight: 600;
            color: #1d1d1f;
        """)
        layout.addWidget(title_label)
        layout.addStretch()
        
        # 创建列表项
        item = QListWidgetItem()
        item.setSizeHint(header_widget.sizeHint())
        
        self.task_list.addItem(item)
        self.task_list.setItemWidget(item, header_widget)
        
    def add_task_to_list(self, task_info: dict):
        """添加任务到列表"""
        task_card = task_info['card']
        
        # 创建列表项
        item = QListWidgetItem()
        item.setSizeHint(task_card.sizeHint())
        
        # 添加到列表
        self.task_list.addItem(item)
        self.task_list.setItemWidget(item, task_card)
        
        # 更新任务信息中的item引用
        task_info['item'] = item
        
    def update_stats(self):
        """更新统计信息"""
        total_count = len(self.tasks)
        filtered_count = len(self.filtered_tasks)
        
        if total_count == filtered_count:
            self.stats_label.setText(f"共 {total_count} 个任务")
        else:
            self.stats_label.setText(f"显示 {filtered_count} / {total_count} 个任务")
            
    def extract_platform_from_url(self, url: str) -> str:
        """从URL提取平台信息"""
        url_lower = url.lower()
        
        if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'YouTube'
        elif 'bilibili.com' in url_lower:
            return 'B站'
        elif 'douyin.com' in url_lower or 'tiktok.com' in url_lower:
            return '抖音'
        elif 'instagram.com' in url_lower:
            return 'Instagram'
        else:
            return '其他'
            
    def select_all_tasks(self, select: bool):
        """全选/取消全选任务"""
        if select:
            self.task_list.selectAll()
        else:
            self.task_list.clearSelection()
            
    def batch_start_tasks(self):
        """批量开始任务"""
        for task_id in self.selected_tasks:
            self.task_action.emit(task_id, "start")
            
    def batch_pause_tasks(self):
        """批量暂停任务"""
        for task_id in self.selected_tasks:
            self.task_action.emit(task_id, "pause")
            
    def delete_selected_tasks(self):
        """删除选中的任务"""
        for task_id in list(self.selected_tasks):
            self.remove_task(task_id)
            
    def clear_completed_tasks(self):
        """清除已完成的任务"""
        completed_tasks = []
        for task_id, task_info in self.tasks.items():
            if task_info['metadata'].get('status') == 'completed':
                completed_tasks.append(task_id)
                
        for task_id in completed_tasks:
            self.remove_task(task_id)
            
    def get_task_count(self) -> int:
        """获取任务数量"""
        return len(self.tasks)
        
    def get_selected_tasks(self) -> Set[str]:
        """获取选中的任务ID"""
        return self.selected_tasks.copy()

# Backward compatibility alias
DraggableTaskList = VirtualTaskList