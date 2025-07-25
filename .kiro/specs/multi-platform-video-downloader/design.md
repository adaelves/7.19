# 设计文档

## 概述

多平台视频下载软件采用模块化架构设计，基于Python + PySide6技术栈，实现专业级的视频下载功能。软件采用插件化设计，支持动态扩展新平台，同时提供完美复刻macOS风格的现代化用户界面。

## 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    用户界面层 (UI Layer)                      │
├─────────────────────────────────────────────────────────────┤
│                   业务逻辑层 (Business Layer)                 │
├─────────────────────────────────────────────────────────────┤
│                   数据访问层 (Data Access Layer)             │
├─────────────────────────────────────────────────────────────┤
│                   核心服务层 (Core Services)                 │
└─────────────────────────────────────────────────────────────┘
```

### 核心模块架构

```
app/
├── core/                    # 核心模块
│   ├── downloader/         # 下载器核心
│   ├── extractor/          # 提取器系统
│   ├── plugin/             # 插件管理
│   └── utils/              # 工具类
├── ui/                     # 用户界面
│   ├── components/         # UI组件
│   ├── dialogs/           # 对话框
│   ├── styles/            # QSS样式
│   └── main_window.py     # 主窗口
├── data/                   # 数据层
│   ├── models/            # 数据模型
│   ├── database/          # 数据库操作
│   └── storage/           # 存储管理
├── services/              # 服务层
│   ├── download_service.py
│   ├── monitor_service.py
│   └── config_service.py
└── plugins/               # 插件目录
    ├── youtube.py         # YouTube下载器
    ├── bilibili.py        # B站下载器
    ├── tiktok.py          # TikTok下载器
    ├── instagram.py       # Instagram下载器
    ├── pornhub.py         # Pornhub下载器
    ├── youporn.py         # YouPorn下载器
    ├── xvideo.py          # XVideo下载器
    ├── xhamster.py        # XHamster下载器
    ├── weibo.py           # 微博下载器
    ├── tumblr.py          # Tumblr下载器
    ├── pixiv.py           # Pixiv下载器
    ├── kissjav.py         # KissJAV下载器
    ├── fc2.py             # FC2视频下载器
    ├── flickr.py          # Flickr下载器
    ├── twitch.py          # Twitch下载器
    ├── twitter.py         # Twitter下载器
    └── base.py            # 插件基类
```

## 核心组件设计

### 1. 下载器架构

#### BaseDownloader抽象基类
```python
class BaseDownloader(ABC):
    @abstractmethod
    def download(self, url: str, options: DownloadOptions) -> DownloadResult
    
    @abstractmethod
    def get_metadata(self, url: str) -> VideoMetadata
    
    @abstractmethod
    def pause(self) -> None
    
    @abstractmethod
    def resume(self) -> None
    
    @abstractmethod
    def cancel(self) -> None
```

#### 下载管理器
- **DownloadManager**: 统一管理所有下载任务
- **TaskQueue**: 任务队列管理，支持优先级
- **ThreadPool**: 可配置的线程池
- **ProgressTracker**: 进度跟踪和统计

### 2. 插件系统设计

#### BaseExtractor抽象基类
```python
class BaseExtractor(ABC):
    @property
    @abstractmethod
    def supported_domains(self) -> List[str]
    
    @abstractmethod
    def can_handle(self, url: str) -> bool
    
    @abstractmethod
    def extract_info(self, url: str) -> Dict[str, Any]
    
    @abstractmethod
    def get_download_urls(self, info: Dict) -> List[str]
```

#### 插件管理器
- **PluginLoader**: 动态加载插件
- **PluginRegistry**: 插件注册表
- **SecurityManager**: 插件安全隔离
- **URLRouter**: URL路由到对应插件

#### 新增网站插件设计

##### 成人内容平台插件
```python
# YouPorn插件
class YouPornExtractor(BaseExtractor):
    supported_domains = ["youporn.com"]
    
    def extract_info(self, url: str) -> Dict[str, Any]:
        # 处理年龄验证
        # 提取视频元数据
        # 获取多画质下载链接
        
