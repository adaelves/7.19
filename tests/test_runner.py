"""
Test runner for the video downloader application.
Provides different test suites and reporting capabilities.
"""
import pytest
import sys
import os
import time
from pathlib import Path
from typing import List, Dict, Any
import json


class AutomatedTestRunner:
    """Test runner with different test suites and reporting"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.test_dir = self.project_root / "tests"
        self.reports_dir = self.project_root / "test_reports"
        self.reports_dir.mkdir(exist_ok=True)
    
    def run_unit_tests(self, verbose: bool = True) -> int:
        """Run unit tests only"""
        args = [
            str(self.test_dir),
            "-m", "unit",
            "--tb=short",
            f"--html={self.reports_dir}/unit_tests.html",
            "--self-contained-html"
        ]
        
        if verbose:
            args.append("-v")
        
        return pytest.main(args)
    
    def run_integration_tests(self, verbose: bool = True) -> int:
        """Run integration tests only"""
        args = [
            str(self.test_dir),
            "-m", "integration",
            "--tb=short",
            f"--html={self.reports_dir}/integration_tests.html",
            "--self-contained-html"
        ]
        
        if verbose:
            args.append("-v")
        
        return pytest.main(args)
    
    def run_ui_tests(self, verbose: bool = True) -> int:
        """Run UI tests only"""
        args = [
            str(self.test_dir),
            "-m", "ui",
            "--tb=short",
            f"--html={self.reports_dir}/ui_tests.html",
            "--self-contained-html"
        ]
        
        if verbose:
            args.append("-v")
        
        return pytest.main(args)
    
    def run_performance_tests(self, verbose: bool = True) -> int:
        """Run performance tests only"""
        args = [
            str(self.test_dir),
            "-m", "performance",
            "--tb=short",
            f"--html={self.reports_dir}/performance_tests.html",
            "--self-contained-html"
        ]
        
        if verbose:
            args.append("-v")
        
        return pytest.main(args)
    
    def run_all_tests(self, verbose: bool = True, exclude_slow: bool = False) -> int:
        """Run all tests"""
        args = [
            str(self.test_dir),
            "--tb=short",
            f"--html={self.reports_dir}/all_tests.html",
            "--self-contained-html",
            "--cov=app",
            f"--cov-report=html:{self.reports_dir}/coverage",
            f"--cov-report=json:{self.reports_dir}/coverage.json"
        ]
        
        if exclude_slow:
            args.extend(["-m", "not slow"])
        
        if verbose:
            args.append("-v")
        
        return pytest.main(args)
    
    def run_smoke_tests(self) -> int:
        """Run smoke tests (quick validation)"""
        args = [
            str(self.test_dir),
            "-m", "not slow and not performance",
            "--tb=line",
            "-x",  # Stop on first failure
            "--maxfail=5"
        ]
        
        return pytest.main(args)
    
    def run_network_tests(self, verbose: bool = True) -> int:
        """Run network-dependent tests"""
        args = [
            str(self.test_dir),
            "-m", "network",
            "--tb=short",
            f"--html={self.reports_dir}/network_tests.html",
            "--self-contained-html"
        ]
        
        if verbose:
            args.append("-v")
        
        return pytest.main(args)
    
    def run_specific_test(self, test_path: str, verbose: bool = True) -> int:
        """Run a specific test file or test function"""
        args = [test_path, "--tb=short"]
        
        if verbose:
            args.append("-v")
        
        return pytest.main(args)
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        report = {
            "timestamp": time.time(),
            "test_suites": {},
            "summary": {}
        }
        
        # Run different test suites and collect results
        test_suites = [
            ("unit", self.run_unit_tests),
            ("integration", self.run_integration_tests),
            ("ui", self.run_ui_tests),
            ("performance", self.run_performance_tests)
        ]
        
        total_passed = 0
        total_failed = 0
        
        for suite_name, run_func in test_suites:
            print(f"\n{'='*50}")
            print(f"Running {suite_name.upper()} tests...")
            print(f"{'='*50}")
            
            start_time = time.time()
            result = run_func(verbose=False)
            end_time = time.time()
            
            suite_report = {
                "result_code": result,
                "duration": end_time - start_time,
                "passed": result == 0
            }
            
            report["test_suites"][suite_name] = suite_report
            
            if result == 0:
                total_passed += 1
            else:
                total_failed += 1
        
        # Generate summary
        report["summary"] = {
            "total_suites": len(test_suites),
            "passed_suites": total_passed,
            "failed_suites": total_failed,
            "success_rate": total_passed / len(test_suites) if test_suites else 0
        }
        
        # Save report
        report_file = self.reports_dir / "test_summary.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def print_test_summary(self, report: Dict[str, Any]):
        """Print test summary to console"""
        print(f"\n{'='*60}")
        print("TEST SUMMARY")
        print(f"{'='*60}")
        
        summary = report["summary"]
        print(f"Total Test Suites: {summary['total_suites']}")
        print(f"Passed Suites: {summary['passed_suites']}")
        print(f"Failed Suites: {summary['failed_suites']}")
        print(f"Success Rate: {summary['success_rate']:.1%}")
        
        print(f"\n{'='*60}")
        print("DETAILED RESULTS")
        print(f"{'='*60}")
        
        for suite_name, suite_data in report["test_suites"].items():
            status = "✅ PASSED" if suite_data["passed"] else "❌ FAILED"
            duration = suite_data["duration"]
            print(f"{suite_name.upper():12} | {status} | {duration:.2f}s")
        
        print(f"\n{'='*60}")
        
        if summary["failed_suites"] > 0:
            print("⚠️  Some test suites failed. Check individual reports for details.")
        else:
            print("🎉 All test suites passed!")
        
        print(f"Reports saved to: {self.reports_dir}")


def main():
    """Main entry point for test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Video Downloader Test Runner")
    parser.add_argument(
        "suite",
        nargs="?",
        choices=["unit", "integration", "ui", "performance", "all", "smoke", "network", "report"],
        default="all",
        help="Test suite to run"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--exclude-slow",
        action="store_true",
        help="Exclude slow tests"
    )
    parser.add_argument(
        "--test",
        help="Run specific test file or function"
    )
    
    args = parser.parse_args()
    
    runner = AutomatedTestRunner()
    
    if args.test:
        # Run specific test
        result = runner.run_specific_test(args.test, args.verbose)
        sys.exit(result)
    
    # Run test suite
    if args.suite == "unit":
        result = runner.run_unit_tests(args.verbose)
    elif args.suite == "integration":
        result = runner.run_integration_tests(args.verbose)
    elif args.suite == "ui":
        result = runner.run_ui_tests(args.verbose)
    elif args.suite == "performance":
        result = runner.run_performance_tests(args.verbose)
    elif args.suite == "smoke":
        result = runner.run_smoke_tests()
    elif args.suite == "network":
        result = runner.run_network_tests(args.verbose)
    elif args.suite == "report":
        report = runner.generate_test_report()
        runner.print_test_summary(report)
        result = 0 if report["summary"]["failed_suites"] == 0 else 1
    else:  # all
        result = runner.run_all_tests(args.verbose, args.exclude_slow)
    
    sys.exit(result)


if __name__ == "__main__":
    main()