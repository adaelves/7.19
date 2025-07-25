"""
macOS动画系统 - 符合Apple标准的动画效果
"""
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtWidgets import QGraphicsOpacityEffect


class MacOSAnimationHelper:
    """macOS风格动画助手"""
    
    @staticmethod
    def add_transition(widget, property_name, duration=200):
        """添加属性过渡动画"""
        animation = QPropertyAnimation(widget, property_name.encode())
        animation.setDuration(duration)
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        return animation
    
    @staticmethod
    def window_resize_animation(window, target_size):
        """窗口大小调整动画"""
        anim = QPropertyAnimation(window, b"geometry")
        anim.setDuration(200)
        anim.setStartValue(window.geometry())
        anim.setEndValue(QRect(window.x(), window.y(), target_size[0], target_size[1]))
        anim.setEasingCurve(QEasingCurve.OutQuart)
        anim.start()
        return anim
    
    @staticmethod
    def fade_in_animation(widget, duration=300):
        """淡入动画"""
        effect = QGraphicsOpacityEffect()
        widget.setGraphicsEffect(effect)
        
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.OutQuart)
        animation.start()
        return animation
    
    @staticmethod
    def fade_out_animation(widget, duration=300):
        """淡出动画"""
        effect = QGraphicsOpacityEffect()
        widget.setGraphicsEffect(effect)
        
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)
        animation.setEasingCurve(QEasingCurve.OutQuart)
        animation.start()
        return animation
    
    @staticmethod
    def button_press_animation(button):
        """按钮按下动画"""
        anim = QPropertyAnimation(button, b"geometry")
        anim.setDuration(100)
        original_rect = button.geometry()
        pressed_rect = QRect(
            original_rect.x() + 1,
            original_rect.y() + 1,
            original_rect.width() - 2,
            original_rect.height() - 2
        )
        anim.setStartValue(original_rect)
        anim.setEndValue(pressed_rect)
        anim.setEasingCurve(QEasingCurve.OutQuart)
        anim.start()
        return anim