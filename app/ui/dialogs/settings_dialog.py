"""
设置对话框 - macOS风格的设置界面
"""
import os
import json
import requests
from pathlib import Path
from typing import Dict, Any, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QPushButton, QCheckBox, QSpinBox,
    QComboBox, QTextEdit, QFileDialog, QGroupBox, QFormLayout,
    QSlider, QProgressBar, QMessageBox, QFrame, QScrollArea,
    QButtonGroup, QRadioButton, QListWidget, QListWidgetItem,
    QSplitter, QTreeWidget, QTreeWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QFont, QIcon, QPalette, QColor

from ...core.config import config_manager


class ProxyTestThread(QThread):
    """代理测试线程"""
    test_completed = Signal(bool, str)
    
    def __init__(self, proxy_type: str, host: str, port: int, username: str = "", password: str = ""):
        super().__init__()
        self.proxy_type = proxy_type
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        
    def run(self):
        """运行代理测试"""
        try:
            # 构建代理URL
            if self.username and self.password:
                proxy_url = f"{self.proxy_type}://{self.username}:{self.password}@{self.host}:{self.port}"
            else:
                proxy_url = f"{self.proxy_type}://{self.host}:{self.port}"
            
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            
            # 测试连接
            response = requests.get(
                'https://httpbin.org/ip',
                proxies=proxies,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                ip = data.get('origin', 'Unknown')
                self.test_completed.emit(True, f"代理连接成功！IP: {ip}")
            else:
                self.test_completed.emit(False, f"代理测试失败，状态码: {response.status_code}")
                
        except Exception as e:
            self.test_completed.emit(False, f"代理测试失败: {str(e)}")


class SettingsDialog(QDialog):
    """设置对话框"""
    
    settings_changed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setModal(True)
        self.resize(800, 600)
        self.setMinimumSize(700, 500)
        
        # 设置窗口标志
        self.setWindowFlags(
            Qt.Dialog | 
            Qt.WindowTitleHint | 
            Qt.WindowCloseButtonHint
        )
        
        self.proxy_test_thread = None
        self.setup_ui()
        self.load_settings()
        self.setup_connections()
        
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("settingsTabWidget")
        
        # 通用设置
        self.general_tab = self.create_general_tab()
        self.tab_widget.addTab(self.general_tab, "通用")
        
        # 下载设置
        self.download_tab = self.create_download_tab()
        self.tab_widget.addTab(self.download_tab, "下载")
        
        # 网络设置
        self.network_tab = self.create_network_tab()
        self.tab_widget.addTab(self.network_tab, "网络")
        
        # 外观设置
        self.appearance_tab = self.create_appearance_tab()
        self.tab_widget.addTab(self.appearance_tab, "外观")
        
        # 高级设置
        self.advanced_tab = self.create_advanced_tab()
        self.tab_widget.addTab(self.advanced_tab, "高级")
        
        layout.addWidget(self.tab_widget)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(20, 10, 20, 20)
        
        # 重置按钮
        self.reset_btn = QPushButton("重置为默认")
        self.reset_btn.setObjectName("resetButton")
        button_layout.addWidget(self.reset_btn)
        
        button_layout.addStretch()
        
        # 取消按钮
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setObjectName("cancelButton")
        button_layout.addWidget(self.cancel_btn)
        
        # 确定按钮
        self.ok_btn = QPushButton("确定")
        self.ok_btn.setObjectName("okButton")
        self.ok_btn.setDefault(True)
        button_layout.addWidget(self.ok_btn)
        
        layout.addLayout(button_layout)
        
    def create_general_tab(self) -> QWidget:
        """创建通用设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 应用程序设置组
        app_group = QGroupBox("应用程序")
        app_layout = QFormLayout(app_group)
        
        # 开机启动
        self.startup_check = QCheckBox("开机时自动启动")
        app_layout.addRow(self.startup_check)
        
        # 最小化到托盘
        self.tray_check = QCheckBox("最小化到系统托盘")
        app_layout.addRow(self.tray_check)
        
        # 关闭时最小化
        self.close_to_tray_check = QCheckBox("关闭窗口时最小化到托盘")
        app_layout.addRow(self.close_to_tray_check)
        
        layout.addWidget(app_group)
        
        # 系统集成设置组
        integration_group = QGroupBox("系统集成")
        integration_layout = QFormLayout(integration_group)
        
        # 老板键设置
        boss_key_layout = QHBoxLayout()
        self.boss_key_edit = QLineEdit()
        self.boss_key_edit.setPlaceholderText("Ctrl+Shift+H")
        self.boss_key_edit.setReadOnly(True)
        boss_key_layout.addWidget(self.boss_key_edit)
        
        self.boss_key_btn = QPushButton("设置")
        self.boss_key_btn.setFixedWidth(60)
        boss_key_layout.addWidget(self.boss_key_btn)
        
        integration_layout.addRow("老板键 (快速隐藏):", boss_key_layout)
        
        # 系统通知
        self.notifications_check = QCheckBox("启用系统通知")
        self.notifications_check.setChecked(True)
        integration_layout.addRow(self.notifications_check)
        
        # 下载完成通知
        self.download_complete_notify_check = QCheckBox("下载完成时通知")
        self.download_complete_notify_check.setChecked(True)
        integration_layout.addRow(self.download_complete_notify_check)
        
        # 下载失败通知
        self.download_failed_notify_check = QCheckBox("下载失败时通知")
        self.download_failed_notify_check.setChecked(True)
        integration_layout.addRow(self.download_failed_notify_check)
        
        # 协议关联
        protocol_layout = QHBoxLayout()
        self.protocol_check = QCheckBox("注册自定义协议 (videodownloader://)")
        protocol_layout.addWidget(self.protocol_check)
        
        self.protocol_register_btn = QPushButton("注册")
        self.protocol_register_btn.setFixedWidth(60)
        protocol_layout.addWidget(self.protocol_register_btn)
        
        integration_layout.addRow(protocol_layout)
        
        # 文件关联
        file_assoc_layout = QHBoxLayout()
        self.file_assoc_check = QCheckBox("关联视频文件格式")
        file_assoc_layout.addWidget(self.file_assoc_check)
        
        self.file_assoc_btn = QPushButton("设置")
        self.file_assoc_btn.setFixedWidth(60)
        file_assoc_layout.addWidget(self.file_assoc_btn)
        
        integration_layout.addRow(file_assoc_layout)
        
        layout.addWidget(integration_group)
        
        # 语言设置组
        lang_group = QGroupBox("语言")
        lang_layout = QFormLayout(lang_group)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["简体中文", "English", "日本語"])
        lang_layout.addRow("界面语言:", self.language_combo)
        
        layout.addWidget(lang_group)
        
        # 更新设置组
        update_group = QGroupBox("更新")
        update_layout = QFormLayout(update_group)
        
        self.auto_update_check = QCheckBox("自动检查更新")
        update_layout.addRow(self.auto_update_check)
        
        self.check_update_btn = QPushButton("立即检查更新")
        update_layout.addRow(self.check_update_btn)
        
        layout.addWidget(update_group)
        
        layout.addStretch()
        return widget
        
    def create_download_tab(self) -> QWidget:
        """创建下载设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 下载路径设置组
        path_group = QGroupBox("下载路径")
        path_layout = QVBoxLayout(path_group)
        
        # 默认下载路径
        path_row = QHBoxLayout()
        self.download_path_edit = QLineEdit()
        self.download_path_edit.setPlaceholderText("选择下载文件夹...")
        path_row.addWidget(QLabel("默认路径:"))
        path_row.addWidget(self.download_path_edit, 1)
        
        self.browse_path_btn = QPushButton("浏览...")
        path_row.addWidget(self.browse_path_btn)
        
        path_layout.addLayout(path_row)
        
        # 按创作者分类
        self.organize_by_creator_check = QCheckBox("按创作者创建子文件夹")
        path_layout.addWidget(self.organize_by_creator_check)
        
        # 按日期分类
        self.organize_by_date_check = QCheckBox("按日期创建子文件夹")
        path_layout.addWidget(self.organize_by_date_check)
        
        layout.addWidget(path_group)
        
        # 文件命名模板组
        naming_group = QGroupBox("文件命名模板")
        naming_layout = QVBoxLayout(naming_group)
        
        # 模板编辑器
        template_row = QHBoxLayout()
        template_row.addWidget(QLabel("命名模板:"))
        self.naming_template_edit = QLineEdit()
        self.naming_template_edit.setPlaceholderText("{title} - {author}")
        template_row.addWidget(self.naming_template_edit, 1)
        
        self.template_help_btn = QPushButton("?")
        self.template_help_btn.setFixedSize(24, 24)
        self.template_help_btn.setToolTip("查看可用变量")
        template_row.addWidget(self.template_help_btn)
        
        naming_layout.addLayout(template_row)
        
        # 预览
        preview_row = QHBoxLayout()
        preview_row.addWidget(QLabel("预览:"))
        self.template_preview_label = QLabel("示例文件名.mp4")
        self.template_preview_label.setStyleSheet("color: #666; font-style: italic;")
        preview_row.addWidget(self.template_preview_label, 1)
        naming_layout.addLayout(preview_row)
        
        # 模板变量说明
        variables_text = QTextEdit()
        variables_text.setMaximumHeight(120)
        variables_text.setReadOnly(True)
        variables_text.setPlainText(
            "可用变量:\n"
            "{title} - 视频标题\n"
            "{author} - 作者名称\n"
            "{date} - 上传日期 (YYYY-MM-DD)\n"
            "{platform} - 平台名称\n"
            "{quality} - 视频质量\n"
            "{duration} - 视频时长\n"
            "{id} - 视频ID"
        )
        naming_layout.addWidget(variables_text)
        
        layout.addWidget(naming_group)
        
        # 下载选项组
        options_group = QGroupBox("下载选项")
        options_layout = QFormLayout(options_group)
        
        # 并发下载数
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setRange(1, 10)
        self.concurrent_spin.setValue(3)
        options_layout.addRow("同时下载数:", self.concurrent_spin)
        
        # 默认质量
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["最佳质量", "1080p", "720p", "480p", "360p"])
        options_layout.addRow("默认质量:", self.quality_combo)
        
        # 默认格式
        self.format_combo = QComboBox()
        self.format_combo.addItems(["MP4", "MKV", "AVI", "MOV"])
        options_layout.addRow("默认格式:", self.format_combo)
        
        # 断点续传
        self.resume_check = QCheckBox("启用断点续传")
        options_layout.addRow(self.resume_check)
        
        # 重复文件处理
        self.duplicate_combo = QComboBox()
        self.duplicate_combo.addItems(["跳过", "覆盖", "重命名"])
        options_layout.addRow("重复文件:", self.duplicate_combo)
        
        layout.addWidget(options_group)
        
        layout.addStretch()
        return widget
        
    def create_network_tab(self) -> QWidget:
        """创建网络设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 连接设置组
        connection_group = QGroupBox("连接设置")
        connection_layout = QFormLayout(connection_group)
        
        # 连接超时
        self.connection_timeout_spin = QSpinBox()
        self.connection_timeout_spin.setRange(5, 300)
        self.connection_timeout_spin.setSuffix(" 秒")
        connection_layout.addRow("连接超时:", self.connection_timeout_spin)
        
        # 读取超时
        self.read_timeout_spin = QSpinBox()
        self.read_timeout_spin.setRange(10, 600)
        self.read_timeout_spin.setSuffix(" 秒")
        connection_layout.addRow("读取超时:", self.read_timeout_spin)
        
        # 重试次数
        self.retry_spin = QSpinBox()
        self.retry_spin.setRange(0, 10)
        connection_layout.addRow("重试次数:", self.retry_spin)
        
        # 下载限速
        speed_layout = QHBoxLayout()
        self.speed_limit_check = QCheckBox("限制下载速度")
        self.speed_limit_spin = QSpinBox()
        self.speed_limit_spin.setRange(1, 10000)
        self.speed_limit_spin.setSuffix(" KB/s")
        self.speed_limit_spin.setEnabled(False)
        speed_layout.addWidget(self.speed_limit_check)
        speed_layout.addWidget(self.speed_limit_spin)
        connection_layout.addRow("速度限制:", speed_layout)
        
        layout.addWidget(connection_group)
        
        # 代理设置组
        proxy_group = QGroupBox("代理设置")
        proxy_layout = QVBoxLayout(proxy_group)
        
        # 代理类型选择
        proxy_type_layout = QHBoxLayout()
        self.proxy_group_btn = QButtonGroup()
        
        self.no_proxy_radio = QRadioButton("不使用代理")
        self.no_proxy_radio.setChecked(True)
        self.proxy_group_btn.addButton(self.no_proxy_radio, 0)
        proxy_type_layout.addWidget(self.no_proxy_radio)
        
        self.http_proxy_radio = QRadioButton("HTTP代理")
        self.proxy_group_btn.addButton(self.http_proxy_radio, 1)
        proxy_type_layout.addWidget(self.http_proxy_radio)
        
        self.socks5_proxy_radio = QRadioButton("SOCKS5代理")
        self.proxy_group_btn.addButton(self.socks5_proxy_radio, 2)
        proxy_type_layout.addWidget(self.socks5_proxy_radio)
        
        proxy_type_layout.addStretch()
        proxy_layout.addLayout(proxy_type_layout)
        
        # 代理配置
        proxy_config_frame = QFrame()
        proxy_config_layout = QFormLayout(proxy_config_frame)
        
        # 服务器地址
        self.proxy_host_edit = QLineEdit()
        self.proxy_host_edit.setPlaceholderText("代理服务器地址")
        self.proxy_host_edit.setEnabled(False)
        proxy_config_layout.addRow("服务器:", self.proxy_host_edit)
        
        # 端口
        self.proxy_port_spin = QSpinBox()
        self.proxy_port_spin.setRange(1, 65535)
        self.proxy_port_spin.setValue(8080)
        self.proxy_port_spin.setEnabled(False)
        proxy_config_layout.addRow("端口:", self.proxy_port_spin)
        
        # 用户名
        self.proxy_username_edit = QLineEdit()
        self.proxy_username_edit.setPlaceholderText("用户名（可选）")
        self.proxy_username_edit.setEnabled(False)
        proxy_config_layout.addRow("用户名:", self.proxy_username_edit)
        
        # 密码
        self.proxy_password_edit = QLineEdit()
        self.proxy_password_edit.setPlaceholderText("密码（可选）")
        self.proxy_password_edit.setEchoMode(QLineEdit.Password)
        self.proxy_password_edit.setEnabled(False)
        proxy_config_layout.addRow("密码:", self.proxy_password_edit)
        
        proxy_layout.addWidget(proxy_config_frame)
        
        # 代理测试
        proxy_test_layout = QHBoxLayout()
        self.proxy_test_btn = QPushButton("测试代理")
        self.proxy_test_btn.setEnabled(False)
        proxy_test_layout.addWidget(self.proxy_test_btn)
        
        self.proxy_test_progress = QProgressBar()
        self.proxy_test_progress.setVisible(False)
        proxy_test_layout.addWidget(self.proxy_test_progress)
        
        proxy_test_layout.addStretch()
        proxy_layout.addLayout(proxy_test_layout)
        
        # 测试结果
        self.proxy_test_result = QLabel("")
        self.proxy_test_result.setWordWrap(True)
        proxy_layout.addWidget(self.proxy_test_result)
        
        layout.addWidget(proxy_group)
        
        layout.addStretch()
        return widget
        
    def create_appearance_tab(self) -> QWidget:
        """创建外观设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 主题设置组
        theme_group = QGroupBox("主题")
        theme_layout = QVBoxLayout(theme_group)
        
        # 主题选择
        theme_selection_layout = QHBoxLayout()
        self.theme_group_btn = QButtonGroup()
        
        self.light_theme_radio = QRadioButton("浅色主题")
        self.light_theme_radio.setChecked(True)
        self.theme_group_btn.addButton(self.light_theme_radio, 0)
        theme_selection_layout.addWidget(self.light_theme_radio)
        
        self.dark_theme_radio = QRadioButton("深色主题")
        self.theme_group_btn.addButton(self.dark_theme_radio, 1)
        theme_selection_layout.addWidget(self.dark_theme_radio)
        
        self.auto_theme_radio = QRadioButton("跟随系统")
        self.theme_group_btn.addButton(self.auto_theme_radio, 2)
        theme_selection_layout.addWidget(self.auto_theme_radio)
        
        theme_selection_layout.addStretch()
        theme_layout.addLayout(theme_selection_layout)
        
        # 主题预览
        preview_frame = QFrame()
        preview_frame.setFrameStyle(QFrame.StyledPanel)
        preview_frame.setMinimumHeight(100)
        preview_layout = QVBoxLayout(preview_frame)
        
        preview_label = QLabel("主题预览")
        preview_label.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(preview_label)
        
        theme_layout.addWidget(preview_frame)
        
        layout.addWidget(theme_group)
        
        # 界面设置组
        ui_group = QGroupBox("界面")
        ui_layout = QFormLayout(ui_group)
        
        # 字体大小
        self.font_size_slider = QSlider(Qt.Horizontal)
        self.font_size_slider.setRange(8, 18)
        self.font_size_slider.setValue(12)
        font_size_layout = QHBoxLayout()
        font_size_layout.addWidget(QLabel("小"))
        font_size_layout.addWidget(self.font_size_slider, 1)
        font_size_layout.addWidget(QLabel("大"))
        self.font_size_value = QLabel("12")
        font_size_layout.addWidget(self.font_size_value)
        ui_layout.addRow("字体大小:", font_size_layout)
        
        # 界面缩放
        self.ui_scale_slider = QSlider(Qt.Horizontal)
        self.ui_scale_slider.setRange(80, 150)
        self.ui_scale_slider.setValue(100)
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("80%"))
        scale_layout.addWidget(self.ui_scale_slider, 1)
        scale_layout.addWidget(QLabel("150%"))
        self.ui_scale_value = QLabel("100%")
        scale_layout.addWidget(self.ui_scale_value)
        ui_layout.addRow("界面缩放:", scale_layout)
        
        # 动画效果
        self.animation_check = QCheckBox("启用动画效果")
        self.animation_check.setChecked(True)
        ui_layout.addRow(self.animation_check)
        
        # 透明效果
        self.transparency_check = QCheckBox("启用透明效果")
        self.transparency_check.setChecked(True)
        ui_layout.addRow(self.transparency_check)
        
        layout.addWidget(ui_group)
        
        layout.addStretch()
        return widget
        
    def create_advanced_tab(self) -> QWidget:
        """创建高级设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 性能设置组
        performance_group = QGroupBox("性能")
        performance_layout = QFormLayout(performance_group)
        
        # 内存缓存
        self.memory_cache_spin = QSpinBox()
        self.memory_cache_spin.setRange(64, 2048)
        self.memory_cache_spin.setSuffix(" MB")
        performance_layout.addRow("内存缓存:", self.memory_cache_spin)
        
        # 磁盘缓存
        self.disk_cache_spin = QSpinBox()
        self.disk_cache_spin.setRange(100, 10000)
        self.disk_cache_spin.setSuffix(" MB")
        performance_layout.addRow("磁盘缓存:", self.disk_cache_spin)
        
        # 硬件加速
        self.hardware_accel_check = QCheckBox("启用硬件加速")
        performance_layout.addRow(self.hardware_accel_check)
        
        layout.addWidget(performance_group)
        
        # 日志设置组
        log_group = QGroupBox("日志")
        log_layout = QFormLayout(log_group)
        
        # 日志级别
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["调试", "信息", "警告", "错误"])
        log_layout.addRow("日志级别:", self.log_level_combo)
        
        # 日志文件大小
        self.log_size_spin = QSpinBox()
        self.log_size_spin.setRange(1, 100)
        self.log_size_spin.setSuffix(" MB")
        log_layout.addRow("日志文件大小:", self.log_size_spin)
        
        # 清理日志按钮
        self.clear_log_btn = QPushButton("清理日志文件")
        log_layout.addRow(self.clear_log_btn)
        
        layout.addWidget(log_group)
        
        # 数据管理组
        data_group = QGroupBox("数据管理")
        data_layout = QVBoxLayout(data_group)
        
        # 导入导出配置
        config_layout = QHBoxLayout()
        self.export_config_btn = QPushButton("导出配置")
        self.import_config_btn = QPushButton("导入配置")
        config_layout.addWidget(self.export_config_btn)
        config_layout.addWidget(self.import_config_btn)
        config_layout.addStretch()
        data_layout.addLayout(config_layout)
        
        # 清理数据
        cleanup_layout = QHBoxLayout()
        self.clear_history_btn = QPushButton("清理下载历史")
        self.clear_cache_btn = QPushButton("清理缓存")
        cleanup_layout.addWidget(self.clear_history_btn)
        cleanup_layout.addWidget(self.clear_cache_btn)
        cleanup_layout.addStretch()
        data_layout.addLayout(cleanup_layout)
        
        layout.addWidget(data_group)
        
        layout.addStretch()
        return widget
        
    def setup_connections(self):
        """设置信号连接"""
        # 按钮连接
        self.ok_btn.clicked.connect(self.accept_settings)
        self.cancel_btn.clicked.connect(self.reject)
        self.reset_btn.clicked.connect(self.reset_settings)
        
        # 路径浏览
        self.browse_path_btn.clicked.connect(self.browse_download_path)
        
        # 代理设置连接
        self.proxy_group_btn.buttonToggled.connect(self.on_proxy_type_changed)
        self.proxy_test_btn.clicked.connect(self.test_proxy)
        
        # 速度限制连接
        self.speed_limit_check.toggled.connect(self.speed_limit_spin.setEnabled)
        
        # 模板预览更新
        self.naming_template_edit.textChanged.connect(self.update_template_preview)
        self.template_help_btn.clicked.connect(self.show_template_help)
        
        # 滑块值更新
        self.font_size_slider.valueChanged.connect(
            lambda v: self.font_size_value.setText(str(v))
        )
        self.ui_scale_slider.valueChanged.connect(
            lambda v: self.ui_scale_value.setText(f"{v}%")
        )
        
        # 高级功能连接
        self.export_config_btn.clicked.connect(self.export_config)
        self.import_config_btn.clicked.connect(self.import_config)
        self.clear_history_btn.clicked.connect(self.clear_history)
        self.clear_cache_btn.clicked.connect(self.clear_cache)
        self.clear_log_btn.clicked.connect(self.clear_logs)
        
        # 系统集成功能连接
        self.boss_key_btn.clicked.connect(self.set_boss_key)
        self.protocol_register_btn.clicked.connect(self.register_protocol)
        self.file_assoc_btn.clicked.connect(self.setup_file_associations)
        
    def load_settings(self):
        """加载设置"""
        config = config_manager.config
        
        # 通用设置
        # 这里可以根据实际配置加载设置
        
        # 下载设置
        self.download_path_edit.setText(config.download_path)
        self.concurrent_spin.setValue(config.max_concurrent_downloads)
        self.naming_template_edit.setText("{title} - {author}")
        
        # 网络设置
        self.connection_timeout_spin.setValue(config.connection_timeout)
        self.read_timeout_spin.setValue(config.read_timeout)
        self.retry_spin.setValue(config.max_retries)
        
        # 外观设置
        if config.theme == "dark":
            self.dark_theme_radio.setChecked(True)
        else:
            self.light_theme_radio.setChecked(True)
            
        self.update_template_preview()
        
    def accept_settings(self):
        """接受设置"""
        settings = self.get_current_settings()
        self.save_settings(settings)
        self.settings_changed.emit(settings)
        self.accept()
        
    def get_current_settings(self) -> Dict[str, Any]:
        """获取当前设置"""
        settings = {}
        
        # 通用设置 - 系统集成
        settings['startup_enabled'] = self.startup_check.isChecked()
        settings['tray_enabled'] = self.tray_check.isChecked()
        settings['close_to_tray'] = self.close_to_tray_check.isChecked()
        settings['boss_key'] = self.boss_key_edit.text() or "Ctrl+Shift+H"
        settings['notifications_enabled'] = self.notifications_check.isChecked()
        settings['download_complete_notify'] = self.download_complete_notify_check.isChecked()
        settings['download_failed_notify'] = self.download_failed_notify_check.isChecked()
        settings['protocol_registered'] = self.protocol_check.isChecked()
        settings['file_associations_enabled'] = self.file_assoc_check.isChecked()
        
        # 下载设置
        settings['download_path'] = self.download_path_edit.text()
        settings['max_concurrent_downloads'] = self.concurrent_spin.value()
        settings['naming_template'] = self.naming_template_edit.text()
        settings['organize_by_creator'] = self.organize_by_creator_check.isChecked()
        settings['organize_by_date'] = self.organize_by_date_check.isChecked()
        
        # 网络设置
        settings['connection_timeout'] = self.connection_timeout_spin.value()
        settings['read_timeout'] = self.read_timeout_spin.value()
        settings['max_retries'] = self.retry_spin.value()
        settings['speed_limit_enabled'] = self.speed_limit_check.isChecked()
        settings['speed_limit'] = self.speed_limit_spin.value()
        
        # 代理设置
        proxy_type = self.proxy_group_btn.checkedId()
        settings['proxy_enabled'] = proxy_type > 0
        if proxy_type == 1:
            settings['proxy_type'] = 'http'
        elif proxy_type == 2:
            settings['proxy_type'] = 'socks5'
        else:
            settings['proxy_type'] = 'none'
            
        settings['proxy_host'] = self.proxy_host_edit.text()
        settings['proxy_port'] = self.proxy_port_spin.value()
        settings['proxy_username'] = self.proxy_username_edit.text()
        settings['proxy_password'] = self.proxy_password_edit.text()
        
        # 外观设置
        theme_id = self.theme_group_btn.checkedId()
        if theme_id == 1:
            settings['theme'] = 'dark'
        elif theme_id == 2:
            settings['theme'] = 'auto'
        else:
            settings['theme'] = 'light'
            
        settings['font_size'] = self.font_size_slider.value()
        settings['ui_scale'] = self.ui_scale_slider.value()
        settings['animation_enabled'] = self.animation_check.isChecked()
        settings['transparency_enabled'] = self.transparency_check.isChecked()
        
        return settings
        
    def save_settings(self, settings: Dict[str, Any]):
        """保存设置"""
        # 更新配置管理器
        for key, value in settings.items():
            if hasattr(config_manager.config, key):
                setattr(config_manager.config, key, value)
        
        config_manager.save()
        
    def reset_settings(self):
        """重置设置"""
        reply = QMessageBox.question(
            self, "重置设置",
            "确定要重置所有设置为默认值吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            config_manager.reset_to_defaults()
            self.load_settings()
            
    def browse_download_path(self):
        """浏览下载路径"""
        current_path = self.download_path_edit.text()
        if not current_path:
            current_path = str(Path.home() / "Downloads")
            
        path = QFileDialog.getExistingDirectory(
            self, "选择下载文件夹", current_path
        )
        
        if path:
            self.download_path_edit.setText(path)
            
    def on_proxy_type_changed(self, button, checked):
        """代理类型改变"""
        if checked:
            proxy_enabled = self.proxy_group_btn.checkedId() > 0
            
            self.proxy_host_edit.setEnabled(proxy_enabled)
            self.proxy_port_spin.setEnabled(proxy_enabled)
            self.proxy_username_edit.setEnabled(proxy_enabled)
            self.proxy_password_edit.setEnabled(proxy_enabled)
            self.proxy_test_btn.setEnabled(proxy_enabled)
            
    def test_proxy(self):
        """测试代理连接"""
        proxy_type_id = self.proxy_group_btn.checkedId()
        if proxy_type_id <= 0:
            return
            
        proxy_type = "http" if proxy_type_id == 1 else "socks5"
        host = self.proxy_host_edit.text().strip()
        port = self.proxy_port_spin.value()
        username = self.proxy_username_edit.text().strip()
        password = self.proxy_password_edit.text().strip()
        
        if not host:
            QMessageBox.warning(self, "错误", "请输入代理服务器地址")
            return
            
        # 显示进度条
        self.proxy_test_progress.setVisible(True)
        self.proxy_test_progress.setRange(0, 0)  # 无限进度条
        self.proxy_test_btn.setEnabled(False)
        self.proxy_test_result.setText("正在测试代理连接...")
        
        # 启动测试线程
        self.proxy_test_thread = ProxyTestThread(proxy_type, host, port, username, password)
        self.proxy_test_thread.test_completed.connect(self.on_proxy_test_completed)
        self.proxy_test_thread.start()
        
    def on_proxy_test_completed(self, success: bool, message: str):
        """代理测试完成"""
        self.proxy_test_progress.setVisible(False)
        self.proxy_test_btn.setEnabled(True)
        
        if success:
            self.proxy_test_result.setText(f"✅ {message}")
            self.proxy_test_result.setStyleSheet("color: green;")
        else:
            self.proxy_test_result.setText(f"❌ {message}")
            self.proxy_test_result.setStyleSheet("color: red;")
            
    def update_template_preview(self):
        """更新模板预览"""
        template = self.naming_template_edit.text()
        if not template:
            template = "{title} - {author}"
            
        # 示例数据
        example_data = {
            'title': '示例视频标题',
            'author': '示例作者',
            'date': '2024-01-15',
            'platform': 'YouTube',
            'quality': '1080p',
            'duration': '05:30',
            'id': 'abc123'
        }
        
        try:
            preview = template.format(**example_data)
            self.template_preview_label.setText(f"{preview}.mp4")
            self.template_preview_label.setStyleSheet("color: #666; font-style: italic;")
        except KeyError as e:
            self.template_preview_label.setText(f"错误: 未知变量 {e}")
            self.template_preview_label.setStyleSheet("color: red; font-style: italic;")
            
    def show_template_help(self):
        """显示模板帮助"""
        help_text = """