# XVideo插件  
class XVideoExtractor(BaseExtractor):
    supported_domains = ["xvideos.com"]
    
    def extract_info(self, url: str) -> Dict[str, Any]:
        # 解析视频页面
        # 提取M3U8流媒体链接
        # 处理地域限制

# XHamster插件
class XHamsterExtractor(BaseExtractor):
    supported_domains = ["xhamster.com"]
    
    def extract_info(self, url: str) -> Dict[str, Any]:
        # 处理动态加载内容
        # 提取高清视频源
        # 支持VR内容下载

# KissJAV插件
class KissJAVExtractor(BaseExtractor):
    supported_domains = ["kissjav.com"]
    
    def extract_info(self, url: str) -> Dict[str, Any]:
        # 处理防爬虫机制
        # 提取视频流链接
        # 支持字幕下载
```

##### 社交媒体平台插件
```python
# 微博插件
class WeiboExtractor(BaseExtractor):
    supported_domains = ["weibo.com", "weibo.cn"]
    
    def extract_info(self, url: str) -> Dict[str, Any]:
        # 处理登录验证
        # 提取微博视频和图片
        # 支持长微博图片拼接

# Tumblr插件
class TumblrExtractor(BaseExtractor):
    supported_domains = ["tumblr.com"]
    
    def extract_info(self, url: str) -> Dict[str, Any]:
        # 处理NSFW内容
        # 提取GIF和视频
        # 支持博客批量下载

# Pixiv插件
class PixivExtractor(BaseExtractor):
    supported_domains = ["pixiv.net"]
    
    def extract_info(self, url: str) -> Dict[str, Any]:
        # 处理登录认证
        # 提取高分辨率插画
        # 支持动图(ugoira)下载
        # 处理多图作品
```

##### 流媒体和图片平台插件
```python
# FC2视频插件
class FC2Extractor(BaseExtractor):
    supported_domains = ["video.fc2.com"]
    
    def extract_info(self, url: str) -> Dict[str, Any]:
        # 处理FC2会员验证
        # 提取视频流链接
        # 支持高清画质选择
        # 处理地域限制

# Flickr插件
class FlickrExtractor(BaseExtractor):
    supported_domains = ["flickr.com", "flic.kr"]
    
    def extract_info(self, url: str) -> Dict[str, Any]:
        # 提取高分辨率图片
        # 支持相册批量下载
        # 处理私有相册权限
        # 提取EXIF信息

# Twitch插件
class TwitchExtractor(BaseExtractor):
    supported_domains = ["twitch.tv", "clips.twitch.tv"]
    
    def extract_info(self, url: str) -> Dict[str, Any]:
        # 提取直播录像和片段
        # 支持多画质选择
        # 处理订阅者专属内容
        # 提取聊天记录

# Twitter插件 (重点功能)
class TwitterExtractor(BaseExtractor):
    supported_domains = ["twitter.com", "x.com", "t.co"]
    
    def extract_info(self, url: str) -> Dict[str, Any]:
        # 提取推文中的视频、图片、GIF
        # 支持4K高清图片下载
        # 处理敏感内容警告
        # 支持Cookie认证访问私有内容
    
    def extract_user_media(self, username: str) -> List[Dict[str, Any]]:
        # 批量获取用户所有媒体内容
        # 支持时间范围筛选
        # 智能去重和分类
        # 支持增量更新检测
    
    def get_user_timeline(self, username: str, include_replies: bool = False) -> List[Dict]:
        # 获取用户时间线
        # 过滤纯文本推文
        # 只保留包含媒体的推文
        # 支持翻页获取历史内容
```

#### 插件扩展机制
```python
class PluginManager:
    def __init__(self):
        self.extractors = {}
        self.load_builtin_plugins()
        self.load_external_plugins()
    
    def register_extractor(self, extractor_class):
        """注册新的提取器插件"""
        extractor = extractor_class()
        for domain in extractor.supported_domains:
            self.extractors[domain] = extractor
    
    def get_extractor(self, url: str) -> BaseExtractor:
        """根据URL获取对应的提取器"""
        domain = self.extract_domain(url)
        return self.extractors.get(domain)
    
    def load_external_plugins(self):
        """动态加载外部插件"""
        plugin_dir = Path("plugins")
        for plugin_file in plugin_dir.glob("*.py"):
            self.load_plugin_file(plugin_file)
