#!/usr/bin/env python3
"""
Portable application builder for VideoDownloader.
Builds portable versions for Windows, macOS, and Linux.
"""

import os
import sys
import platform
import subprocess
import shutil
import zipfile
import tarfile
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import argparse
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Project configuration
PROJECT_ROOT = Path(__file__).parent.parent
APP_NAME = "VideoDownloader"
VERSION = "1.0.0"
AUTHOR = "VideoDownloader Project"

# Platform detection
CURRENT_PLATFORM = platform.system().lower()
IS_WINDOWS = CURRENT_PLATFORM == "windows"
IS_MACOS = CURRENT_PLATFORM == "darwin"
IS_LINUX = CURRENT_PLATFORM == "linux"

# Build directories
BUILD_DIR = PROJECT_ROOT / "build"
DIST_DIR = PROJECT_ROOT / "dist"
PORTABLE_DIR = PROJECT_ROOT / "portable"
ASSETS_DIR = PROJECT_ROOT / "assets"


class PortableBuilder:
    """Builder for portable application packages."""
    
    def __init__(self, target_platform: Optional[str] = None):
        self.target_platform = target_platform or CURRENT_PLATFORM
        self.build_dir = BUILD_DIR / self.target_platform
        self.dist_dir = DIST_DIR / self.target_platform
        self.portable_dir = PORTABLE_DIR / self.target_platform
        
        # Ensure directories exist
        for directory in [self.build_dir, self.dist_dir, self.portable_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def clean_build_dirs(self) -> None:
        """Clean build directories."""
        logger.info("Cleaning build directories...")
        
        for directory in [self.build_dir, self.dist_dir]:
            if directory.exists():
                shutil.rmtree(directory)
                directory.mkdir(parents=True, exist_ok=True)
    
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are available."""
        logger.info("Checking dependencies...")
        
        # Check PyInstaller
        try:
            import PyInstaller
            logger.info(f"PyInstaller version: {PyInstaller.__version__}")
        except ImportError:
            logger.error("PyInstaller not found. Install with: pip install pyinstaller")
            return False
        
        # Check main application
        main_script = PROJECT_ROOT / "app" / "main.py"
        if not main_script.exists():
            logger.error(f"Main script not found: {main_script}")
            return False
        
        # Check required modules
        required_modules = ['PySide6', 'requests', 'aiohttp']
        for module in required_modules:
            try:
                __import__(module)
                logger.info(f"✓ {module}")
            except ImportError:
                logger.error(f"✗ {module} not found")
                return False
        
        return True
    
    def generate_pyinstaller_spec(self) -> Path:
        """Generate PyInstaller spec file."""
        logger.info(f"Generating PyInstaller spec for {self.target_platform}...")
        
        # Import configuration
        sys.path.insert(0, str(PROJECT_ROOT / "build_scripts"))
        from pyinstaller_config import generate_spec_file
        
        spec_file = generate_spec_file()
        logger.info(f"Spec file generated: {spec_file}")
        return spec_file
    
    def build_with_pyinstaller(self) -> bool:
        """Build application with PyInstaller."""
        logger.info("Building application with PyInstaller...")
        
        try:
            # Generate spec file
            spec_file = self.generate_pyinstaller_spec()
            
            # Run PyInstaller
            cmd = [
                sys.executable, '-m', 'PyInstaller',
                '--clean',
                '--noconfirm',
                str(spec_file)
            ]
            
            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"PyInstaller failed: {result.stderr}")
                return False
            
            logger.info("PyInstaller build completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Build failed: {e}")
            return False
    
    def create_portable_structure(self) -> bool:
        """Create portable directory structure."""
        logger.info("Creating portable structure...")
        
        try:
            # Find built application
            if IS_WINDOWS:
                app_source = DIST_DIR / APP_NAME
                if not app_source.exists():
                    logger.error(f"Built application not found: {app_source}")
                    return False
            elif IS_MACOS:
                app_source = DIST_DIR / f"{APP_NAME}.app"
                if not app_source.exists():
                    logger.error(f"Built application not found: {app_source}")
                    return False
            else:  # Linux
                app_source = DIST_DIR / APP_NAME
                if not app_source.exists():
                    logger.error(f"Built application not found: {app_source}")
                    return False
            
            # Create portable directory
            portable_app_dir = self.portable_dir / f"{APP_NAME}_Portable"
            if portable_app_dir.exists():
                shutil.rmtree(portable_app_dir)
            portable_app_dir.mkdir(parents=True)
            
            # Copy application
            if IS_WINDOWS:
                # Copy entire directory for Windows
                shutil.copytree(app_source, portable_app_dir / APP_NAME)
                
                # Create launcher script
                launcher_script = portable_app_dir / f"{APP_NAME}.bat"
                launcher_script.write_text(
                    f'@echo off\n'
                    f'cd /d "%~dp0"\n'
                    f'set VIDEODOWNLOADER_PORTABLE=1\n'
                    f'"{APP_NAME}\\{APP_NAME}.exe" %*\n',
                    encoding='utf-8'
                )
                
            elif IS_MACOS:
                # Copy .app bundle
                shutil.copytree(app_source, portable_app_dir / f"{APP_NAME}.app")
                
                # Create launcher script
                launcher_script = portable_app_dir / f"Run_{APP_NAME}.command"
                launcher_script.write_text(
                    f'#!/bin/bash\n'
                    f'cd "$(dirname "$0")"\n'
                    f'export VIDEODOWNLOADER_PORTABLE=1\n'
                    f'open "{APP_NAME}.app"\n',
                    encoding='utf-8'
                )
                launcher_script.chmod(0o755)
                
            else:  # Linux
                # Copy executable
                shutil.copy2(app_source, portable_app_dir / APP_NAME)
                
                # Create launcher script
                launcher_script = portable_app_dir / f"run_{APP_NAME}.sh"
                launcher_script.write_text(
                    f'#!/bin/bash\n'
                    f'cd "$(dirname "$0")"\n'
                    f'export VIDEODOWNLOADER_PORTABLE=1\n'
                    f'./{APP_NAME} "$@"\n',
                    encoding='utf-8'
                )
                launcher_script.chmod(0o755)
            
            # Create portable marker
            portable_marker = portable_app_dir / "portable.txt"
            portable_marker.write_text(
                f"{APP_NAME} Portable Version {VERSION}\n"
                f"======================================\n\n"
                f"This is a portable version of {APP_NAME}.\n"
                f"All configuration and data will be stored in the 'Data' folder.\n\n"
                f"To run the application:\n"
                f"- Windows: Double-click {APP_NAME}.bat\n"
                f"- macOS: Double-click Run_{APP_NAME}.command\n"
                f"- Linux: Run ./run_{APP_NAME}.sh\n\n"
                f"For more information, visit: https://github.com/your-repo\n",
                encoding='utf-8'
            )
            
            # Create Data directory structure
            data_dir = portable_app_dir / "Data"
            data_subdirs = ["Config", "Cache", "Logs", "Downloads", "Plugins", "Backups"]
            for subdir in data_subdirs:
                (data_dir / subdir).mkdir(parents=True, exist_ok=True)
            
            # Create README files
            self._create_readme_files(portable_app_dir)
            
            # Copy additional files
            self._copy_additional_files(portable_app_dir)
            
            logger.info(f"Portable structure created: {portable_app_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create portable structure: {e}")
            return False
    
    def _create_readme_files(self, portable_dir: Path) -> None:
        """Create README files for portable version."""
        # Main README
        main_readme = portable_dir / "README.txt"
        main_readme.write_text(
            f"{APP_NAME} Portable v{VERSION}\n"
            f"{'=' * (len(APP_NAME) + len(VERSION) + 12)}\n\n"
            f"Thank you for using {APP_NAME}!\n\n"
            f"QUICK START:\n"
            f"-----------\n"
            f"1. Run the launcher script for your platform\n"
            f"2. The application will start in portable mode\n"
            f"3. All data will be stored in the 'Data' folder\n\n"
            f"FEATURES:\n"
            f"---------\n"
            f"• Download videos from multiple platforms\n"
            f"• Batch download support\n"
            f"• Creator monitoring\n"
            f"• Plugin system\n"
            f"• Cross-platform compatibility\n\n"
            f"SYSTEM REQUIREMENTS:\n"
            f"-------------------\n"
            f"• Windows 10+ / macOS 10.13+ / Linux (modern distro)\n"
            f"• 4GB RAM minimum\n"
            f"• 1GB free disk space\n"
            f"• Internet connection\n\n"
            f"SUPPORT:\n"
            f"--------\n"
            f"• GitHub: https://github.com/your-repo\n"
            f"• Issues: https://github.com/your-repo/issues\n"
            f"• Documentation: https://github.com/your-repo/wiki\n\n"
            f"LICENSE:\n"
            f"--------\n"
            f"This software is open source. See LICENSE file for details.\n",
            encoding='utf-8'
        )
        
        # Data directory README
        data_readme = portable_dir / "Data" / "README.txt"
        data_readme.write_text(
            f"{APP_NAME} Data Directory\n"
            f"{'=' * (len(APP_NAME) + 16)}\n\n"
            f"This directory contains all user data for the portable version:\n\n"
            f"DIRECTORIES:\n"
            f"------------\n"
            f"• Config/    - Application settings and configuration\n"
            f"• Cache/     - Temporary files and thumbnails\n"
            f"• Logs/      - Application log files\n"
            f"• Downloads/ - Default download location\n"
            f"• Plugins/   - User-installed plugins\n"
            f"• Backups/   - Automatic backups of settings\n\n"
            f"BACKUP:\n"
            f"-------\n"
            f"To backup your data, simply copy this entire 'Data' folder.\n"
            f"To restore, replace the 'Data' folder with your backup.\n\n"
            f"MIGRATION:\n"
            f"----------\n"
            f"You can move this portable version to any location.\n"
            f"All settings and data will be preserved.\n",
            encoding='utf-8'
        )
    
    def _copy_additional_files(self, portable_dir: Path) -> None:
        """Copy additional files to portable directory."""
        # Copy license if exists
        license_file = PROJECT_ROOT / "LICENSE"
        if license_file.exists():
            shutil.copy2(license_file, portable_dir / "LICENSE.txt")
        
        # Copy changelog if exists
        changelog_file = PROJECT_ROOT / "CHANGELOG.md"
        if changelog_file.exists():
            shutil.copy2(changelog_file, portable_dir / "CHANGELOG.txt")
        
        # Copy icons if exist
        if ASSETS_DIR.exists():
            icons = list(ASSETS_DIR.glob("icon.*"))
            if icons:
                icons_dir = portable_dir / "Icons"
                icons_dir.mkdir(exist_ok=True)
                for icon in icons:
                    shutil.copy2(icon, icons_dir / icon.name)
    
    def create_archive(self, archive_format: str = "zip") -> Optional[Path]:
        """Create archive of portable application."""
        logger.info(f"Creating {archive_format} archive...")
        
        try:
            portable_app_dir = self.portable_dir / f"{APP_NAME}_Portable"
            if not portable_app_dir.exists():
                logger.error("Portable directory not found")
                return None
            
            # Determine archive name
            platform_suffix = {
                'windows': 'Win64',
                'darwin': 'macOS',
                'linux': 'Linux64'
            }.get(self.target_platform, self.target_platform)
            
            archive_name = f"{APP_NAME}_v{VERSION}_{platform_suffix}_Portable"
            
            if archive_format.lower() == "zip":
                archive_path = self.portable_dir / f"{archive_name}.zip"
                
                with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
                    for file_path in portable_app_dir.rglob('*'):
                        if file_path.is_file():
                            arcname = file_path.relative_to(portable_app_dir.parent)
                            zf.write(file_path, arcname)
                            
            elif archive_format.lower() in ["tar.gz", "tgz"]:
                archive_path = self.portable_dir / f"{archive_name}.tar.gz"
                
                with tarfile.open(archive_path, 'w:gz') as tf:
                    tf.add(portable_app_dir, arcname=portable_app_dir.name)
            
            else:
                logger.error(f"Unsupported archive format: {archive_format}")
                return None
            
            # Calculate archive size
            archive_size = archive_path.stat().st_size / (1024 * 1024)  # MB
            logger.info(f"Archive created: {archive_path} ({archive_size:.1f} MB)")
            
            return archive_path
            
        except Exception as e:
            logger.error(f"Failed to create archive: {e}")
            return None
    
    def build_portable(self, clean: bool = True, archive_format: str = "zip") -> bool:
        """Build complete portable application."""
        logger.info(f"Building portable {APP_NAME} for {self.target_platform}...")
        
        try:
            # Clean build directories
            if clean:
                self.clean_build_dirs()
            
            # Check dependencies
            if not self.check_dependencies():
                return False
            
            # Build with PyInstaller
            if not self.build_with_pyinstaller():
                return False
            
            # Create portable structure
            if not self.create_portable_structure():
                return False
            
            # Create archive
            archive_path = self.create_archive(archive_format)
            if not archive_path:
                return False
            
            logger.info(f"✅ Portable build completed successfully!")
            logger.info(f"📦 Archive: {archive_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Build failed: {e}")
            return False
    
    def get_build_info(self) -> Dict[str, Any]:
        """Get build information."""
        return {
            'app_name': APP_NAME,
            'version': VERSION,
            'target_platform': self.target_platform,
            'current_platform': CURRENT_PLATFORM,
            'build_dir': str(self.build_dir),
            'dist_dir': str(self.dist_dir),
            'portable_dir': str(self.portable_dir),
        }


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description=f"Build portable {APP_NAME}")
    parser.add_argument(
        '--platform', '-p',
        choices=['windows', 'darwin', 'linux', 'all'],
        default=CURRENT_PLATFORM,
        help='Target platform (default: current platform)'
    )
    parser.add_argument(
        '--no-clean', 
        action='store_true',
        help='Skip cleaning build directories'
    )
    parser.add_argument(
        '--archive-format', '-f',
        choices=['zip', 'tar.gz'],
        default='zip',
        help='Archive format (default: zip)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Build for specified platform(s)
    if args.platform == 'all':
        platforms = ['windows', 'darwin', 'linux']
        success_count = 0
        
        for platform in platforms:
            logger.info(f"\n{'='*60}")
            logger.info(f"Building for {platform}")
            logger.info(f"{'='*60}")
            
            builder = PortableBuilder(platform)
            if builder.build_portable(clean=not args.no_clean, archive_format=args.archive_format):
                success_count += 1
            else:
                logger.error(f"Build failed for {platform}")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Build Summary: {success_count}/{len(platforms)} successful")
        logger.info(f"{'='*60}")
        
        return success_count == len(platforms)
    
    else:
        builder = PortableBuilder(args.platform)
        return builder.build_portable(clean=not args.no_clean, archive_format=args.archive_format)


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)