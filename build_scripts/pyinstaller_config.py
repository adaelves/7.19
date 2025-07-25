"""
PyInstaller configuration for portable video downloader application.
Supports Windows, macOS, and Linux portable builds.
"""

import os
import sys
import platform
from pathlib import Path

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent
APP_NAME = "VideoDownloader"
VERSION = "1.0.0"

# Platform-specific configurations
PLATFORM = platform.system().lower()
IS_WINDOWS = PLATFORM == "windows"
IS_MACOS = PLATFORM == "darwin"
IS_LINUX = PLATFORM == "linux"

# Build directories
BUILD_DIR = PROJECT_ROOT / "build"
DIST_DIR = PROJECT_ROOT / "dist"
PORTABLE_DIR = PROJECT_ROOT / "portable"

# Application entry point
MAIN_SCRIPT = PROJECT_ROOT / "app" / "main.py"

# Data files and directories to include
DATA_FILES = [
    # UI styles and themes
    (str(PROJECT_ROOT / "app" / "ui" / "styles"), "app/ui/styles"),
    # Configuration templates
    (str(PROJECT_ROOT / "app" / "config"), "app/config"),
    # Plugin directory
    (str(PROJECT_ROOT / "app" / "plugins"), "app/plugins"),
    # Examples and documentation
    (str(PROJECT_ROOT / "examples"), "examples"),
    # License and readme
    (str(PROJECT_ROOT / "README.md"), "."),
    (str(PROJECT_ROOT / "LICENSE"), ".") if (PROJECT_ROOT / "LICENSE").exists() else None,
]

# Filter out None entries
DATA_FILES = [item for item in DATA_FILES if item is not None]

# Hidden imports (modules that PyInstaller might miss)
HIDDEN_IMPORTS = [
    # PySide6 modules
    'PySide6.QtCore',
    'PySide6.QtWidgets', 
    'PySide6.QtGui',
    'PySide6.QtNetwork',
    'PySide6.QtMultimedia',
    
    # Network and HTTP libraries
    'requests',
    'aiohttp',
    'urllib3',
    
    # Video processing
    'yt_dlp',
    'ffmpeg',
    
    # Database
    'sqlite3',
    
    # Async support
    'asyncio',
    'concurrent.futures',
    
    # Plugin system
    'importlib.util',
    'pkgutil',
    
    # Application modules
    'app.core',
    'app.ui',
    'app.services',
    'app.plugins',
    'app.data',
]

# Excluded modules (to reduce size)
EXCLUDED_MODULES = [
    # Development and testing
    'pytest',
    'unittest',
    'doctest',
    'pdb',
    
    # Documentation
    'pydoc',
    'help',
    
    # Unused standard library modules
    'tkinter',
    'turtle',
    'curses',
    'readline',
    
    # Unused network modules
    'ftplib',
    'poplib',
    'imaplib',
    'nntplib',
    'telnetlib',
]

# Platform-specific configurations
def get_platform_config():
    """Get platform-specific PyInstaller configuration."""
    config = {
        'name': APP_NAME,
        'script': str(MAIN_SCRIPT),
        'datas': DATA_FILES,
        'hiddenimports': HIDDEN_IMPORTS,
        'excludes': EXCLUDED_MODULES,
        'noconfirm': True,
        'clean': True,
        'distpath': str(DIST_DIR),
        'workpath': str(BUILD_DIR),
    }
    
    if IS_WINDOWS:
        config.update({
            'onefile': False,  # Use onedir for portable version
            'console': False,  # GUI application
            'icon': str(PROJECT_ROOT / "assets" / "icon.ico") if (PROJECT_ROOT / "assets" / "icon.ico").exists() else None,
            'version_file': str(PROJECT_ROOT / "build_scripts" / "version_info.txt"),
            'uac_admin': False,  # Don't require admin privileges
        })
    
    elif IS_MACOS:
        config.update({
            'onefile': False,  # Use app bundle
            'windowed': True,  # GUI application
            'icon': str(PROJECT_ROOT / "assets" / "icon.icns") if (PROJECT_ROOT / "assets" / "icon.icns").exists() else None,
            'bundle_identifier': f'com.videodownloader.{APP_NAME.lower()}',
        })
    
    elif IS_LINUX:
        config.update({
            'onefile': True,  # Single AppImage-style executable
            'console': False,  # GUI application
            'icon': str(PROJECT_ROOT / "assets" / "icon.png") if (PROJECT_ROOT / "assets" / "icon.png").exists() else None,
        })
    
    # Remove None values
    config = {k: v for k, v in config.items() if v is not None}
    
    return config

