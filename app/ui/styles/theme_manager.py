"""
主题管理器 - 负责管理macOS风格的主题切换
"""
import json
from pathlib import Path
from typing import Dict, Any
from PySide6.QtCore import QObject, Signal


class ThemeManager(QObject):
    """主题管理器"""
    
    theme_changed = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.current_theme = "light"
        self.themes_dir = Path(__file__).parent
        self.config_file = Path.home() / ".video_downloader" / "theme_config.json"
        self.load_settings()
        
    def load_settings(self):
        """加载主题设置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.current_theme = config.get('theme', 'light')
        except Exception:
            self.current_theme = "light"
            
    def save_settings(self):
        """保存主题设置"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            config = {'theme': self.current_theme}
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        except Exception:
            pass
            
    def set_theme(self, theme_name: str):
        """设置主题"""
        if theme_name in ['light', 'dark']:
            self.current_theme = theme_name
            self.theme_changed.emit(theme_name)
            
    def get_stylesheet(self) -> str:
        """获取当前主题的样式表"""
        # 加载基础样式
        base_style = self._load_style_file("base.qss")
        
        # 加载主题特定样式
        theme_style = self._load_style_file(f"{self.current_theme}_theme.qss")
        
        # 加载组件样式
        components_style = self._load_components_styles()
        
        # 加载macOS特定样式
        macos_style = self._load_style_file("macos/window.qss")
        
        return f"{base_style}\n{theme_style}\n{components_style}\n{macos_style}"
        
    def _load_style_file(self, filename: str) -> str:
        """加载样式文件"""
        try:
            style_path = self.themes_dir / filename
            if style_path.exists():
                with open(style_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception:
            pass
        return ""
        
    def _load_components_styles(self) -> str:
        """加载所有组件样式"""
        components_dir = self.themes_dir / "components"
        if not components_dir.exists():
            return ""
            
        styles = []
        for style_file in components_dir.glob("*.qss"):
            try:
                with open(style_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 替换CSS变量为实际颜色值
                    content = self._replace_css_variables(content)
                    styles.append(content)
            except Exception:
                continue
                
        return "\n".join(styles)
        
    def _replace_css_variables(self, css_content: str) -> str:
        """替换CSS变量为实际颜色值"""
        colors = self.get_theme_colors()
        
        # 替换CSS变量
        replacements = {
            'var(--background)': colors['background'],
            'var(--surface)': colors['surface'],
            'var(--primary)': colors['primary'],
            'var(--secondary)': colors['secondary'],
            'var(--text-primary)': colors['text_primary'],
            'var(--text-secondary)': colors['text_secondary'],
            'var(--border)': colors['border'],
            'var(--accent)': colors['accent']
        }
        
        for var, color in replacements.items():
            css_content = css_content.replace(var, color)
            
        return css_content
        
    def get_theme_colors(self) -> Dict[str, str]:
        """获取当前主题的颜色配置"""
        if self.current_theme == "dark":
            return {
                'background': '#1e1e1e',
                'surface': '#2d2d2d',
                'primary': '#007aff',
                'secondary': '#5856d6',
                'text_primary': '#ffffff',
                'text_secondary': '#8e8e93',
                'border': '#38383a',
                'accent': '#ff9500'
            }
        else:  # light theme
            return {
                'background': '#f2f2f7',
                'surface': '#ffffff',
                'primary': '#007aff',
                'secondary': '#5856d6',
                'text_primary': '#000000',
                'text_secondary': '#8e8e93',
                'border': '#c6c6c8',
                'accent': '#ff9500'
            }