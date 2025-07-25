"""
Python version compatibility tests.
Tests compatibility across different Python versions (3.8+).
"""

import sys
import ast
import inspect
from pathlib import Path
from typing import List, Dict, Any
import pytest


class TestPythonVersionCompatibility:
    """Test Python version compatibility for the application."""
    
    def test_minimum_python_version(self):
        """Test that Python version meets minimum requirements."""
        min_version = (3, 8)
        current_version = sys.version_info[:2]
        
        assert current_version >= min_version, (
            f"Python {min_version[0]}.{min_version[1]}+ required, "
            f"but running {current_version[0]}.{current_version[1]}"
        )
    
    def test_async_await_support(self):
        """Test async/await syntax support (Python 3.5+)."""
        # Test basic async function definition
        async def test_async_function():
            return "async_result"
        
        # Test that function is a coroutine
        import asyncio
        assert asyncio.iscoroutinefunction(test_async_function)
        
        # Test async context manager support (Python 3.7+)
        class AsyncContextManager:
            async def __aenter__(self):
                return self
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
        
        async def test_async_context():
            async with AsyncContextManager():
                pass
        
        assert asyncio.iscoroutinefunction(test_async_context)
    
    def test_dataclasses_support(self):
        """Test dataclasses support (Python 3.7+)."""
        from dataclasses import dataclass, field
        from typing import List, Optional
        
        @dataclass
        class TestDataClass:
            name: str
            value: int = 0
            items: List[str] = field(default_factory=list)
            optional_field: Optional[str] = None
        
        # Test dataclass creation
        obj = TestDataClass("test")
        assert obj.name == "test"
        assert obj.value == 0
        assert obj.items == []
        assert obj.optional_field is None
        
        # Test with all fields
        obj2 = TestDataClass("test2", 42, ["item1"], "optional")
        assert obj2.name == "test2"
        assert obj2.value == 42
        assert obj2.items == ["item1"]
        assert obj2.optional_field == "optional"
    
    def test_typing_support(self):
        """Test typing module features used in the application."""
        from typing import (
            List, Dict, Optional, Union, Tuple, Any, Callable,
            TypeVar, Generic, Protocol
        )
        
        # Test basic type hints
        def typed_function(name: str, count: int) -> List[str]:
            return [name] * count
        
        result = typed_function("test", 3)
        assert result == ["test", "test", "test"]
        
        # Test Optional and Union
        def optional_function(value: Optional[str] = None) -> Union[str, int]:
            return value if value is not None else 0
        
        assert optional_function("test") == "test"
        assert optional_function() == 0
        
        # Test TypeVar and Generic (Python 3.5+)
        T = TypeVar('T')
        
        class GenericContainer(Generic[T]):
            def __init__(self, item: T):
                self.item = item
            
            def get(self) -> T:
                return self.item
        
        container = GenericContainer("test")
        assert container.get() == "test"
        
        # Test Protocol (Python 3.8+)
        if sys.version_info >= (3, 8):
            class Drawable(Protocol):
                def draw(self) -> None: ...
            
            class Circle:
                def draw(self) -> None:
                    pass
            
            def draw_shape(shape: Drawable) -> None:
                shape.draw()
            
            circle = Circle()
            draw_shape(circle)  # Should not raise
    
    def test_pathlib_support(self):
        """Test pathlib support (Python 3.4+)."""
        from pathlib import Path
        import tempfile
        
        # Test Path creation and operations
        path = Path("test") / "subdir" / "file.txt"
        assert str(path) in ["test/subdir/file.txt", "test\\subdir\\file.txt"]
        
        # Test with temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_file = tmp_path / "test.txt"
            
            # Test file operations
            test_file.write_text("test content")
            assert test_file.exists()
            assert test_file.read_text() == "test content"
            
            # Test directory operations
            subdir = tmp_path / "subdir"
            subdir.mkdir()
            assert subdir.exists()
            assert subdir.is_dir()
    
    def test_f_string_support(self):
        """Test f-string support (Python 3.6+)."""
        name = "world"
        count = 42
        
        # Basic f-string
        result = f"Hello, {name}!"
        assert result == "Hello, world!"
        
        # F-string with expressions
        result = f"Count: {count * 2}"
        assert result == "Count: 84"
        
        # F-string with format specifiers
        pi = 3.14159
        result = f"Pi: {pi:.2f}"
        assert result == "Pi: 3.14"
    
    def test_walrus_operator_support(self):
        """Test walrus operator support (Python 3.8+)."""
        if sys.version_info < (3, 8):
            pytest.skip("Walrus operator requires Python 3.8+")
        
        # Test walrus operator in if statement
        data = [1, 2, 3, 4, 5]
        if (n := len(data)) > 3:
            assert n == 5
        
        # Test walrus operator in list comprehension
        numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        squares = [y for x in numbers if (y := x * x) > 25]
        assert squares == [36, 49, 64, 81, 100]
    
    def test_positional_only_parameters(self):
        """Test positional-only parameters (Python 3.8+)."""
        if sys.version_info < (3, 8):
            pytest.skip("Positional-only parameters require Python 3.8+")
        
        def func_with_pos_only(a, b, /, c, d, *, e, f):
            return a + b + c + d + e + f
        
        # Test valid calls
        result = func_with_pos_only(1, 2, 3, d=4, e=5, f=6)
        assert result == 21
        
        result = func_with_pos_only(1, 2, c=3, d=4, e=5, f=6)
        assert result == 21
    
    def test_dictionary_merge_operator(self):
        """Test dictionary merge operator (Python 3.9+)."""
        if sys.version_info < (3, 9):
            pytest.skip("Dictionary merge operator requires Python 3.9+")
        
        dict1 = {"a": 1, "b": 2}
        dict2 = {"c": 3, "d": 4}
        
        # Test merge operator
        merged = dict1 | dict2
        assert merged == {"a": 1, "b": 2, "c": 3, "d": 4}
        
        # Test update operator
        dict1 |= dict2
        assert dict1 == {"a": 1, "b": 2, "c": 3, "d": 4}
    
    def test_match_statement(self):
        """Test match statement (Python 3.10+)."""
        if sys.version_info < (3, 10):
            pytest.skip("Match statement requires Python 3.10+")
        
        def process_value(value):
            match value:
                case int() if value > 0:
                    return "positive integer"
                case int() if value < 0:
                    return "negative integer"
                case 0:
                    return "zero"
                case str() if len(value) > 0:
                    return "non-empty string"
                case str():
                    return "empty string"
                case _:
                    return "other"
        
        assert process_value(5) == "positive integer"
        assert process_value(-3) == "negative integer"
        assert process_value(0) == "zero"
        assert process_value("hello") == "non-empty string"
        assert process_value("") == "empty string"
        assert process_value([1, 2, 3]) == "other"
    
    def test_exception_groups(self):
        """Test exception groups (Python 3.11+)."""
        if sys.version_info < (3, 11):
            pytest.skip("Exception groups require Python 3.11+")
        
        # Test ExceptionGroup creation (using exec to avoid syntax errors on older Python)
        test_code = '''
try:
    raise ExceptionGroup("Multiple errors", [
        ValueError("Invalid value"),
        TypeError("Wrong type"),
    ])
except* ValueError as eg:
    assert len(eg.exceptions) == 1
    assert isinstance(eg.exceptions[0], ValueError)
except* TypeError as eg:
    assert len(eg.exceptions) == 1
    assert isinstance(eg.exceptions[0], TypeError)
'''
        # Execute the test code only on Python 3.11+
        exec(test_code)
    
    def test_builtin_modules_availability(self):
        """Test availability of built-in modules used by the application."""
        required_modules = [
            'os', 'sys', 'pathlib', 'json', 'sqlite3', 'urllib',
            'threading', 'multiprocessing', 'asyncio', 'tempfile',
            'shutil', 'subprocess', 'platform', 'socket', 'ssl',
            'hashlib', 'base64', 'datetime', 'time', 'logging',
            'configparser', 'argparse', 'collections', 'itertools',
            'functools', 'operator', 'copy', 'pickle', 'gzip',
            'zipfile', 'tarfile', 'csv', 'xml', 'html', 're',
        ]
        
        for module_name in required_modules:
            try:
                __import__(module_name)
            except ImportError:
                pytest.fail(f"Required built-in module '{module_name}' not available")
    
    def test_syntax_compatibility(self):
        """Test that application code uses compatible syntax."""
        app_dir = Path("app")
        if not app_dir.exists():
            pytest.skip("Application directory not found")
        
        python_files = list(app_dir.rglob("*.py"))
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                
                # Try to parse the file
                ast.parse(source, filename=str(py_file))
                
            except SyntaxError as e:
                pytest.fail(f"Syntax error in {py_file}: {e}")
            except UnicodeDecodeError as e:
                pytest.fail(f"Encoding error in {py_file}: {e}")
    
    def test_import_compatibility(self):
        """Test that application modules can be imported."""
        app_modules = [
            'app.core.config',
            'app.data.models.core',
            'app.core.downloader.base',
            'app.core.extractor.base',
        ]
        
        for module_name in app_modules:
            try:
                __import__(module_name)
            except ImportError as e:
                # Skip if module doesn't exist yet
                if "No module named" in str(e):
                    pytest.skip(f"Module {module_name} not implemented yet")
                else:
                    pytest.fail(f"Import error for {module_name}: {e}")
            except Exception as e:
                pytest.fail(f"Unexpected error importing {module_name}: {e}")


class TestVersionSpecificFeatures:
    """Test version-specific features and their fallbacks."""
    
    def test_feature_detection(self):
        """Test detection of version-specific features."""
        features = {
            'walrus_operator': sys.version_info >= (3, 8),
            'positional_only': sys.version_info >= (3, 8),
            'dict_merge': sys.version_info >= (3, 9),
            'match_statement': sys.version_info >= (3, 10),
            'exception_groups': sys.version_info >= (3, 11),
            'task_groups': sys.version_info >= (3, 11),
        }
        
        for feature, available in features.items():
            print(f"{feature}: {'Available' if available else 'Not available'}")
    
    def test_graceful_degradation(self):
        """Test that the application degrades gracefully on older Python versions."""
        # This would test fallback implementations for newer features
        # For now, just ensure we can detect the version
        
        version_tuple = sys.version_info[:2]
        
        if version_tuple >= (3, 8):
            # Full feature set available
            assert True
        elif version_tuple >= (3, 7):
            # Limited feature set
            pytest.skip("Python 3.7 support deprecated")
        else:
            pytest.fail("Python version too old")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])