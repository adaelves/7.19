"""
macOS风格UI控件库 - 完全符合Apple设计规范
严格按照macOS Human Interface Guidelines实现
"""
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *


class MacOSButton(QPushButton):
    """macOS标准按钮 - 完全符合Apple设计规范"""
    
    def __init__(self, text="", button_type="primary"):
        super().__init__(text)
        self.button_type = button_type
        self.setup_style()
        self.setup_animations()
        
    def setup_style(self):
        """设置按钮样式 - 符合macOS标准"""
        if self.button_type == "primary":
            self.setStyleSheet("""
                QPushButton {
                    background-color: #007AFF;
                    border: none;
                    border-radius: 8px;
                    color: white;
                    font-family: 'SF Pro Text', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI';
                    font-size: 13pt;
                    font-weight: 500;
                    padding: 8px 16px;
                    min-height: 20px;
                }
                QPushButton:hover {
                    background-color: #1E88FF;
                }
                QPushButton:pressed {
                    background-color: #0051D5;
                }
                QPushButton:disabled {
                    background-color: #E5E5E7;
                    color: #8E8E93;
                }
            """)
        elif self.button_type == "secondary":
            self.setStyleSheet("""
                QPushButton {
                    background-color: #F2F2F7;
                    border: 1px solid #E2E2E2;
                    border-radius: 8px;
                    color: #007AFF;
                    font-family: 'SF Pro Text', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI';
                    font-size: 13pt;
                    font-weight: 500;
                    padding: 8px 16px;
                    min-height: 20px;
                }
                QPushButton:hover {
                    background-color: #E8E8E8;
                    border-color: #D1D1D6;
                }
                QPushButton:pressed {
                    background-color: #D1D1D6;
                }
            """)
            
    def setup_animations(self):
        """设置动画效果 - 200ms标准过渡"""
        self.setStyleSheet(self.styleSheet() + """
            QPushButton {
                transition: all 200ms ease-in-out;
            }
        """)


class MacOSLineEdit(QLineEdit):
    """macOS标准输入框 - 完全符合Apple设计规范"""
    
    def __init__(self, placeholder=""):
        super().__init__()
        if placeholder:
            self.setPlaceholderText(placeholder)
        self.setup_style()
        
    def setup_style(self):
        """设置输入框样式 - 符合macOS标准"""
        self.setStyleSheet("""
            QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #E2E2E2;
                border-radius: 10px;
                padding: 8px 12px;
                font-family: 'SF Pro Text', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI';
                font-size: 13pt;
                color: #1D1D1F;
                selection-background-color: #007AFF;
                transition: all 200ms ease-in-out;
            }
            QLineEdit:focus {
                border-color: #007AFF;
                outline: none;
            }
            QLineEdit:hover {
                border-color: #D1D1D6;
            }
            QLineEdit::placeholder {
                color: #86868B;
            }
        """)


class MacOSProgressBar(QProgressBar):
    """macOS标准进度条 - 完全符合Apple设计规范"""
    
    def __init__(self):
        super().__init__()
        self.setup_style()
        
    def setup_style(self):
        """设置进度条样式 - 符合macOS标准"""
        self.setStyleSheet("""
            QProgressBar {
                background-color: #F2F2F7;
                border: none;
                border-radius: 4px;
                height: 8px;
                text-align: center;
                font-family: 'SF Pro Text', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI';
                font-size: 11pt;
                color: #86868B;
            }
            QProgressBar::chunk {
                background-color: #34C759;
                border-radius: 4px;
            }
        """)