```

### 3. 数据模型设计

#### 核心数据模型
```python
@dataclass
class VideoMetadata:
    title: str
    author: str
    thumbnail_url: str
    duration: int
    view_count: int
    upload_date: datetime
    quality_options: List[QualityOption]
    
@dataclass
class DownloadTask:
    id: str
    url: str
    metadata: VideoMetadata
    status: TaskStatus
    progress: float
    download_path: str
    created_at: datetime
    
@dataclass
class CreatorProfile:
    id: str
    name: str
    platform: str
    channel_url: str
    avatar_url: str
    last_check: datetime
    auto_download: bool
    priority: int
```

#### 数据库设计
```sql
-- 下载历史表
CREATE TABLE download_history (
    id INTEGER PRIMARY KEY,
    url TEXT NOT NULL,
    title TEXT,
    author TEXT,
    file_path TEXT,
    file_size INTEGER,
    md5_hash TEXT,
    download_date DATETIME,
    platform TEXT
);

-- 创作者监控表
CREATE TABLE creators (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    platform TEXT NOT NULL,
    channel_url TEXT UNIQUE,
    avatar_url TEXT,
    last_video_count INTEGER,
    last_check DATETIME,
    auto_download BOOLEAN,
    priority INTEGER
);

-- 配置表
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at DATETIME
);
```

## 用户界面设计

### 1. 主界面布局

#### 窗口结构
```
┌─────────────────────────────────────────────────────────────┐
│  [●][○][○]           App Title              [🌙][⚙️][📁]    │
├─────────────────────────────────────────────────────────────┤
│  URL输入框                                    [添加] [粘贴]   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                 下载列表区域                            │ │
│  │  ┌─[缩略图]─[标题]─────────[进度条]─[状态]─[操作]─┐    │ │
│  │  │                                                │    │ │
│  │  └────────────────────────────────────────────────┘    │ │
│  └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  状态栏: [总进度] [下载速度] [剩余时间] [活跃任务数]         │
└─────────────────────────────────────────────────────────────┘
```

#### macOS风格特性
- **窗口装饰**: 使用macOS标准的红绿黄按钮
- **毛玻璃效果**: 背景模糊和透明度
- **圆角设计**: 所有UI元素使用圆角
- **阴影效果**: 卡片式布局带阴影
- **动画过渡**: 流畅的状态切换动画

### 2. 组件设计

#### 下载任务卡片
```python
class DownloadTaskCard(QWidget):
    def __init__(self, task: DownloadTask):
        # 缩略图 (80x60)
        # 标题和作者信息
        # 魔法进度条 (带波形图)
        # 状态指示器 (彩色圆点)
        # 操作按钮组
```

#### 魔法进度条
- **波形图显示**: 实时带宽使用情况
- **渐变色彩**: 根据速度变化颜色
- **动画效果**: 平滑的进度更新
- **多段显示**: 支持分段下载进度

#### 3D Touch右键菜单
```python
class ContextMenu(QMenu):
    def __init__(self):
        # 任务控制组
        self.add_action_group("任务控制", [
            ("开始", self.start_task),
            ("暂停", self.pause_task),
            ("重新开始", self.restart_task)
        ])
        
        # 批量操作组
        self.add_action_group("批量操作", [
            ("开始全部", self.start_all),
            ("暂停全部", self.pause_all)
        ])
        
        # 文件操作组
        self.add_action_group("文件操作", [
            ("打开文件", self.open_file),
            ("打开文件夹", self.open_folder)
        ])
```

### 3. 主题系统

#### QSS样式架构
```
styles/
├── base.qss           # 基础样式
├── light_theme.qss    # 明亮主题
├── dark_theme.qss     # 暗黑主题
├── components/        # 组件样式
│   ├── buttons.qss
│   ├── progress.qss
│   ├── cards.qss
│   └── menus.qss
└── macos/            # macOS特定样式
    ├── window.qss
    ├── scrollbar.qss
    └── effects.qss
