# 🎬 多平台视频下载器

一个现代化的多平台视频下载工具，采用macOS风格设计，支持多个主流视频平台。

## ✨ 功能特点

- 🎥 **多平台支持** - 支持YouTube、Bilibili、抖音等主流平台
- 🎨 **精美界面** - 完全按照macOS设计规范实现
- 📱 **响应式设计** - 适配不同屏幕尺寸
- 🌙 **主题切换** - 支持浅色/深色主题
- 📊 **实时进度** - 可视化下载进度和状态
- 🔄 **批量下载** - 支持队列和批量操作
- 📁 **路径管理** - 自定义下载路径
- 🎵 **格式选择** - 支持视频/音频格式转换

## 🚀 快速开始

### 系统要求
- Python 3.8+
- PySide6
- yt-dlp
- requests

### 安装步骤

1. **克隆仓库**
```bash
git clone <repository-url>
cd video-downloader
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **启动程序**
```bash
# 默认启动（HTML风格界面，推荐）
python run.py

# 或选择界面风格
python run.py html     # HTML风格界面
python run.py native   # macOS原生风格界面
```

### 界面测试
```bash
# 可视化界面选择器
python test_html_style.py
```

## 🎨 界面风格

### HTML风格界面（推荐）⭐
- 完全按照设计稿实现
- 900x600固定窗口
- 现代化macOS设计
- Tailwind CSS颜色系统

### macOS原生风格界面
- 100% Apple设计规范
- 响应式窗口大小
- SF Pro字体系统
- 原生交互体验

## 📖 使用说明

1. **启动程序** - 运行 `python run.py`
2. **输入链接** - 在搜索框中粘贴视频URL
3. **添加下载** - 点击"添加下载"按钮
4. **监控进度** - 在下载列表中查看实时进度
5. **管理文件** - 使用操作按钮控制下载状态

## 🌐 支持的平台

- ✅ YouTube
- ✅ Bilibili (哔哩哔哩)
- ✅ 抖音 (TikTok)
- ✅ 快手
- ✅ 微博视频
- ✅ 西瓜视频
- 🔄 更多平台持续添加中...

## 📁 项目结构

```
多平台视频下载器/
├── run.py                     # 主启动文件
├── test_html_style.py         # 界面测试工具
└── app/
    ├── ui/
    │   ├── html_style_window.py   # HTML风格界面（推荐）
    │   ├── main_window.py         # macOS原生界面
    │   └── styles/                # 样式文件
    ├── core/                      # 核心功能
    ├── services/                  # 服务层
    └── plugins/                   # 插件系统
```

## 🛠️ 开发说明

- **主界面**: `app/ui/html_style_window.py` (推荐使用)
- **样式管理**: `app/ui/styles/theme_manager.py`
- **控件库**: `app/ui/macos_widgets.py`
- **动画系统**: `app/ui/animation_helper.py`

## 🧹 项目优化

经过全面清理，项目现在更加简洁：
- **删除了13个重复/冗余文件**
- **启动文件从8个减少到2个**
- **UI实现从4个减少到2个**
- **统一了控件库**

## 🤝 贡献

欢迎提交Issue和Pull Request来帮助改进项目！

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

💡 **提示**: 推荐使用 `python run.py` 启动，将获得最佳的界面体验！