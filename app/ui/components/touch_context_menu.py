"""
3D Touch式右键菜单组件 - macOS风格
"""
from PySide6.QtWidgets import (
    QMenu, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QFont, QColor, QPalette


class TouchContextMenuGroup(QWidget):
    """菜单组"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.actions = []
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面"""
        self.setObjectName("touchMenuGroup")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # 组标题
        if self.title:
            title_label = QLabel(self.title)
            title_label.setObjectName("groupTitle")
            title_label.setStyleSheet("""
                #groupTitle {
                    font-size: 11px;
                    font-weight: 600;
                    color: #8e8e93;
                    padding: 4px 12px 2px 12px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
            """)
            layout.addWidget(title_label)
            
    def add_action(self, icon: str, text: str, callback):
        """添加动作"""
        action_widget = TouchContextAction(icon, text, callback)
        self.layout().addWidget(action_widget)
        self.actions.append(action_widget)
        return action_widget


class TouchContextAction(QWidget):
    """菜单动作项"""
    
    def __init__(self, icon: str, text: str, callback, parent=None):
        super().__init__(parent)
        self.icon = icon
        self.text = text
        self.callback = callback
        self.is_hovered = False
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面"""
        self.setObjectName("touchMenuAction")
        self.setFixedHeight(36)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(10)
        
        # 图标
        icon_label = QLabel(self.icon)
        icon_label.setObjectName("actionIcon")
        icon_label.setFixedSize(20, 20)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("""
            #actionIcon {
                font-size: 16px;
                color: #007aff;
            }
        """)
        layout.addWidget(icon_label)
        
        # 文本
        text_label = QLabel(self.text)
        text_label.setObjectName("actionText")
        text_label.setStyleSheet("""
            #actionText {
                font-size: 14px;
                font-weight: 500;
                color: #1d1d1f;
            }
        """)
        layout.addWidget(text_label, 1)
        
        # 设置样式
        self.setStyleSheet("""
            #touchMenuAction {
                background-color: transparent;
                border-radius: 8px;
                margin: 0px 4px;
            }
            #touchMenuAction:hover {
                background-color: rgba(0, 122, 255, 0.1);
            }
        """)
        
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            # 添加按下效果
            self.setStyleSheet("""
                #touchMenuAction {
                    background-color: rgba(0, 122, 255, 0.2);
                    border-radius: 8px;
                    margin: 0px 4px;
                }
            """)
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            # 恢复样式
            self.setStyleSheet("""
                #touchMenuAction {
                    background-color: transparent;
                    border-radius: 8px;
                    margin: 0px 4px;
                }
                #touchMenuAction:hover {
                    background-color: rgba(0, 122, 255, 0.1);
                }
            """)
            
            # 执行回调
            if self.callback:
                self.callback()
                
            # 关闭菜单
            menu = self.parent()
            while menu and not isinstance(menu, TouchContextMenu):
                menu = menu.parent()
            if menu:
                menu.close()
                
        super().mouseReleaseEvent(event)
        
    def enterEvent(self, event):
        """鼠标进入事件"""
        self.is_hovered = True
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """鼠标离开事件"""
        self.is_hovered = False
        super().leaveEvent(event)


class TouchContextMenu(QMenu):
    """3D Touch式上下文菜单"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.groups = []
        self.setup_ui()
        self.setup_animations()
        
    def setup_ui(self):
        """设置用户界面"""
        self.setObjectName("touchContextMenu")
        
        # 设置窗口属性
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 创建主容器
        self.container = QWidget()
        self.container.setObjectName("menuContainer")
        
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        self.main_layout.setSpacing(8)
        
        # 设置样式
        self.container.setStyleSheet("""
            #menuContainer {
                background-color: rgba(255, 255, 255, 0.95);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 12px;
                backdrop-filter: blur(20px);
            }
        """)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 4)
        self.container.setGraphicsEffect(shadow)
        
        # 设置布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.container)
        
    def setup_animations(self):
        """设置动画"""
        self.scale_animation = QPropertyAnimation(self.container, b"geometry")
        self.scale_animation.setDuration(200)
        self.scale_animation.setEasingCurve(QEasingCurve.OutCubic)
        
    def add_group(self, title: str = "") -> TouchContextMenuGroup:
        """添加菜单组"""
        # 如果不是第一个组，添加分隔线
        if self.groups:
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setFrameShadow(QFrame.Sunken)
            separator.setStyleSheet("""
                QFrame {
                    color: rgba(0, 0, 0, 0.1);
                    margin: 4px 8px;
                }
            """)
            self.main_layout.addWidget(separator)
            
        group = TouchContextMenuGroup(title)
        self.main_layout.addWidget(group)
        self.groups.append(group)
        return group
        
    def exec(self, pos):
        """显示菜单"""
        # 调整大小
        self.adjustSize()
        
        # 设置初始位置和大小（用于动画）
        final_rect = QRect(pos.x(), pos.y(), self.width(), self.height())
        start_rect = QRect(
            pos.x() + self.width() // 4,
            pos.y() + self.height() // 4,
            self.width() // 2,
            self.height() // 2
        )
        
        # 设置动画
        self.container.setGeometry(start_rect)
        self.scale_animation.setStartValue(start_rect)
        self.scale_animation.setEndValue(final_rect)
        
        # 显示菜单
        self.move(pos)
        self.show()
        
        # 启动动画
        self.scale_animation.start()
        
        # 执行事件循环
        super().exec(pos)
        
    def showEvent(self, event):
        """显示事件"""
        super().showEvent(event)
        
        # 设置初始透明度
        self.setWindowOpacity(0.0)
        
        # 透明度动画
        from PySide6.QtCore import QTimer
        self.opacity_timer = QTimer()
        self.opacity_value = 0.0
        
        def update_opacity():
            self.opacity_value += 0.1
            if self.opacity_value >= 1.0:
                self.opacity_value = 1.0
                self.opacity_timer.stop()
            self.setWindowOpacity(self.opacity_value)
            
        self.opacity_timer.timeout.connect(update_opacity)
        self.opacity_timer.start(20)  # 50fps