```

#### 主题切换机制
```python
class ThemeManager:
    def __init__(self):
        self.current_theme = "light"
        self.themes = {
            "light": self.load_light_theme(),
            "dark": self.load_dark_theme()
        }
    
    def switch_theme(self, theme_name: str):
        # 平滑过渡动画
        # 样式表更新
        # 配置保存
```

## 服务层设计

### 1. 下载服务

#### DownloadService
```python
class DownloadService:
    def __init__(self):
        self.task_manager = TaskManager()
        self.plugin_manager = PluginManager()
        self.progress_tracker = ProgressTracker()
    
    async def add_download(self, url: str, options: DownloadOptions):
        # URL分析和插件选择
        # 元数据提取
        # 任务创建和队列添加
        # 进度回调设置
    
    async def batch_download(self, urls: List[str]):
        # 批量任务处理
        # 并发控制
        # 错误处理和重试
```

#### 高级功能实现
- **断点续传**: 基于HTTP Range请求
- **多线程下载**: 文件分段并行下载
- **M3U8处理**: HLS流媒体解析和合并
- **代理支持**: 全局代理配置
- **限速控制**: 令牌桶算法

### 2. 监控服务

#### CreatorMonitorService
```python
class CreatorMonitorService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.creators = []
    
    async def add_creator(self, creator: CreatorProfile):
        # 创作者信息验证
        # 数据库存储
        # 监控任务调度
    
    async def check_updates(self, creator: CreatorProfile):
        # 获取最新视频列表
        # 与历史记录对比
        # 新视频检测和处理
```

### 3. 配置服务

#### ConfigService
```python
class ConfigService:
    def __init__(self):
        self.config_file = "config.json"
        self.settings = self.load_settings()
    
    def get(self, key: str, default=None):
        return self.settings.get(key, default)
    
    def set(self, key: str, value):
        self.settings[key] = value
        self.save_settings()
```

## 错误处理策略

### 1. 异常分类
- **网络异常**: 连接超时、DNS解析失败
- **解析异常**: URL无效、平台不支持
- **下载异常**: 文件损坏、磁盘空间不足
- **插件异常**: 插件加载失败、安全违规

### 2. 错误恢复机制
- **自动重试**: 指数退避算法
- **降级处理**: 质量降级、单线程模式
- **用户通知**: 友好的错误提示
- **日志记录**: 详细的错误日志

### 3. 安全机制
- **插件沙箱**: 限制插件系统访问
- **输入验证**: URL和用户输入验证
- **文件检查**: 下载文件安全扫描
- **权限控制**: 最小权限原则

## 测试策略

### 1. 单元测试
- **核心组件测试**: 下载器、提取器、插件系统
- **数据模型测试**: 数据验证和序列化
- **工具函数测试**: 辅助功能测试

### 2. 集成测试
- **端到端测试**: 完整下载流程
- **平台兼容性测试**: 各平台功能验证
- **性能测试**: 大量任务处理能力

### 3. UI测试
- **界面响应测试**: 用户交互响应
- **主题切换测试**: 样式正确性
- **动画效果测试**: 流畅度验证

## 部署和分发

### 1. 打包策略
- **PyInstaller**: 单文件可执行程序
- **依赖管理**: 自动检测和打包依赖
- **资源文件**: 样式、图标、配置文件

### 2. 平台适配
- **Windows**: .exe安装包，支持开机启动
- **macOS**: .app应用包，支持拖拽安装
- **Linux**: AppImage或deb/rpm包

### 3. 更新机制
- **自动更新检查**: 启动时检查新版本
- **增量更新**: 只下载变更部分
- **回滚机制**: 更新失败时恢复

## 性能优化

### 1. 内存管理
- **对象池**: 重用下载任务对象
- **缓存策略**: LRU缓存元数据
- **垃圾回收**: 及时清理无用对象

### 2. 网络优化
- **连接复用**: HTTP连接池
- **压缩传输**: 支持gzip压缩
- **CDN加速**: 智能选择下载节点

### 3. 界面优化
- **虚拟列表**: 大量任务时的性能优化
- **异步渲染**: 避免界面卡顿
- **资源预加载**: 提前加载常用资源

这个设计文档提供了完整的技术架构和实现方案，确保软件的功能完整性、性能优秀性和用户体验的优雅性。