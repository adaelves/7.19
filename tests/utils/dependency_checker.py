"""
Dependency checker utility for cross-platform compatibility.
Automatically detects and validates required dependencies.
"""

import os
import sys
import platform
import subprocess
import shutil
import importlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json


class DependencyChecker:
    """Utility class for checking system dependencies."""
    
    def __init__(self):
        self.platform = platform.system()
        self.python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        self.results = {}
    
    def check_all_dependencies(self) -> Dict:
        """Check all dependencies and return results."""
        self.results = {
            'platform_info': self.get_platform_info(),
            'python_info': self.check_python_compatibility(),
            'system_dependencies': self.check_system_dependencies(),
            'python_packages': self.check_python_packages(),
            'optional_tools': self.check_optional_tools(),
            'ui_dependencies': self.check_ui_dependencies(),
            'network_capabilities': self.check_network_capabilities(),
        }
        return self.results
    
    def get_platform_info(self) -> Dict:
        """Get detailed platform information."""
        return {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'architecture': platform.architecture(),
            'python_implementation': platform.python_implementation(),
            'python_version': platform.python_version(),
        }
    
    def check_python_compatibility(self) -> Dict:
        """Check Python version compatibility."""
        version_info = sys.version_info
        is_compatible = version_info >= (3, 8)
        
        return {
            'version': f"{version_info.major}.{version_info.minor}.{version_info.micro}",
            'is_compatible': is_compatible,
            'minimum_required': '3.8.0',
            'executable_path': sys.executable,
            'prefix': sys.prefix,
            'path': sys.path[:3],  # First 3 paths only
        }
    
    def check_system_dependencies(self) -> Dict:
        """Check system-level dependencies."""
        dependencies = {}
        
        # Check for common system tools
        system_tools = {
            'Windows': ['powershell.exe', 'cmd.exe'],
            'Darwin': ['bash', 'zsh', 'which'],
            'Linux': ['bash', 'which', 'ls', 'grep'],
        }
        
        tools_to_check = system_tools.get(self.platform, [])
        
        for tool in tools_to_check:
            path = shutil.which(tool)
            dependencies[tool] = {
                'available': path is not None,
                'path': path,
            }
        
        return dependencies
    
    def check_python_packages(self) -> Dict:
        """Check required Python packages."""
        required_packages = [
            'PySide6',
            'requests',
            'aiohttp',
            'asyncio',
            'sqlite3',
            'pathlib',
            'json',
            'urllib',
            'threading',
            'multiprocessing',
        ]
        
        optional_packages = [
            'pytest',
            'pytest-asyncio',
            'pytest-qt',
            'coverage',
            'black',
            'flake8',
        ]
        
        results = {
            'required': {},
            'optional': {},
        }
        
        # Check required packages
        for package in required_packages:
            try:
                module = importlib.import_module(package)
                version = getattr(module, '__version__', 'unknown')
                results['required'][package] = {
                    'available': True,
                    'version': version,
                    'path': getattr(module, '__file__', 'built-in'),
                }
            except ImportError as e:
                results['required'][package] = {
                    'available': False,
                    'error': str(e),
                }
        
        # Check optional packages
        for package in optional_packages:
            try:
                module = importlib.import_module(package)
                version = getattr(module, '__version__', 'unknown')
                results['optional'][package] = {
                    'available': True,
                    'version': version,
                }
            except ImportError:
                results['optional'][package] = {
                    'available': False,
                }
        
        return results
    
    def check_optional_tools(self) -> Dict:
        """Check optional external tools."""
        tools = {
            'ffmpeg': ['ffmpeg', 'ffmpeg.exe'],
            'yt-dlp': ['yt-dlp', 'yt-dlp.exe'],
            'git': ['git', 'git.exe'],
            'pip': ['pip', 'pip3', 'pip.exe'],
        }
        
        results = {}
        
        for tool_name, commands in tools.items():
            found = False
            tool_path = None
            version = None
            
            for cmd in commands:
                path = shutil.which(cmd)
                if path:
                    found = True
                    tool_path = path
                    
                    # Try to get version
                    try:
                        result = subprocess.run(
                            [cmd, '--version'],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        if result.returncode == 0:
                            version = result.stdout.strip().split('\n')[0]
                    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                        pass
                    
                    break
            
            results[tool_name] = {
                'available': found,
                'path': tool_path,
                'version': version,
            }
        
        return results
    
    def check_ui_dependencies(self) -> Dict:
        """Check UI framework dependencies."""
        results = {}
        
        # Check PySide6 components
        pyside6_modules = [
            'PySide6.QtCore',
            'PySide6.QtWidgets',
            'PySide6.QtGui',
            'PySide6.QtNetwork',
            'PySide6.QtMultimedia',
        ]
        
        for module_name in pyside6_modules:
            try:
                module = importlib.import_module(module_name)
                results[module_name] = {
                    'available': True,
                    'version': getattr(module, '__version__', 'unknown'),
                }
            except ImportError as e:
                results[module_name] = {
                    'available': False,
                    'error': str(e),
                }
        
        # Check display availability (for GUI tests)
        display_available = True
        if self.platform in ['Linux', 'Darwin']:
            display_available = os.environ.get('DISPLAY') is not None
        
        results['display'] = {
            'available': display_available,
            'variable': os.environ.get('DISPLAY', 'N/A'),
        }
        
        return results
    
    def check_network_capabilities(self) -> Dict:
        """Check network-related capabilities."""
        results = {}
        
        # Check SSL support
        try:
            import ssl
            protocols = []
            try:
                # Try to get available protocols
                if hasattr(ssl, '_PROTOCOL_NAMES'):
                    protocols = list(ssl._PROTOCOL_NAMES.keys())
                else:
                    # Fallback to common protocols
                    common_protocols = ['TLSv1', 'TLSv1_1', 'TLSv1_2']
                    for protocol in common_protocols:
                        if hasattr(ssl, f'PROTOCOL_{protocol.replace(".", "_")}'):
                            protocols.append(protocol)
            except:
                protocols = ['TLS_AVAILABLE']
            
            results['ssl'] = {
                'available': True,
                'version': ssl.OPENSSL_VERSION,
                'protocols': protocols,
            }
        except ImportError:
            results['ssl'] = {'available': False}
        
        # Check socket support
        try:
            import socket
            results['socket'] = {
                'available': True,
                'ipv6_support': socket.has_ipv6,
            }
        except ImportError:
            results['socket'] = {'available': False}
        
        # Check requests library
        try:
            import requests
            results['requests'] = {
                'available': True,
                'version': requests.__version__,
            }
        except ImportError:
            results['requests'] = {'available': False}
        
        return results
    
    def generate_report(self) -> str:
        """Generate a human-readable dependency report."""
        if not self.results:
            self.check_all_dependencies()
        
        report = []
        report.append("=" * 60)
        report.append("CROSS-PLATFORM COMPATIBILITY REPORT")
        report.append("=" * 60)
        
        # Platform info
        platform_info = self.results['platform_info']
        report.append(f"\nPlatform: {platform_info['system']} {platform_info['release']}")
        report.append(f"Architecture: {platform_info['architecture'][0]}")
        report.append(f"Python: {platform_info['python_version']} ({platform_info['python_implementation']})")
        
        # Python compatibility
        python_info = self.results['python_info']
        status = "✓" if python_info['is_compatible'] else "✗"
        report.append(f"\nPython Compatibility: {status}")
        report.append(f"  Version: {python_info['version']}")
        report.append(f"  Required: {python_info['minimum_required']}+")
        
        # Required packages
        report.append("\nRequired Python Packages:")
        required_packages = self.results['python_packages']['required']
        for package, info in required_packages.items():
            status = "✓" if info['available'] else "✗"
            version = f" ({info.get('version', 'unknown')})" if info['available'] else ""
            report.append(f"  {status} {package}{version}")
        
        # Optional tools
        report.append("\nOptional Tools:")
        optional_tools = self.results['optional_tools']
        for tool, info in optional_tools.items():
            status = "✓" if info['available'] else "✗"
            version = f" ({info.get('version', 'unknown')})" if info['available'] and info.get('version') else ""
            report.append(f"  {status} {tool}{version}")
        
        # UI dependencies
        report.append("\nUI Dependencies:")
        ui_deps = self.results['ui_dependencies']
        for module, info in ui_deps.items():
            if module != 'display':
                status = "✓" if info['available'] else "✗"
                report.append(f"  {status} {module}")
        
        display_status = "✓" if ui_deps['display']['available'] else "✗"
        report.append(f"  {display_status} Display available")
        
        # Network capabilities
        report.append("\nNetwork Capabilities:")
        network = self.results['network_capabilities']
        for capability, info in network.items():
            status = "✓" if info['available'] else "✗"
            report.append(f"  {status} {capability}")
        
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)
    
    def save_report(self, filepath: str) -> None:
        """Save the dependency report to a file."""
        report = self.generate_report()
        Path(filepath).write_text(report, encoding='utf-8')
    
    def save_json_report(self, filepath: str) -> None:
        """Save the dependency results as JSON."""
        if not self.results:
            self.check_all_dependencies()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, default=str)


def main():
    """Main function to run dependency check."""
    checker = DependencyChecker()
    
    print("Checking dependencies...")
    checker.check_all_dependencies()
    
    # Print report
    print(checker.generate_report())
    
    # Save reports
    reports_dir = Path("test_reports")
    reports_dir.mkdir(exist_ok=True)
    
    platform_name = platform.system().lower()
    checker.save_report(f"test_reports/dependency_report_{platform_name}.txt")
    checker.save_json_report(f"test_reports/dependency_report_{platform_name}.json")
    
    print(f"\nReports saved to test_reports/dependency_report_{platform_name}.*")


if __name__ == '__main__':
    main()