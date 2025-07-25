"""
macOS-style UI widgets and components
"""
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *


class MacOSButton(QPushButton):
    """macOS-style button"""
    
    def __init__(self, text="", button_type="primary"):
        super().__init__(text)
        self.button_type = button_type
        self.setup_style()
        
    def setup_style(self):
        """Setup macOS button style"""
        if self.button_type == "primary":
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #007AFF, stop:1 #0051D5);
                    border: none;
                    border-radius: 8px;
                    color: white;
                    font-weight: 600;
                    font-size: 14px;
                    padding: 8px 16px;
                    min-height: 20px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #1E88FF, stop:1 #0A5AE6);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #0051D5, stop:1 #003A9F);
                }
                QPushButton:disabled {
                    background: #E5E5E7;
                    color: #8E8E93;
                }
            """)
        elif self.button_type == "secondary":
            self.setStyleSheet("""
                QPushButton {
                    background: #F2F2F7;
                    border: 1px solid #D1D1D6;
                    border-radius: 8px;
                    color: #007AFF;
                    font-weight: 600;
                    font-size: 14px;
                    padding: 8px 16px;
                    min-height: 20px;
                }
                QPushButton:hover {
                    background: #E5E5EA;
                    border-color: #C7C7CC;
                }
                QPushButton:pressed {
                    background: #D1D1D6;
                }
            """)


class MacOSLineEdit(QLineEdit):
    """macOS-style line edit"""
    
    def __init__(self, placeholder=""):
        super().__init__()
        if placeholder:
            self.setPlaceholderText(placeholder)
        self.setup_style()
        
    def setup_style(self):
        """Setup macOS line edit style"""
        self.setStyleSheet("""
            QLineEdit {
                background: white;
                border: 2px solid #E5E5E7;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                color: #1C1C1E;
                selection-background-color: #007AFF;
            }
            QLineEdit:focus {
                border-color: #007AFF;
                outline: none;
            }
            QLineEdit:hover {
                border-color: #D1D1D6;
            }
        """)


class MacOSProgressBar(QProgressBar):
    """macOS-style progress bar"""
    
    def __init__(self):
        super().__init__()
        self.setup_style()
        
    def setup_style(self):
        """Setup macOS progress bar style"""
        self.setStyleSheet("""
            QProgressBar {
                background: #F2F2F7;
                border: none;
                border-radius: 4px;
                height: 8px;
                text-align: center;
                font-size: 12px;
                color: #8E8E93;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #34C759, stop:1 #30B350);
                border-radius: 4px;
            }
        """)


class MacOSCard(QFrame):
    """macOS-style card container"""
    
    def __init__(self):
        super().__init__()
        self.setup_style()
        
    def setup_style(self):
        """Setup macOS card style"""
        self.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #E5E5E7;
                border-radius: 12px;
                padding: 16px;
            }
        """)
        self.setFrameStyle(QFrame.NoFrame)


class MacOSTabWidget(QTabWidget):
    """macOS-style tab widget"""
    
    def __init__(self):
        super().__init__()
        self.setup_style()
        
    def setup_style(self):
        """Setup macOS tab widget style"""
        self.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: #F2F2F7;
                border-radius: 12px;
                margin-top: 8px;
            }
            QTabWidget::tab-bar {
                alignment: center;
            }
            QTabBar::tab {
                background: transparent;
                color: #8E8E93;
                padding: 8px 20px;
                margin: 0px 4px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
                min-width: 80px;
            }
            QTabBar::tab:selected {
                background: white;
                color: #007AFF;
                border: 1px solid #E5E5E7;
            }
            QTabBar::tab:hover:!selected {
                background: #E5E5EA;
                color: #1C1C1E;
            }
        """)


class MacOSListWidget(QListWidget):
    """macOS-style list widget"""
    
    def __init__(self):
        super().__init__()
        self.setup_style()
        
    def setup_style(self):
        """Setup macOS list widget style"""
        self.setStyleSheet("""
            QListWidget {
                background: white;
                border: 1px solid #E5E5E7;
                border-radius: 8px;
                outline: none;
                padding: 4px;
            }
            QListWidget::item {
                background: transparent;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                margin: 2px;
                color: #1C1C1E;
            }
            QListWidget::item:selected {
                background: #007AFF;
                color: white;
            }
            QListWidget::item:hover:!selected {
                background: #F2F2F7;
            }
        """)


class MacOSScrollArea(QScrollArea):
    """macOS-style scroll area"""
    
    def __init__(self):
        super().__init__()
        self.setup_style()
        
    def setup_style(self):
        """Setup macOS scroll area style"""
        self.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                border-radius: 4px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #C7C7CC;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #8E8E93;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """)