# PyInstaller spec file template
SPEC_TEMPLATE = """
# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Add project root to path
project_root = Path(r'{project_root}')
sys.path.insert(0, str(project_root))

block_cipher = None

a = Analysis(
    [r'{script}'],
    pathex=[r'{project_root}'],
    binaries=[],
    datas={datas},
    hiddenimports={hiddenimports},
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes={excludes},
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

{exe_config}

{collect_config}
"""

def generate_spec_file():
    """Generate PyInstaller spec file for current platform."""
    config = get_platform_config()
    
    # Platform-specific EXE configuration
    if IS_WINDOWS:
        exe_config = f"""
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='{APP_NAME}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=r'{config.get("icon", "")}',
    version=r'{PROJECT_ROOT / "build_scripts" / "version_info.txt"}',
)
"""
        
        collect_config = f"""
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='{APP_NAME}',
)
"""
    
    elif IS_MACOS:
        exe_config = f"""
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='{APP_NAME}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=r'{config.get("icon", "")}',
)
"""
        
        collect_config = f"""
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='{APP_NAME}',
)

app = BUNDLE(
    coll,
    name='{APP_NAME}.app',
    icon=r'{config.get("icon", "")}',
    bundle_identifier='{config.get("bundle_identifier", "com.videodownloader.app")}',
    info_plist={{
        'CFBundleName': '{APP_NAME}',
        'CFBundleDisplayName': 'Video Downloader',
        'CFBundleVersion': '{VERSION}',
        'CFBundleShortVersionString': '{VERSION}',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.13.0',
    }},
)
"""
    
    elif IS_LINUX:
        exe_config = f"""
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{APP_NAME}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=r'{config.get("icon", "")}',
)
"""
        collect_config = ""
    
    # Generate spec content
    spec_content = SPEC_TEMPLATE.format(
        project_root=PROJECT_ROOT,
        script=MAIN_SCRIPT,
        datas=repr(DATA_FILES),
        hiddenimports=repr(HIDDEN_IMPORTS),
        excludes=repr(EXCLUDED_MODULES),
        exe_config=exe_config,
        collect_config=collect_config,
    )
    
    # Write spec file
    spec_file = PROJECT_ROOT / "build_scripts" / f"{APP_NAME}_{PLATFORM}.spec"
    spec_file.parent.mkdir(exist_ok=True)
    spec_file.write_text(spec_content, encoding='utf-8')
    
    return spec_file

if __name__ == '__main__':
    print(f"Generating PyInstaller spec for {PLATFORM}...")
    spec_file = generate_spec_file()
    print(f"Spec file generated: {spec_file}")
    
    # Print configuration summary
    config = get_platform_config()
    print(f"\nConfiguration summary:")
    print(f"  Platform: {PLATFORM}")
    print(f"  App name: {APP_NAME}")
    print(f"  Version: {VERSION}")
    print(f"  Main script: {MAIN_SCRIPT}")
    print(f"  Data files: {len(DATA_FILES)} items")
    print(f"  Hidden imports: {len(HIDDEN_IMPORTS)} modules")
    print(f"  Excluded modules: {len(EXCLUDED_MODULES)} modules")