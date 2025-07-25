# Multi-platform Video Downloader

一个功能强大的跨平台视频下载器，支持多个主流视频平台，采用现代化GUI界面设计。

## ✨ 主要特性

- 🎬 **多平台支持**: YouTube, B站, 抖音, Instagram, Twitter等
- 📱 **社交媒体**: 支持各大社交媒体平台的视频和图片下载
- 🔄 **批量下载**: 支持批量下载和创作者监控
- 🎨 **现代UI**: 基于PySide6的现代化界面设计
- 🔌 **插件系统**: 可扩展的插件架构
- 💾 **便携版**: 支持便携模式，数据本地存储
- 🌍 **跨平台**: Windows, macOS, Linux全平台支持

## 🚀 快速开始

### 方法1: 直接运行（推荐）

#### Windows用户
1. 双击 `VideoDownloader.bat` 文件
2. 等待依赖检查完成
3. 应用程序将自动启动

#### macOS/Linux用户
1. 打开终端，进入项目目录
2. 运行: `chmod +x run_VideoDownloader.sh`
3. 运行: `./run_VideoDownloader.sh`

#### 通用方法
```bash
# 使用Python启动器
python run.py

# 或直接运行主程序
python app/main.py
```

### 方法2: 手动安装依赖

```bash
# 1. 安装Python依赖
pip install PySide6 requests aiohttp yt-dlp

# 2. 运行应用程序
python app/main.py
```

## 📋 系统要求

- **Python**: 3.8 或更高版本
- **操作系统**: Windows 10+, macOS 10.13+, 或现代Linux发行版
- **内存**: 4GB RAM 最低
- **存储**: 1GB 可用空间
- **网络**: 互联网连接

## 🎯 使用方法

1. **启动应用程序**
   - 使用上述任一方法启动应用程序

2. **下载视频**
   - 在URL输入框中粘贴视频链接
   - 点击"开始下载"按钮或按回车键
   - 在下载标签页中查看进度

3. **查看历史**
   - 切换到"历史"标签页查看下载记录

4. **配置设置**
   - 在"设置"标签页中查看和修改配置

## 🔧 开发者指南

### 安装开发依赖

```bash
# 安装基础依赖
pip install PySide6 requests aiohttp yt-dlp

# 安装开发工具
pip install pytest pytest-qt pytest-asyncio black flake8 isort

# 安装打包工具
pip install pyinstaller
```

### 运行测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行便携版测试
python -m pytest tests/test_portable_build.py -v

# 运行兼容性测试
python tests/run_compatibility_tests.py
```

### 构建便携版

```bash
# 构建当前平台
python build_portable.py

# 构建所有平台
python build_portable.py --platform all

# 使用Makefile (如果可用)
make build-portable
```

## 📦 便携版说明

应用程序支持便携模式，所有配置和数据将存储在应用程序目录下的 `Data` 文件夹中：

```
VideoDownloader/
├── VideoDownloader.bat      # Windows启动器
├── run_VideoDownloader.sh   # Linux/macOS启动器
├── run.py                   # Python启动器
├── app/                     # 应用程序代码
├── Data/                    # 便携数据目录
│   ├── Config/             # 配置文件
│   ├── Downloads/          # 默认下载目录
│   ├── Cache/              # 缓存文件
│   ├── Logs/               # 日志文件
│   └── Plugins/            # 插件目录
└── portable.txt            # 便携模式标记
```

## 🐛 故障排除

### 常见问题

1. **"未找到Python"错误**
   - 确保已安装Python 3.8+
   - 确保Python已添加到系统PATH

2. **"缺少依赖"错误**
   - 运行: `pip install PySide6 requests aiohttp yt-dlp`

3. **界面显示异常**
   - 确保显示器支持GUI应用程序
   - 在Linux上可能需要安装额外的GUI库

4. **下载失败**
   - 检查网络连接
   - 确认视频链接有效
   - 某些平台可能需要特殊处理

### 获取帮助

- 查看日志输出（在应用程序的"下载"标签页中）
- 检查 `Data/Logs/` 目录中的日志文件
- 在GitHub上提交Issue

## 📄 许可证

本项目采用开源许可证。详见 [LICENSE](LICENSE) 文件。

## 🤝 贡献

欢迎贡献代码！请查看贡献指南了解详情。

## 📞 联系方式

- GitHub: [项目仓库地址]
- Issues: [问题反馈地址]
- 文档: [项目文档地址]

---

**注意**: 请遵守各平台的服务条款，仅下载您有权下载的内容。