"""
Test framework validation for cross-platform compatibility testing.
Validates that all test components are properly implemented and working.
"""

import os
import sys
import platform
import subprocess
from pathlib import Path
from typing import List, Dict, Any
import pytest
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.utils.dependency_checker import DependencyChecker


class TestFrameworkValidation:
    """Validate the cross-platform testing framework."""
    
    def test_dependency_checker_functionality(self):
        """Test that dependency checker works correctly."""
        checker = DependencyChecker()
        results = checker.check_all_dependencies()
        
        # Verify all expected sections are present
        expected_sections = [
            'platform_info',
            'python_info',
            'system_dependencies',
            'python_packages',
            'optional_tools',
            'ui_dependencies',
            'network_capabilities',
        ]
        
        for section in expected_sections:
            assert section in results, f"Missing section: {section}"
        
        # Verify platform info
        platform_info = results['platform_info']
        assert 'system' in platform_info
        assert 'python_version' in platform_info
        assert platform_info['system'] in ['Windows', 'Darwin', 'Linux']
        
        # Verify Python compatibility
        python_info = results['python_info']
        assert 'is_compatible' in python_info
        assert 'version' in python_info
        assert isinstance(python_info['is_compatible'], bool)
    
    def test_dependency_report_generation(self):
        """Test that dependency reports can be generated."""
        checker = DependencyChecker()
        checker.check_all_dependencies()
        
        # Test text report generation
        report = checker.generate_report()
        assert isinstance(report, str)
        assert len(report) > 0
        assert "CROSS-PLATFORM COMPATIBILITY REPORT" in report
        
        # Test that report contains platform information
        assert platform.system() in report
        assert "Python Compatibility" in report
    
    def test_test_runner_functionality(self):
        """Test that the compatibility test runner works."""
        from tests.run_compatibility_tests import CompatibilityTestRunner
        
        # Create a test runner
        runner = CompatibilityTestRunner("test_temp_reports")
        
        # Test platform info gathering
        platform_info = runner._get_platform_info()
        assert 'system' in platform_info
        assert 'python_version' in platform_info
        assert 'python_executable' in platform_info
        
        # Cleanup
        import shutil
        temp_dir = Path("test_temp_reports")
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
    
    def test_cross_platform_test_structure(self):
        """Test that cross-platform tests are properly structured."""
        test_file = Path("tests/test_cross_platform_compatibility.py")
        assert test_file.exists(), "Cross-platform test file missing"
        
        # Read the test file and verify it contains expected test classes
        content = test_file.read_text()
        
        expected_classes = [
            "TestCrossPlatformCompatibility",
            "TestWindowsCompatibility",
            "TestMacOSCompatibility", 
            "TestLinuxCompatibility",
            "TestDependencyDetection",
            "TestUICompatibility",
            "TestNetworkCompatibility",
        ]
        
        for class_name in expected_classes:
            assert f"class {class_name}" in content, f"Missing test class: {class_name}"
    
    def test_python_version_test_structure(self):
        """Test that Python version tests are properly structured."""
        test_file = Path("tests/test_python_version_compatibility.py")
        assert test_file.exists(), "Python version test file missing"
        
        content = test_file.read_text()
        
        expected_classes = [
            "TestPythonVersionCompatibility",
            "TestVersionSpecificFeatures",
        ]
        
        for class_name in expected_classes:
            assert f"class {class_name}" in content, f"Missing test class: {class_name}"
        
        # Check for version-specific tests
        version_features = [
            "walrus_operator",
            "positional_only",
            "dict_merge",
            "match_statement",
        ]
        
        for feature in version_features:
            assert feature in content, f"Missing version feature test: {feature}"
    
    @pytest.mark.slow
    def test_actual_test_execution(self):
        """Test that tests can actually be executed."""
        # Run a subset of tests to verify they work
        cmd = [
            sys.executable, '-m', 'pytest',
            'tests/test_python_version_compatibility.py::TestPythonVersionCompatibility::test_minimum_python_version',
            '-v'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)
        assert result.returncode == 0, f"Test execution failed: {result.stderr}"
        assert "PASSED" in result.stdout or "passed" in result.stdout
    
    def test_github_workflow_structure(self):
        """Test that GitHub Actions workflow is properly configured."""
        workflow_file = Path(".github/workflows/compatibility-tests.yml")
        assert workflow_file.exists(), "GitHub Actions workflow missing"
        
        content = workflow_file.read_text(encoding='utf-8')
        
        # Check for required workflow components
        required_components = [
            "name: Cross-Platform Compatibility Tests",
            "strategy:",
            "matrix:",
            "os: [ubuntu-latest, windows-latest, macos-latest]",
            "python-version:",
            "uses: actions/setup-python@v4",
            "pip install pytest",
        ]
        
        for component in required_components:
            assert component in content, f"Missing workflow component: {component}"
    
    def test_test_reports_directory(self):
        """Test that test reports directory exists and contains reports."""
        reports_dir = Path("test_reports")
        assert reports_dir.exists(), "Test reports directory missing"
        
        # Check for recent report files
        report_files = list(reports_dir.glob("*.txt")) + list(reports_dir.glob("*.json"))
        assert len(report_files) > 0, "No test reports found"
    
    def test_platform_specific_tests(self):
        """Test that platform-specific tests are properly marked."""
        test_file = Path("tests/test_cross_platform_compatibility.py")
        content = test_file.read_text()
        
        # Check for platform-specific skip markers
        platform_markers = [
            '@pytest.mark.skipif(platform.system() != \'Windows\'',
            '@pytest.mark.skipif(platform.system() != \'Darwin\'',
            '@pytest.mark.skipif(platform.system() != \'Linux\'',
        ]
        
        for marker in platform_markers:
            assert marker in content, f"Missing platform marker: {marker}"
    
    def test_test_markers(self):
        """Test that appropriate test markers are used."""
        # Check for slow test markers
        slow_tests = [
            "test_actual_test_execution",
            "test_http_requests",
        ]
        
        # Verify markers are properly defined
        pytest_ini = Path("tests/pytest.ini")
        if pytest_ini.exists():
            content = pytest_ini.read_text()
            assert "markers" in content or "slow" in content


