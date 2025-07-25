"""
Web-based user interface using HTML/CSS/JS with PySide6 WebEngine
"""
import os
import json
from pathlib import Path
from typing import Dict, Any

from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
from PySide6.QtCore import QObject, Signal, Slot, QUrl, pyqtSlot
from PySide6.QtGui import QIcon

from app.core.portable import get_portable_manager
from app.services.download_service import DownloadService
from app.services.settings_service import SettingsService
from app.services.creator_service import CreatorService


class WebBridge(QObject):
    """Bridge between JavaScript and Python"""
    
    # Signals to JavaScript
    task_added = Signal(str, dict)  # url, task_data
    task_updated = Signal(str, dict)  # url, task_data
    task_completed = Signal(str, str)  # url, filepath
    task_failed = Signal(str, str)  # url, error
    creator_added = Signal(str, dict)  # creator_url, creator_info
    creator_updated = Signal(str, dict)  # creator_url, creator_info
    settings_updated = Signal(str, dict)  # section, settings
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.portable_manager = get_portable_manager()
        
        # Initialize services
        self.download_service = DownloadService()
        self.settings_service = SettingsService()
        self.creator_service = CreatorService()
        
        # Connect service signals
        self.connect_service_signals()
    
    def connect_service_signals(self):
        """Connect service signals to bridge signals"""
        # Download service
        self.download_service.task_added.connect(self.on_task_added)
        self.download_service.task_updated.connect(self.on_task_updated)
        self.download_service.task_completed.connect(self.on_task_completed)
        self.download_service.task_failed.connect(self.on_task_failed)
        
        # Creator service
        self.creator_service.creator_added.connect(self.on_creator_added)
        self.creator_service.creator_updated.connect(self.on_creator_updated)
        
        # Settings service
        self.settings_service.settings_changed.connect(self.on_settings_changed)
    
    def on_task_added(self, url: str):
        """Handle task added"""
        task = self.download_service.get_task(url)
        if task:
            task_data = {
                'url': url,
                'title': task.title or url,
                'filename': task.filename,
                'progress': task.progress,
                'status': task.status,
                'speed': task.speed,
                'eta': task.eta,
                'file_size': task.file_size,
                'downloaded_size': task.downloaded_size,
                'error': task.error,
            }
            self.task_added.emit(url, task_data)
    
    def on_task_updated(self, url: str, task_data: dict):
        """Handle task updated"""
        self.task_updated.emit(url, task_data)
    
    def on_task_completed(self, url: str, filepath: str):
        """Handle task completed"""
        self.task_completed.emit(url, filepath)
    
    def on_task_failed(self, url: str, error: str):
        """Handle task failed"""
        self.task_failed.emit(url, error)
    
    def on_creator_added(self, creator_url: str):
        """Handle creator added"""
        creator = self.creator_service.get_creator(creator_url)
        if creator:
            creator_info = {
                'url': creator.url,
                'name': creator.name,
                'platform': creator.platform,
                'video_count': creator.video_count,
                'auto_download': creator.auto_download,
                'enabled': creator.enabled,
            }
            self.creator_added.emit(creator_url, creator_info)
    
    def on_creator_updated(self, creator_url: str, creator_info: dict):
        """Handle creator updated"""
        self.creator_updated.emit(creator_url, creator_info)
    
    def on_settings_changed(self, section: str, settings):
        """Handle settings changed"""
        if hasattr(settings, '__dict__'):
            settings_dict = settings.__dict__
        else:
            settings_dict = dict(settings)
        self.settings_updated.emit(section, settings_dict)
    
    # JavaScript callable methods
    @Slot(str, result=bool)
    def addDownload(self, url: str) -> bool:
        """Add download task"""
        return self.download_service.add_download(url)
    
    @Slot(str, result=bool)
    def cancelDownload(self, url: str) -> bool:
        """Cancel download task"""
        return self.download_service.cancel_download(url)
    
    @Slot()
    def clearCompleted(self):
        """Clear completed downloads"""
        self.download_service.clear_completed()
    
    @Slot(str, bool, result=bool)
    def addCreator(self, url: str, auto_download: bool = False) -> bool:
        """Add creator for monitoring"""
        return self.creator_service.add_creator(url, auto_download)
    
    @Slot(str, result=bool)
    def removeCreator(self, url: str) -> bool:
        """Remove creator from monitoring"""
        return self.creator_service.remove_creator(url)
    
    @Slot(str, str, str)
    def updateDownloadSettings(self, key: str, value: str):
        """Update download settings"""
        # Convert string values to appropriate types
        if key == 'download_path':
            self.settings_service.update_download_settings(download_path=value)
        elif key == 'quality':
            self.settings_service.update_download_settings(quality=value)
        elif key == 'max_concurrent':
            self.settings_service.update_download_settings(max_concurrent=int(value))
        elif key == 'rate_limit':
            rate_limit = int(value) if value and value != '0' else None
            self.settings_service.update_download_settings(rate_limit=rate_limit)
    
    @Slot(str, str)
    def updateNetworkSettings(self, key: str, value: str):
        """Update network settings"""
        if key == 'proxy_enabled':
            self.settings_service.update_network_settings(proxy_enabled=value.lower() == 'true')
        elif key == 'proxy_type':
            self.settings_service.update_network_settings(proxy_type=value)
        elif key == 'proxy_host':
            self.settings_service.update_network_settings(proxy_host=value)
        elif key == 'proxy_port':
            self.settings_service.update_network_settings(proxy_port=int(value))
        elif key == 'proxy_username':
            self.settings_service.update_network_settings(proxy_username=value)
        elif key == 'proxy_password':
            self.settings_service.update_network_settings(proxy_password=value)
    
    @Slot(result=str)
    def getAppInfo(self) -> str:
        """Get application information"""
        info = {
            'version': '1.0.0',
            'portable_mode': self.portable_manager.is_portable,
            'data_dir': str(self.portable_manager.data_dir),
            'downloads_dir': str(self.portable_manager.get_downloads_directory()),
        }
        return json.dumps(info)
    
    @Slot(result=str)
    def getDownloadSettings(self) -> str:
        """Get download settings"""
        settings = self.settings_service.get_download_settings()
        return json.dumps({
            'download_path': settings.download_path,
            'quality': settings.quality,
            'max_concurrent': settings.max_concurrent,
            'rate_limit': settings.rate_limit,
        })
    
    @Slot(result=str)
    def getNetworkSettings(self) -> str:
        """Get network settings"""
        settings = self.settings_service.get_network_settings()
        return json.dumps({
            'proxy_enabled': settings.proxy_enabled,
            'proxy_type': settings.proxy_type,
            'proxy_host': settings.proxy_host,
            'proxy_port': settings.proxy_port,
            'proxy_username': settings.proxy_username,
            'proxy_password': settings.proxy_password,
        })
    
    @Slot(result=str)
    def getAllTasks(self) -> str:
        """Get all download tasks"""
        tasks = self.download_service.get_all_tasks()
        tasks_data = {}
        
        for url, task in tasks.items():
            tasks_data[url] = {
                'url': url,
                'title': task.title or url,
                'filename': task.filename,
                'progress': task.progress,
                'status': task.status,
                'speed': task.speed,
                'eta': task.eta,
                'file_size': task.file_size,
                'downloaded_size': task.downloaded_size,
                'error': task.error,
            }
        
        return json.dumps(tasks_data)
    
    @Slot(result=str)
    def getAllCreators(self) -> str:
        """Get all creators"""
        creators = self.creator_service.get_creators()
        creators_data = {}
        
        for url, creator in creators.items():
            creators_data[url] = {
                'url': creator.url,
                'name': creator.name,
                'platform': creator.platform,
                'video_count': creator.video_count,
                'auto_download': creator.auto_download,
                'enabled': creator.enabled,
                'last_check': creator.last_check.isoformat() if creator.last_check else None,
            }
        
        return json.dumps(creators_data)