class MacOSCard(QFrame):
    """macOS标准卡片容器 - 完全符合Apple设计规范"""
    
    def __init__(self):
        super().__init__()
        self.setup_style()
        self.setup_shadow()
        
    def setup_style(self):
        """设置卡片样式 - 符合macOS标准"""
        self.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E2E2E2;
                border-radius: 10px;
                padding: 16px;
            }
        """)
        self.setFrameStyle(QFrame.NoFrame)
        
    def setup_shadow(self):
        """设置阴影效果 - 模糊半径15px，透明度20%，偏移量(0,2px)"""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 51))  # 20%透明度
        self.setGraphicsEffect(shadow)


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
    """macOS标准列表控件 - 完全符合Apple设计规范"""
    
    def __init__(self):
        super().__init__()
        self.setup_style()
        
    def setup_style(self):
        """设置列表样式 - 符合macOS标准"""
        self.setStyleSheet("""
            QListWidget {
                background-color: #FFFFFF;
                border: 1px solid #E2E2E2;
                border-radius: 10px;
                outline: none;
                padding: 4px;
                font-family: 'SF Pro Text', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI';
                font-size: 13pt;
            }
            QListWidget::item {
                background-color: transparent;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                margin: 2px;
                color: #1D1D1F;
                min-height: 32px;
                transition: all 200ms ease-in-out;
            }
            QListWidget::item:selected {
                background-color: #007AFF;
                color: white;
            }
            QListWidget::item:hover:!selected {
                background-color: #F0F0F0;
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


class MacOSTrafficLightButton(QPushButton):
    """macOS交通灯按钮 - 完全符合Apple设计规范"""
    
    def __init__(self, button_type="close", parent=None):
        super().__init__(parent)
        self.button_type = button_type
        self.setup_style()
        
    def setup_style(self):
        """设置交通灯按钮样式"""
        self.setFixedSize(12, 12)
        
        colors = {
            "close": {
                "normal": "#FF3B30",
                "hover": "#FF453A", 
                "pressed": "#E02020"
            },
            "minimize": {
                "normal": "#FFCC00",
                "hover": "#FFD60A",
                "pressed": "#E6B800"
            },
            "maximize": {
                "normal": "#34C759",
                "hover": "#32D74B",
                "pressed": "#2DB24E"
            }
        }
        
        color_set = colors.get(self.button_type, colors["close"])
        
        self.setStyleSheet(f"""
            QPushButton {{
                border-radius: 6px;
                background-color: {color_set["normal"]};
                border: none;
            }}
            QPushButton:hover {{
                background-color: {color_set["hover"]};
            }}
            QPushButton:pressed {{
                background-color: {color_set["pressed"]};
            }}
        """)


class MacOSLabel(QLabel):
    """macOS原生风格标签"""
    
    def __init__(self, text="", font_size=13, font_weight="normal", parent=None):
        super().__init__(text, parent)
        self.font_size = font_size
        self.font_weight = font_weight
        self.setup_style()
        
    def setup_style(self):
        """设置标签样式"""
        weight = "500" if self.font_weight == "medium" else "600" if self.font_weight == "bold" else "400"
        self.setStyleSheet(f"""
            QLabel {{
                color: #1D1D1F;
                background-color: transparent;
                font-family: 'SF Pro Text', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI';
                font-size: {self.font_size}pt;
                font-weight: {weight};
            }}
        """)


class MacOSTitleLabel(QLabel):
    """macOS标题标签"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setup_style()
        
    def setup_style(self):
        """设置标题样式"""
        self.setStyleSheet("""
            QLabel {
                color: #1D1D1F;
                font-family: 'SF Pro Display', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI';
                font-size: 13pt;
                font-weight: 500;
                background-color: transparent;
            }
        """)


class MacOSFrame(QFrame):
    """macOS原生风格框架"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_style()
        
    def setup_style(self):
        """设置框架样式"""
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.8);
                border-radius: 10px;
                border: 1px solid rgba(0, 0, 0, 0.05);
            }
        """)


class MacOSThemeManager:
    """macOS主题管理器 - 支持浅色和深色主题"""
    
    def __init__(self):
        self.current_theme = "light"
        
    def get_colors(self, theme="light"):
        """获取主题颜色"""
        if theme == "dark":
            return {
                # 深色主题颜色
                "background": "#1C1C1E",
                "text": "#F5F5F7", 
                "secondary_text": "#AEAEB2",
                "accent": "#007AFF",
                "success": "#34C759",
                "warning": "#FFCC00",
                "error": "#FF3B30",
                "separator": "#38383A",
                "card_background": "#2C2C2E",
                "input_background": "#1C1C1E",
                "input_border": "#38383A",
                "hover_background": "#3A3A3C"
            }
        else:
            return {
                # 浅色主题颜色
                "background": "#FFFFFF",
                "text": "#1D1D1F",
                "secondary_text": "#86868B", 
                "accent": "#007AFF",
                "success": "#34C759",
                "warning": "#FFCC00",
                "error": "#FF3B30",
                "separator": "#E2E2E2",
                "card_background": "#FFFFFF",
                "input_background": "#FFFFFF",
                "input_border": "#E2E2E2",
                "hover_background": "#F0F0F0"
            }
    
    def get_fonts(self):
        """获取字体配置"""
        return {
            "title": {
                "family": "'SF Pro Display', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI'",
                "size": "13-16pt",
                "weight": "600"
            },
            "body": {
                "family": "'SF Pro Text', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI'",
                "size": "12-13pt", 
                "weight": "400"
            },
            "caption": {
                "family": "'SF Pro Text', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI'",
                "size": "11pt",
                "weight": "400"
            },
            "button": {
                "family": "'SF Pro Text', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI'",
                "size": "13pt",
                "weight": "500"
            }
        }
    
    def get_animations(self):
        """获取动画配置"""
        return {
            "transition_duration": "200ms",
            "easing": "ease-in-out",
            "spring_damping": 0.7,
            "spring_stiffness": 300
        }
    
    def get_dimensions(self):
        """获取尺寸配置"""
        return {
            "border_radius": "10px",
            "button_radius": "8px", 
            "shadow_blur": "15px",
            "shadow_opacity": "20%",
            "shadow_offset": "(0,2px)",
            "titlebar_height": "29px",  # 22pt
            "list_item_height": "32px",
            "separator_width": "1px"
        }


class MacOSThemedButton(MacOSButton):
    """支持主题的macOS按钮"""
    
    def __init__(self, text="", button_type="primary", theme="light"):
        self.theme = theme
        super().__init__(text, button_type)
        
    def setup_style(self):
        """设置主题化按钮样式"""
        theme_manager = MacOSThemeManager()
        colors = theme_manager.get_colors(self.theme)
        fonts = theme_manager.get_fonts()
        
        if self.button_type == "primary":
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors['accent']};
                    border: none;
                    border-radius: 8px;
                    color: white;
                    font-family: {fonts['button']['family']};
                    font-size: {fonts['button']['size']};
                    font-weight: {fonts['button']['weight']};
                    padding: 8px 16px;
                    min-height: 20px;
                    transition: all 200ms ease-in-out;
                }}
                QPushButton:hover {{
                    background-color: #1E88FF;
                }}
                QPushButton:pressed {{
                    background-color: #0051D5;
                }}
                QPushButton:disabled {{
                    background-color: #E5E5E7;
                    color: #8E8E93;
                }}
            """)
        elif self.button_type == "secondary":
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors['card_background']};
                    border: 1px solid {colors['separator']};
                    border-radius: 8px;
                    color: {colors['accent']};
                    font-family: {fonts['button']['family']};
                    font-size: {fonts['button']['size']};
                    font-weight: {fonts['button']['weight']};
                    padding: 8px 16px;
                    min-height: 20px;
                    transition: all 200ms ease-in-out;
                }}
                QPushButton:hover {{
                    background-color: {colors['hover_background']};
                }}
                QPushButton:pressed {{
                    background-color: {colors['separator']};
                }}
            """)


class MacOSThemedLineEdit(MacOSLineEdit):
    """支持主题的macOS输入框"""
    
    def __init__(self, placeholder="", theme="light"):
        self.theme = theme
        super().__init__(placeholder)
        
    def setup_style(self):
        """设置主题化输入框样式"""
        theme_manager = MacOSThemeManager()
        colors = theme_manager.get_colors(self.theme)
        fonts = theme_manager.get_fonts()
        
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors['input_background']};
                border: 1px solid {colors['input_border']};
                border-radius: 10px;
                padding: 8px 12px;
                font-family: {fonts['body']['family']};
                font-size: {fonts['body']['size']};
                color: {colors['text']};
                selection-background-color: {colors['accent']};
                transition: all 200ms ease-in-out;
            }}
            QLineEdit:focus {{
                border-color: {colors['accent']};
                outline: none;
            }}
            QLineEdit:hover {{
                border-color: {colors['separator']};
            }}
            QLineEdit::placeholder {{
                color: {colors['secondary_text']};
            }}
        """)