class TestTestCategories:
    """Test that all test categories are properly implemented."""
    
    def test_dependency_tests_exist(self):
        """Test that dependency tests exist and are comprehensive."""
        checker = DependencyChecker()
        results = checker.check_all_dependencies()
        
        # Verify all dependency categories are checked
        assert 'python_packages' in results
        assert 'optional_tools' in results
        assert 'ui_dependencies' in results
        assert 'network_capabilities' in results
        
        # Verify required packages are checked
        required_packages = results['python_packages']['required']
        essential_packages = ['PySide6', 'requests', 'sqlite3', 'asyncio']
        
        for package in essential_packages:
            assert package in required_packages, f"Missing required package check: {package}"
    
    def test_platform_tests_coverage(self):
        """Test that all major platforms are covered."""
        test_file = Path("tests/test_cross_platform_compatibility.py")
        content = test_file.read_text()
        
        # Check for Windows-specific tests
        assert "TestWindowsCompatibility" in content
        assert "test_windows_file_paths" in content
        assert "test_windows_registry_access" in content
        
        # Check for macOS-specific tests
        assert "TestMacOSCompatibility" in content
        assert "test_macos_file_paths" in content
        assert "test_macos_permissions" in content
        
        # Check for Linux-specific tests
        assert "TestLinuxCompatibility" in content
        assert "test_linux_file_paths" in content
        assert "test_linux_permissions" in content
    
    def test_python_version_coverage(self):
        """Test that Python version compatibility is comprehensive."""
        test_file = Path("tests/test_python_version_compatibility.py")
        content = test_file.read_text()
        
        # Check for version-specific feature tests
        version_features = [
            "async_await_support",
            "dataclasses_support", 
            "typing_support",
            "pathlib_support",
            "f_string_support",
        ]
        
        for feature in version_features:
            assert f"test_{feature}" in content, f"Missing Python feature test: {feature}"
    
    @pytest.mark.network
    def test_network_tests_exist(self):
        """Test that network compatibility tests exist."""
        test_file = Path("tests/test_cross_platform_compatibility.py")
        content = test_file.read_text()
        
        assert "TestNetworkCompatibility" in content
        assert "test_http_requests" in content
        assert "test_ssl_support" in content
    
    def test_ui_tests_exist(self):
        """Test that UI compatibility tests exist."""
        test_file = Path("tests/test_cross_platform_compatibility.py")
        content = test_file.read_text()
        
        assert "TestUICompatibility" in content
        assert "test_qt_availability" in content
        assert "test_window_creation" in content


def test_framework_completeness():
    """Test that the testing framework is complete and functional."""
    # Verify all major components exist
    required_files = [
        "tests/test_cross_platform_compatibility.py",
        "tests/test_python_version_compatibility.py", 
        "tests/utils/dependency_checker.py",
        "tests/run_compatibility_tests.py",
        ".github/workflows/compatibility-tests.yml",
    ]
    
    for file_path in required_files:
        assert Path(file_path).exists(), f"Required file missing: {file_path}"
    
    # Verify test reports can be generated
    reports_dir = Path("test_reports")
    assert reports_dir.exists(), "Test reports directory missing"


def test_test_categories_implemented():
    """Test that all required test categories are implemented."""
    categories = {
        'platform_detection': 'test_platform_detection',
        'file_path_handling': 'test_file_path_handling', 
        'database_compatibility': 'test_database_compatibility',
        'python_version_compatibility': 'test_python_version_compatibility',
        'dependency_detection': 'test_python_executable_detection',
        'ui_compatibility': 'test_qt_availability',
        'network_compatibility': 'test_http_requests',
    }
    
    test_file = Path("tests/test_cross_platform_compatibility.py")
    content = test_file.read_text()
    
    for category, test_name in categories.items():
        assert test_name in content, f"Missing test for category {category}: {test_name}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])