class WebInterface(QMainWindow):
    """Main window with web-based interface"""
    
    def __init__(self):
        super().__init__()
        self.portable_manager = get_portable_manager()
        self.bridge = WebBridge(self)
        
        self.init_ui()
        self.load_web_interface()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Multi-platform Video Downloader v1.0.0")
        self.setGeometry(100, 100, 900, 600)
        
        # Set application icon
        icon_path = Path(__file__).parent.parent.parent / "assets" / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create web view
        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)
        
        # Setup web channel for JavaScript bridge
        from PySide6.QtWebChannel import QWebChannel
        self.channel = QWebChannel()
        self.channel.registerObject("bridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)
    
    def load_web_interface(self):
        """Load the HTML interface"""
        # Try enhanced HTML first
        enhanced_html = Path(__file__).parent / "enhanced_interface.html"
        original_html = Path(__file__).parent.parent.parent / "video_downloader (1).html"
        
        if enhanced_html.exists():
            # Load the enhanced HTML file
            self.web_view.load(QUrl.fromLocalFile(str(enhanced_html.absolute())))
            print(f"✅ Loaded enhanced HTML interface: {enhanced_html}")
        elif original_html.exists():
            # Load the original HTML file
            self.web_view.load(QUrl.fromLocalFile(str(original_html.absolute())))
            print(f"✅ Loaded original HTML interface: {original_html}")
        else:
            # Create a simple fallback HTML
            print("⚠️  HTML files not found, using fallback interface")
            self.create_fallback_html()
    
    def create_fallback_html(self):
        """Create a fallback HTML interface"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Video Downloader</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 20px; }
                .container { max-width: 800px; margin: 0 auto; }
                .input-group { margin: 20px 0; }
                input[type="text"] { width: 70%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
                button { padding: 10px 20px; background: #007AFF; color: white; border: none; border-radius: 5px; cursor: pointer; }
                button:hover { background: #0051D5; }
                .task-list { margin: 20px 0; }
                .task-item { padding: 10px; border: 1px solid #ddd; margin: 5px 0; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Multi-platform Video Downloader</h1>
                
                <div class="input-group">
                    <input type="text" id="urlInput" placeholder="输入视频链接">
                    <button onclick="addDownload()">开始下载</button>
                </div>
                
                <div class="task-list" id="taskList">
                    <h3>下载任务</h3>
                    <div id="tasks"></div>
                </div>
                
                <div>
                    <h3>应用信息</h3>
                    <div id="appInfo"></div>
                </div>
            </div>
            
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
            <script>
                let bridge;
                
                new QWebChannel(qt.webChannelTransport, function(channel) {
                    bridge = channel.objects.bridge;
                    
                    // Connect signals
                    bridge.task_added.connect(onTaskAdded);
                    bridge.task_updated.connect(onTaskUpdated);
                    bridge.task_completed.connect(onTaskCompleted);
                    bridge.task_failed.connect(onTaskFailed);
                    
                    // Load initial data
                    loadAppInfo();
                    loadTasks();
                });
                
                function addDownload() {
                    const url = document.getElementById('urlInput').value;
                    if (url && bridge) {
                        bridge.addDownload(url);
                        document.getElementById('urlInput').value = '';
                    }
                }
                
                function onTaskAdded(url, taskData) {
                    console.log('Task added:', url, taskData);
                    updateTaskDisplay();
                }
                
                function onTaskUpdated(url, taskData) {
                    console.log('Task updated:', url, taskData);
                    updateTaskDisplay();
                }
                
                function onTaskCompleted(url, filepath) {
                    console.log('Task completed:', url, filepath);
                    updateTaskDisplay();
                }
                
                function onTaskFailed(url, error) {
                    console.log('Task failed:', url, error);
                    updateTaskDisplay();
                }
                
                function loadAppInfo() {
                    if (bridge) {
                        bridge.getAppInfo(function(info) {
                            const data = JSON.parse(info);
                            document.getElementById('appInfo').innerHTML = 
                                '<p>版本: ' + data.version + '</p>' +
                                '<p>便携模式: ' + (data.portable_mode ? '是' : '否') + '</p>' +
                                '<p>数据目录: ' + data.data_dir + '</p>';
                        });
                    }
                }
                
                function loadTasks() {
                    if (bridge) {
                        bridge.getAllTasks(function(tasks) {
                            updateTaskDisplay();
                        });
                    }
                }
                
                function updateTaskDisplay() {
                    if (bridge) {
                        bridge.getAllTasks(function(tasksJson) {
                            const tasks = JSON.parse(tasksJson);
                            const tasksDiv = document.getElementById('tasks');
                            tasksDiv.innerHTML = '';
                            
                            for (const [url, task] of Object.entries(tasks)) {
                                const taskDiv = document.createElement('div');
                                taskDiv.className = 'task-item';
                                taskDiv.innerHTML = 
                                    '<strong>' + (task.title || task.url) + '</strong><br>' +
                                    '状态: ' + task.status + ' | 进度: ' + task.progress.toFixed(1) + '%<br>' +
                                    '速度: ' + task.speed + ' | ETA: ' + task.eta;
                                tasksDiv.appendChild(taskDiv);
                            }
                        });
                    }
                }
            </script>
        </body>
        </html>
        """
        
        self.web_view.setHtml(html_content)