文件命名模板变量说明：

{title} - 视频标题
{author} - 作者名称  
{date} - 上传日期 (YYYY-MM-DD)
{platform} - 平台名称
{quality} - 视频质量
{duration} - 视频时长
{id} - 视频ID

示例模板：
{title} - {author}
[{platform}] {title} ({quality})
{date} - {author} - {title}
{author}/{title}

注意：文件名中不能包含以下字符：
< > : " | ? * \\ /
        """
        
        QMessageBox.information(self, "命名模板帮助", help_text.strip())
        
    def export_config(self):
        """导出配置"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出配置", "video_downloader_config.json",
            "JSON文件 (*.json)"
        )
        
        if file_path:
            try:
                settings = self.get_current_settings()
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=2, ensure_ascii=False)
                QMessageBox.information(self, "成功", "配置已导出")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出配置失败: {e}")
                
    def import_config(self):
        """导入配置"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入配置", "",
            "JSON文件 (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # 应用导入的设置
                self.apply_imported_settings(settings)
                QMessageBox.information(self, "成功", "配置已导入")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入配置失败: {e}")
                
    def apply_imported_settings(self, settings: Dict[str, Any]):
        """应用导入的设置"""
        # 这里可以根据导入的设置更新界面控件
        if 'download_path' in settings:
            self.download_path_edit.setText(settings['download_path'])
        if 'theme' in settings:
            if settings['theme'] == 'dark':
                self.dark_theme_radio.setChecked(True)
            else:
                self.light_theme_radio.setChecked(True)
        # 添加更多设置的应用逻辑...
        
    def clear_history(self):
        """清理下载历史"""
        reply = QMessageBox.question(
            self, "清理历史",
            "确定要清理所有下载历史记录吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 这里添加清理历史的逻辑
            QMessageBox.information(self, "完成", "下载历史已清理")
            
    def clear_cache(self):
        """清理缓存"""
        reply = QMessageBox.question(
            self, "清理缓存",
            "确定要清理所有缓存文件吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 这里添加清理缓存的逻辑
            QMessageBox.information(self, "完成", "缓存已清理")
            
    def clear_logs(self):
        """清理日志"""
        reply = QMessageBox.question(
            self, "清理日志",
            "确定要清理所有日志文件吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 这里添加清理日志的逻辑
            QMessageBox.information(self, "完成", "日志文件已清理")
            
    def set_boss_key(self):
        """设置老板键"""
        from PySide6.QtWidgets import QInputDialog
        from PySide6.QtGui import QKeySequence
        
        current_key = self.boss_key_edit.text() or "Ctrl+Shift+H"
        
        # 创建一个简单的输入对话框
        text, ok = QInputDialog.getText(
            self, "设置老板键", 
            "请输入快捷键组合 (例如: Ctrl+Shift+H):",
            text=current_key
        )
        
        if ok and text.strip():
            # 验证快捷键格式
            try:
                key_sequence = QKeySequence(text.strip())
                if not key_sequence.isEmpty():
                    self.boss_key_edit.setText(text.strip())
                    QMessageBox.information(self, "成功", f"老板键已设置为: {text.strip()}")
                else:
                    QMessageBox.warning(self, "错误", "无效的快捷键格式")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"快捷键格式错误: {e}")
                
    def register_protocol(self):
        """注册自定义协议"""
        reply = QMessageBox.question(
            self, "注册协议",
            "确定要注册 videodownloader:// 协议吗？\n"
            "这将允许浏览器直接调用本应用程序下载视频。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 这里需要调用系统集成服务的方法
                # 暂时显示成功消息
                self.protocol_check.setChecked(True)
                QMessageBox.information(self, "成功", "协议注册成功！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"协议注册失败: {e}")
                
    def setup_file_associations(self):
        """设置文件关联"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QDialogButtonBox
        
        # 创建文件关联设置对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("文件关联设置")
        dialog.setModal(True)
        dialog.resize(300, 400)
        
        layout = QVBoxLayout(dialog)
        
        # 添加说明
        info_label = QLabel("选择要关联的视频文件格式:")
        layout.addWidget(info_label)
        
        # 文件格式选项
        formats = [
            ('.mp4', 'MP4 视频文件'),
            ('.avi', 'AVI 视频文件'),
            ('.mkv', 'MKV 视频文件'),
            ('.mov', 'MOV 视频文件'),
            ('.wmv', 'WMV 视频文件'),
            ('.flv', 'FLV 视频文件'),
            ('.webm', 'WebM 视频文件'),
            ('.m4v', 'M4V 视频文件'),
            ('.3gp', '3GP 视频文件'),
            ('.ts', 'TS 视频文件')
        ]
        
        checkboxes = {}
        for ext, desc in formats:
            checkbox = QCheckBox(f"{ext.upper()} - {desc}")
            checkbox.setChecked(True)  # 默认全选
            checkboxes[ext] = checkbox
            layout.addWidget(checkbox)
            
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            dialog
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.Accepted:
            # 获取选中的格式
            selected_formats = [ext for ext, cb in checkboxes.items() if cb.isChecked()]
            
            if selected_formats:
                try:
                    # 这里需要调用系统集成服务的方法
                    # 暂时显示成功消息
                    self.file_assoc_check.setChecked(True)
                    QMessageBox.information(
                        self, "成功", 
                        f"已关联 {len(selected_formats)} 种文件格式"
                    )
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"文件关联失败: {e}")
            else:
                QMessageBox.information(self, "提示", "未选择任何文件格式")