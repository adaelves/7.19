"""
Cross-platform compatibility test runner.
Runs all compatibility tests and generates comprehensive reports.
"""

import os
import sys
import platform
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import argparse

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.utils.dependency_checker import DependencyChecker


class CompatibilityTestRunner:
    """Runner for cross-platform compatibility tests."""
    
    def __init__(self, output_dir: str = "test_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.platform_name = platform.system().lower()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results = {}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all compatibility tests."""
        print("=" * 60)
        print("CROSS-PLATFORM COMPATIBILITY TEST SUITE")
        print("=" * 60)
        print(f"Platform: {platform.system()} {platform.release()}")
        print(f"Python: {platform.python_version()}")
        print(f"Architecture: {platform.machine()}")
        print("=" * 60)
        
        self.results = {
            'platform_info': self._get_platform_info(),
            'timestamp': self.timestamp,
            'tests': {}
        }
        
        # Run dependency check
        print("\n1. Checking dependencies...")
        self.results['tests']['dependencies'] = self._run_dependency_check()
        
        # Run Python version compatibility tests
        print("\n2. Running Python version compatibility tests...")
        self.results['tests']['python_compatibility'] = self._run_python_tests()
        
        # Run cross-platform compatibility tests
        print("\n3. Running cross-platform compatibility tests...")
        self.results['tests']['cross_platform'] = self._run_cross_platform_tests()
        
        # Run UI compatibility tests (if display available)
        print("\n4. Running UI compatibility tests...")
        self.results['tests']['ui_compatibility'] = self._run_ui_tests()
        
        # Run network compatibility tests
        print("\n5. Running network compatibility tests...")
        self.results['tests']['network_compatibility'] = self._run_network_tests()
        
        # Generate reports
        print("\n6. Generating reports...")
        self._generate_reports()
        
        return self.results
    
    def _get_platform_info(self) -> Dict[str, Any]:
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
            'python_executable': sys.executable,
        }
    
    def _run_dependency_check(self) -> Dict[str, Any]:
        """Run dependency check."""
        try:
            checker = DependencyChecker()
            results = checker.check_all_dependencies()
            
            # Save detailed dependency report
            report_file = self.output_dir / f"dependencies_{self.platform_name}_{self.timestamp}.txt"
            checker.save_report(str(report_file))
            
            json_file = self.output_dir / f"dependencies_{self.platform_name}_{self.timestamp}.json"
            checker.save_json_report(str(json_file))
            
            print("   ✓ Dependency check completed")
            return {
                'status': 'success',
                'summary': self._summarize_dependencies(results),
                'report_file': str(report_file),
                'json_file': str(json_file),
            }
        except Exception as e:
            print(f"   ✗ Dependency check failed: {e}")
            return {
                'status': 'failed',
                'error': str(e),
            }
    
    def _run_python_tests(self) -> Dict[str, Any]:
        """Run Python version compatibility tests."""
        try:
            cmd = [
                sys.executable, '-m', 'pytest',
                'tests/test_python_version_compatibility.py',
                '-v', '--tb=short',
                f'--junitxml={self.output_dir}/python_compatibility_{self.platform_name}_{self.timestamp}.xml'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)
            
            success = result.returncode == 0
            print(f"   {'✓' if success else '✗'} Python compatibility tests {'passed' if success else 'failed'}")
            
            return {
                'status': 'success' if success else 'failed',
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'xml_report': f"python_compatibility_{self.platform_name}_{self.timestamp}.xml",
            }
        except Exception as e:
            print(f"   ✗ Python compatibility tests failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
            }
    
    def _run_cross_platform_tests(self) -> Dict[str, Any]:
        """Run cross-platform compatibility tests."""
        try:
            cmd = [
                sys.executable, '-m', 'pytest',
                'tests/test_cross_platform_compatibility.py',
                '-v', '--tb=short',
                f'--junitxml={self.output_dir}/cross_platform_{self.platform_name}_{self.timestamp}.xml'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)
            
            success = result.returncode == 0
            print(f"   {'✓' if success else '✗'} Cross-platform tests {'passed' if success else 'failed'}")
            
            return {
                'status': 'success' if success else 'failed',
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'xml_report': f"cross_platform_{self.platform_name}_{self.timestamp}.xml",
            }
        except Exception as e:
            print(f"   ✗ Cross-platform tests failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
            }
    
    def _run_ui_tests(self) -> Dict[str, Any]:
        """Run UI compatibility tests."""
        try:
            # Check if display is available
            display_available = True
            if platform.system() in ['Linux', 'Darwin']:
                display_available = os.environ.get('DISPLAY') is not None
            
            if not display_available:
                print("   ⚠ Skipping UI tests (no display available)")
                return {
                    'status': 'skipped',
                    'reason': 'No display available',
                }
            
            cmd = [
                sys.executable, '-m', 'pytest',
                'tests/test_cross_platform_compatibility.py::TestUICompatibility',
                '-v', '--tb=short',
                f'--junitxml={self.output_dir}/ui_compatibility_{self.platform_name}_{self.timestamp}.xml'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)
            
            success = result.returncode == 0
            print(f"   {'✓' if success else '✗'} UI compatibility tests {'passed' if success else 'failed'}")
            
            return {
                'status': 'success' if success else 'failed',
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'xml_report': f"ui_compatibility_{self.platform_name}_{self.timestamp}.xml",
            }
        except Exception as e:
            print(f"   ✗ UI compatibility tests failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
            }
    
    def _run_network_tests(self) -> Dict[str, Any]:
        """Run network compatibility tests."""
        try:
            cmd = [
                sys.executable, '-m', 'pytest',
                'tests/test_cross_platform_compatibility.py::TestNetworkCompatibility',
                '-v', '--tb=short',
                f'--junitxml={self.output_dir}/network_compatibility_{self.platform_name}_{self.timestamp}.xml'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)
            
            success = result.returncode == 0
            print(f"   {'✓' if success else '✗'} Network compatibility tests {'passed' if success else 'failed'}")
            
            return {
                'status': 'success' if success else 'failed',
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'xml_report': f"network_compatibility_{self.platform_name}_{self.timestamp}.xml",
            }
        except Exception as e:
            print(f"   ✗ Network compatibility tests failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
            }
    
    def _summarize_dependencies(self, dep_results: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize dependency check results."""
        summary = {
            'python_compatible': dep_results['python_info']['is_compatible'],
            'required_packages': {},
            'optional_tools': {},
            'ui_available': True,
            'network_available': True,
        }
        
        # Summarize required packages
        for package, info in dep_results['python_packages']['required'].items():
            summary['required_packages'][package] = info['available']
        
        # Summarize optional tools
        for tool, info in dep_results['optional_tools'].items():
            summary['optional_tools'][tool] = info['available']
        
        # Check UI availability
        ui_deps = dep_results['ui_dependencies']
        summary['ui_available'] = all(
            info['available'] for module, info in ui_deps.items()
            if module.startswith('PySide6')
        )
        
        # Check network availability
        network_deps = dep_results['network_capabilities']
        summary['network_available'] = all(
            info['available'] for info in network_deps.values()
        )
        
        return summary
    
    def _generate_reports(self) -> None:
        """Generate comprehensive test reports."""
        # Generate summary report
        summary_file = self.output_dir / f"compatibility_summary_{self.platform_name}_{self.timestamp}.txt"
        self._generate_summary_report(summary_file)
        
        # Generate JSON report
        json_file = self.output_dir / f"compatibility_results_{self.platform_name}_{self.timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\nReports generated:")
        print(f"  Summary: {summary_file}")
        print(f"  JSON: {json_file}")
        
        # List all generated files
        report_files = list(self.output_dir.glob(f"*_{self.platform_name}_{self.timestamp}.*"))
        if report_files:
            print(f"\nAll generated files:")
            for file in sorted(report_files):
                print(f"  {file}")
    
    def _generate_summary_report(self, filepath: Path) -> None:
        """Generate a human-readable summary report."""
        lines = []
        lines.append("=" * 80)
        lines.append("CROSS-PLATFORM COMPATIBILITY TEST SUMMARY")
        lines.append("=" * 80)
        
        # Platform info
        platform_info = self.results['platform_info']
        lines.append(f"\nPlatform: {platform_info['system']} {platform_info['release']}")
        lines.append(f"Architecture: {platform_info['architecture'][0]}")
        lines.append(f"Python: {platform_info['python_version']} ({platform_info['python_implementation']})")
        lines.append(f"Test Date: {self.timestamp}")
        
        # Test results summary
        lines.append("\nTEST RESULTS:")
        lines.append("-" * 40)
        
        for test_name, test_result in self.results['tests'].items():
            status = test_result.get('status', 'unknown')
            status_symbol = {
                'success': '✓',
                'failed': '✗',
                'error': '✗',
                'skipped': '⚠',
            }.get(status, '?')
            
            lines.append(f"{status_symbol} {test_name.replace('_', ' ').title()}: {status.upper()}")
            
            if status in ['failed', 'error'] and 'error' in test_result:
                lines.append(f"    Error: {test_result['error']}")
        
        # Dependency summary
        if 'dependencies' in self.results['tests'] and 'summary' in self.results['tests']['dependencies']:
            dep_summary = self.results['tests']['dependencies']['summary']
            lines.append("\nDEPENDENCY SUMMARY:")
            lines.append("-" * 40)
            
            python_status = "✓" if dep_summary['python_compatible'] else "✗"
            lines.append(f"{python_status} Python Version Compatible")
            
            ui_status = "✓" if dep_summary['ui_available'] else "✗"
            lines.append(f"{ui_status} UI Framework Available")
            
            network_status = "✓" if dep_summary['network_available'] else "✗"
            lines.append(f"{network_status} Network Capabilities Available")
            
            # Required packages
            lines.append("\nRequired Packages:")
            for package, available in dep_summary['required_packages'].items():
                status = "✓" if available else "✗"
                lines.append(f"  {status} {package}")
            
            # Optional tools
            lines.append("\nOptional Tools:")
            for tool, available in dep_summary['optional_tools'].items():
                status = "✓" if available else "✗"
                lines.append(f"  {status} {tool}")
        
        lines.append("\n" + "=" * 80)
        
        filepath.write_text("\n".join(lines), encoding='utf-8')


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run cross-platform compatibility tests")
    parser.add_argument(
        '--output-dir', '-o',
        default='test_reports',
        help='Output directory for test reports'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    # Run tests
    runner = CompatibilityTestRunner(args.output_dir)
    results = runner.run_all_tests()
    
    # Print final summary
    print("\n" + "=" * 60)
    print("TEST EXECUTION COMPLETED")
    print("=" * 60)
    
    total_tests = len(results['tests'])
    successful_tests = sum(1 for test in results['tests'].values() if test.get('status') == 'success')
    failed_tests = sum(1 for test in results['tests'].values() if test.get('status') in ['failed', 'error'])
    skipped_tests = sum(1 for test in results['tests'].values() if test.get('status') == 'skipped')
    
    print(f"Total test suites: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Skipped: {skipped_tests}")
    
    if failed_tests > 0:
        print("\n⚠ Some tests failed. Check the detailed reports for more information.")
        sys.exit(1)
    else:
        print("\n✓ All tests passed successfully!")
        sys.exit(0)


if __name__ == '__main__':
    main()