class DownloadTaskCard(MacOSCard):
    """Download task card widget"""
    
    cancel_requested = Signal(str)  # url
    
    def __init__(self, url: str, task_data: dict):
        super().__init__()
        self.url = url
        self.task_data = task_data
        self.setup_ui()
        self.update_task_data(task_data)
        
    def setup_ui(self):
        """Setup task card UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Header with title and cancel button
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel("Loading...")
        self.title_label.setStyleSheet("""
            QLabel {
                font-weight: 600;
                font-size: 16px;
                color: #1C1C1E;
            }
        """)
        
        self.cancel_button = MacOSButton("✕", "secondary")
        self.cancel_button.setFixedSize(24, 24)
        self.cancel_button.clicked.connect(lambda: self.cancel_requested.emit(self.url))
        
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.cancel_button)
        
        # Progress bar
        self.progress_bar = MacOSProgressBar()
        
        # Status and info
        info_layout = QHBoxLayout()
        
        self.status_label = QLabel("Pending")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #8E8E93;
            }
        """)
        
        self.speed_label = QLabel("")
        self.speed_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #8E8E93;
            }
        """)
        
        info_layout.addWidget(self.status_label)
        info_layout.addStretch()
        info_layout.addWidget(self.speed_label)
        
        # Add to layout
        layout.addLayout(header_layout)
        layout.addWidget(self.progress_bar)
        layout.addLayout(info_layout)
        
    def update_task_data(self, task_data: dict):
        """Update task data"""
        self.task_data = task_data
        
        # Update title
        title = task_data.get('title') or task_data.get('filename') or self.url
        if len(title) > 50:
            title = title[:47] + "..."
        self.title_label.setText(title)
        
        # Update progress
        progress = task_data.get('progress', 0)
        self.progress_bar.setValue(int(progress))
        
        # Update status
        status = task_data.get('status', 'pending')
        if status == 'downloading':
            self.status_label.setText(f"下载中... {progress:.1f}%")
            self.cancel_button.show()
        elif status == 'completed':
            self.status_label.setText("已完成")
            self.cancel_button.hide()
        elif status == 'failed':
            self.status_label.setText(f"失败: {task_data.get('error', 'Unknown error')}")
            self.cancel_button.hide()
        else:
            self.status_label.setText("等待中...")
            self.cancel_button.show()
            
        # Update speed
        speed = task_data.get('speed', '')
        eta = task_data.get('eta', '')
        if speed and eta:
            self.speed_label.setText(f"{speed} • {eta}")
        elif speed:
            self.speed_label.setText(speed)
        else:
            self.speed_label.setText("")


class MacOSWindow(QMainWindow):
    """macOS-style main window"""
    
    def __init__(self):
        super().__init__()
        self.setup_style()
        
    def setup_style(self):
        """Setup macOS window style"""
        self.setStyleSheet("""
            QMainWindow {
                background: #F2F2F7;
            }
            QMenuBar {
                background: transparent;
                border: none;
                color: #1C1C1E;
                font-size: 14px;
            }
            QMenuBar::item {
                background: transparent;
                padding: 4px 8px;
                border-radius: 4px;
            }
            QMenuBar::item:selected {
                background: #E5E5EA;
            }
            QStatusBar {
                background: transparent;
                border: none;
                color: #8E8E93;
                font-size: 12px;
            }
        """)
        
        # Set window properties for macOS-like appearance
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | 
                           Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
        
        # Enable unified title and toolbar on macOS
        if hasattr(self, 'setUnifiedTitleAndToolBarOnMac'):
            self.setUnifiedTitleAndToolBarOnMac(True)