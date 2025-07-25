#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
界面测试工具 - 快速测试不同界面风格
"""

import sys
from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton, QVBoxLayout, QWidget, QLabel
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from app.ui.html_style_window import HTMLStyleWindow
from app.ui.main_window import MacOSMainWindow


class InterfaceSelector(QWidget):
    """界面选择器"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("选择界面风格")
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # 标题
        title = QLabel("🎨 多平台视频下载器")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # 说明
        desc = QLabel("请选择您喜欢的界面风格：")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("font-size: 14px; color: #666; margin-bottom: 20px;")
        layout.addWidget(desc)
        
        # HTML风格按钮（推荐）
        html_btn = QPushButton("🎯 HTML风格界面（推荐）")
        html_btn.setStyleSheet("""
            QPushButton {
                background-color: #0071e3;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0051cc;
            }
        """)
        html_btn.clicked.connect(self.open_html_style)
        layout.addWidget(html_btn)
        
        # 原生风格按钮
        native_btn = QPushButton("🍎 macOS原生风格界面")
        native_btn.setStyleSheet("""
            QPushButton {
                background-color: #f3f4f6;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #e5e7eb;
            }
        """)
        native_btn.clicked.connect(self.open_native_style)
        layout.addWidget(native_btn)
        
        # 说明文字
        info = QLabel("💡 HTML风格界面完全按照设计稿实现，推荐使用")
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("font-size: 12px; color: #888; margin-top: 20px;")
        layout.addWidget(info)
        
    def open_html_style(self):
        """打开HTML风格界面"""
        self.hide()
        self.html_window = HTMLStyleWindow()
        self.html_window.show()
        print("🎨 HTML风格界面已启动")
        
    def open_native_style(self):
        """打开原生风格界面"""
        self.hide()
        self.native_window = MacOSMainWindow()
        self.native_window.show()
        print("🍎 macOS原生风格界面已启动")


def main():
    app = QApplication(sys.argv)
    
    # 设置应用程序属性
    app.setApplicationName("界面测试工具")
    app.setApplicationVersion("1.0")
    
    # 设置字体
    font = QFont("-apple-system")
    if not font.exactMatch():
        font = QFont("Segoe UI")
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        style = sys.argv[1].lower()
        if style == 'html':
            window = HTMLStyleWindow()
            print("🎨 直接启动HTML风格界面")
        elif style == 'native':
            window = MacOSMainWindow()
            print("🍎 直接启动macOS原生风格界面")
        else:
            print("❌ 未知的界面风格，请使用 'html' 或 'native'")
            return 1
        window.show()
    else:
        # 显示选择器
        selector = InterfaceSelector()
        selector.show()
        print("🎯 界面选择器已启动")
        print("💡 提示: 可以使用 'python test_html_style.py html' 直接启动HTML风格")
        print("💡 提示: 可以使用 'python test_html_style.py native' 直接启动原生风格")
    
    # 运行应用
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())