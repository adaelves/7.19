"""
URL输入组件 - macOS风格
"""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QPushButton, 
    QLabel, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence


class URLInputWidget(QWidget):
    """URL输入组件"""
    
    url_submitted = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """设置用户界面"""
        self.setObjectName("urlInputWidget")
        self.setFixedHeight(80)
        
        # 主布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        # URL输入框
        self.url_input = QLineEdit()
        self.url_input.setObjectName("urlInput")
        self.url_input.setPlaceholderText("请输入视频链接...")
        self.url_input.setMinimumHeight(40)
        layout.addWidget(self.url_input, 1)
        
        # 添加按钮
        self.add_button = QPushButton("添加")
        self.add_button.setObjectName("addButton")
        self.add_button.setProperty("class", "primary-button")
        self.add_button.setMinimumSize(80, 40)
        layout.addWidget(self.add_button)
        
        # 粘贴按钮
        self.paste_button = QPushButton("粘贴")
        self.paste_button.setObjectName("pasteButton")
        self.paste_button.setProperty("class", "secondary-button")
        self.paste_button.setMinimumSize(60, 40)
        layout.addWidget(self.paste_button)
        
    def setup_connections(self):
        """设置信号连接"""
        self.add_button.clicked.connect(self.submit_url)
        self.paste_button.clicked.connect(self.paste_from_clipboard)
        self.url_input.returnPressed.connect(self.submit_url)
        
    def submit_url(self):
        """提交URL"""
        url = self.url_input.text().strip()
        if url:
            self.url_submitted.emit(url)
            self.url_input.clear()
            
    def paste_from_clipboard(self):
        """从剪贴板粘贴"""
        from PySide6.QtGui import QGuiApplication
        clipboard = QGuiApplication.clipboard()
        text = clipboard.text().strip()
        if text:
            self.url_input.setText(text)
            
    def set_url(self, url: str):
        """设置URL"""
        self.url_input.setText(url)
        
    def clear(self):
        """清空输入"""
        self.url_input.clear()