class MacOSWindow(QMainWindow):
    """macOS风格主窗口 - 完全符合设计标准"""
    
    def __init__(self, theme="light"):
        super().__init__()
        self.theme = theme
        self.setup_style()
        
    def setup_style(self):
        """设置macOS窗口样式"""
        theme_manager = MacOSThemeManager()
        colors = theme_manager.get_colors(self.theme)
        dimensions = theme_manager.get_dimensions()
        
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {colors['background']};
                border-radius: {dimensions['border_radius']};
            }}
            QMenuBar {{
                background: transparent;
                border: none;
                color: {colors['text']};
                font-size: 14px;
                height: {dimensions['titlebar_height']};
            }}
            QMenuBar::item {{
                background: transparent;
                padding: 4px 8px;
                border-radius: 4px;
                transition: all 200ms ease-in-out;
            }}
            QMenuBar::item:selected {{
                background-color: {colors['hover_background']};
            }}
            QStatusBar {{
                background: transparent;
                border: none;
                color: {colors['secondary_text']};
                font-size: 12px;
            }}
        """)
        
        # 设置窗口属性以获得macOS外观
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | 
                           Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
        
        # 在macOS上启用统一标题栏和工具栏
        if hasattr(self, 'setUnifiedTitleAndToolBarOnMac'):
            self.setUnifiedTitleAndToolBarOnMac(True)
            
        # 设置窗口阴影
        self.setup_window_shadow()
        
    def setup_window_shadow(self):
        """设置窗口阴影效果"""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)  # 模糊半径15px
        shadow.setXOffset(0)
        shadow.setYOffset(2)      # 偏移量(0,2px)
        shadow.setColor(QColor(0, 0, 0, 51))  # 20%透明度
        self.setGraphicsEffect(shadow)