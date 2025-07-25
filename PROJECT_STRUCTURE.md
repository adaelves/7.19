# 📁 项目结构说明

经过清理和优化后，项目结构更加清晰简洁。

## 🚀 启动方式

### 主要启动方式（推荐）
```bash
# 默认启动（HTML风格界面）
python run.py

# 指定界面风格启动
python run.py html     # HTML风格界面（推荐）
python run.py native   # macOS原生风格界面
```

### 测试启动方式
```bash
# 界面选择器（可视化选择界面风格）
python test_html_style.py

# 直接启动指定风格
python test_html_style.py html    # HTML风格
python test_html_style.py native  # 原生风格
```

## 📂 项目目录结构

```
多平台视频下载器/
├── 📄 run.py                     # 🎯 主启动文件（推荐使用）
├── 📄 test_html_style.py         # 🧪 界面测试工具
├── 📄 requirements.txt           # 依赖包列表
├── 📄 README.md                  # 项目说明
├── 📄 PROJECT_STRUCTURE.md       # 项目结构说明（本文件）
├── 📄 video_downloader (1).html  # 原始设计稿
└── 📁 app/                       # 应用程序主目录
    ├── 📄 __init__.py
    ├── 📄 main_hybrid.py          # 混合启动器（备用）
    ├── 📁 core/                   # 核心功能模块
    ├── 📁 data/                   # 数据存储
    ├── 📁 plugins/                # 插件系统
    ├── 📁 services/               # 服务层
    └── 📁 ui/                     # 用户界面
        ├── 📄 __init__.py
        ├── 📄 html_style_window.py    # 🎨 HTML风格界面（主推荐）
        ├── 📄 main_window.py          # 🍎 macOS原生风格界面
        ├── 📄 macos_widgets.py        # 统一的macOS风格控件库
        ├── 📄 animation_helper.py     # 动画辅助工具
        ├── 📁 components/             # UI组件
        ├── 📁 dialogs/                # 对话框
        └── 📁 styles/                 # 样式文件
            ├── 📄 theme_manager.py    # 主题管理器
            ├── 📄 base.qss           # 基础样式
            ├── 📄 light_theme.qss    # 浅色主题
            ├── 📄 dark_theme.qss     # 深色主题
            ├── 📁 components/        # 组件样式
            └── 📁 macos/            # macOS特定样式
```

## 🎨 界面风格说明

### 1. HTML风格界面（推荐）⭐
- **文件**: `app/ui/html_style_window.py`
- **特点**: 完全按照 `video_downloader (1).html` 设计实现
- **尺寸**: 900x600 固定窗口
- **风格**: 现代化macOS设计，Tailwind CSS颜色系统
- **功能**: 完整的下载管理界面

### 2. macOS原生风格界面
- **文件**: `app/ui/main_window.py`
- **特点**: 100% macOS原生设计规范
- **尺寸**: 响应式窗口（最小800x500）
- **风格**: Apple Human Interface Guidelines
- **功能**: 原生macOS体验

## 🧹 清理内容

### 已删除的重复文件
- ❌ `demo_macos_native_complete.py`
- ❌ `demo_professional_ui.py`
- ❌ `test_macos_effects.py`
- ❌ `test_macos_native.py`
- ❌ `test_professional_macos.py`
- ❌ `app/ui/professional_macos_window.py`
- ❌ `app/ui/enhanced_interface.html`
- ❌ `app/ui/web_interface.html`
- ❌ `app/ui/web_interface.py`
- ❌ `app/ui/macos_widgets_native.py`
- ❌ `app/ui/start.bat`
- ❌ `app/ui/styles/professional_macos.qss`
- ❌ `INTERFACE_IMPLEMENTATION_SUMMARY.md`

### 合并的文件
- ✅ `app/ui/macos_widgets_native.py` → `app/ui/macos_widgets.py`（统一控件库）

### 优化的文件
- ✅ `run.py` - 重构为统一的主启动文件
- ✅ `test_html_style.py` - 改进为界面选择器工具

## 💡 使用建议

1. **日常使用**: 直接运行 `python run.py`
2. **界面测试**: 使用 `python test_html_style.py` 进行可视化选择
3. **开发调试**: 根据需要选择不同的界面风格

## 🎯 推荐启动方式

```bash
# 最简单的启动方式（推荐）
python run.py
```

这将启动HTML风格界面，完全按照您的设计稿实现，功能完整，视觉效果最佳！

## 📊 清理统计

- **删除文件**: 13个重复/冗余文件
- **合并文件**: 2个控件库文件合并为1个
- **启动文件**: 从8个减少到2个
- **UI实现**: 从4个减少到2个
- **项目更清晰**: 用户不再困惑该用哪个启动文件

现在项目结构清晰简洁，启动方式明确，代码重复度大大降低！