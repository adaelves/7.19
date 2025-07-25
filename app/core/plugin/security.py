"""
Security manager for plugin isolation and safety.
"""
import ast
import logging
import sys
import threading
import time
from typing import Set, List, Dict, Any, Optional, Callable
from pathlib import Path
import importlib.util
from dataclasses import dataclass
from enum import Enum
import hashlib
import json


class SecurityLevel(Enum):
    """Security level enumeration"""
    STRICT = "strict"      # Maximum security, minimal permissions
    MODERATE = "moderate"  # Balanced security and functionality
    PERMISSIVE = "permissive"  # Minimal security checks


class ViolationType(Enum):
    """Security violation type"""
    DANGEROUS_IMPORT = "dangerous_import"
    DANGEROUS_FUNCTION = "dangerous_function"
    FILE_ACCESS = "file_access"
    NETWORK_ACCESS = "network_access"
    SYSTEM_ACCESS = "system_access"
    EXECUTION = "execution"


@dataclass
class SecurityViolation:
    """Security violation information"""
    violation_type: ViolationType
    description: str
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    severity: str = "medium"  # low, medium, high, critical


@dataclass
class SecurityPolicy:
    """Security policy configuration"""
    level: SecurityLevel = SecurityLevel.MODERATE
    allowed_imports: Set[str] = None
    blocked_imports: Set[str] = None
    allowed_functions: Set[str] = None
    blocked_functions: Set[str] = None
    allow_file_access: bool = False
    allow_network_access: bool = True
    allow_system_calls: bool = False
    max_execution_time: float = 30.0  # seconds
    max_memory_usage: int = 100 * 1024 * 1024  # 100MB
    
    def __post_init__(self):
        if self.allowed_imports is None:
            self.allowed_imports = self._get_default_allowed_imports()
        if self.blocked_imports is None:
            self.blocked_imports = self._get_default_blocked_imports()
        if self.allowed_functions is None:
            self.allowed_functions = self._get_default_allowed_functions()
        if self.blocked_functions is None:
            self.blocked_functions = self._get_default_blocked_functions()
    
    def _get_default_allowed_imports(self) -> Set[str]:
        """Get default allowed imports based on security level"""
        base_imports = {
            'json', 're', 'datetime', 'time', 'base64', 'hashlib', 'hmac',
            'uuid', 'typing', 'dataclasses', 'abc', 'asyncio', 'enum',
            'urllib', 'urllib.parse', 'urllib.request', 'urllib.error',
            'requests', 'aiohttp', 'bs4', 'lxml', 'html.parser',
            'app.core.extractor.base', 'app.data.models.core'
        }
        
        if self.level == SecurityLevel.PERMISSIVE:
            base_imports.update({
                'os.path', 'pathlib', 'tempfile', 'shutil'
            })
        elif self.level == SecurityLevel.MODERATE:
            base_imports.update({
                'os.path', 'pathlib'
            })
        
        return base_imports
    
    def _get_default_blocked_imports(self) -> Set[str]:
        """Get default blocked imports"""
        return {
            'os', 'sys', 'subprocess', 'importlib', 'exec', 'eval',
            'compile', '__import__', 'globals', 'locals', 'vars',
            'socket', 'threading', 'multiprocessing', 'ctypes',
            'pickle', 'marshal', 'shelve', 'dbm'
        }
    
    def _get_default_allowed_functions(self) -> Set[str]:
        """Get default allowed functions"""
        return {
            'len', 'str', 'int', 'float', 'bool', 'list', 'dict', 'tuple',
            'set', 'frozenset', 'range', 'enumerate', 'zip', 'map', 'filter',
            'sorted', 'reversed', 'sum', 'min', 'max', 'abs', 'round',
            'print', 'isinstance', 'issubclass', 'hasattr', 'getattr',
            'setattr', 'delattr', 'type', 'id', 'hash'
        }
    
    def _get_default_blocked_functions(self) -> Set[str]:
        """Get default blocked functions"""
        return {
            'exec', 'eval', 'compile', '__import__', 'open', 'file',
            'input', 'raw_input', 'reload', 'exit', 'quit'
        }


class PluginSecurityManager:
    """
    Security manager for plugin isolation and safety checks.
    """
    
    def __init__(self, policy: Optional[SecurityPolicy] = None):
        self.logger = logging.getLogger(__name__)
        self.policy = policy or SecurityPolicy()
        
        # Security state
        self._plugin_checksums: Dict[str, str] = {}
        self._violation_history: Dict[str, List[SecurityViolation]] = {}
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Load security configuration
        self._load_security_config()
    
    def _load_security_config(self):
        """Load security configuration from file"""
        try:
            config_path = Path(__file__).parent.parent.parent.parent / 'config' / 'security.json'
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    self._update_policy_from_config(config)
        except Exception as e:
            self.logger.warning(f"Failed to load security config: {e}")
    
    def _update_policy_from_config(self, config: Dict[str, Any]):
        """Update security policy from configuration"""
        if 'level' in config:
            self.policy.level = SecurityLevel(config['level'])
        
        if 'allowed_imports' in config:
            self.policy.allowed_imports.update(config['allowed_imports'])
        
        if 'blocked_imports' in config:
            self.policy.blocked_imports.update(config['blocked_imports'])
        
        if 'max_execution_time' in config:
            self.policy.max_execution_time = config['max_execution_time']
        
        if 'max_memory_usage' in config:
            self.policy.max_memory_usage = config['max_memory_usage']
    
    def validate_plugin_file(self, plugin_path: Path) -> List[SecurityViolation]:
        """
        Validate a plugin file for security violations.
        
        Args:
            plugin_path: Path to plugin file
            
        Returns:
            List of security violations found
        """
        with self._lock:
            violations = []
            
            try:
                # Read and parse the file
                content = plugin_path.read_text(encoding='utf-8')
                tree = ast.parse(content, filename=str(plugin_path))
                
                # Calculate checksum
                checksum = hashlib.sha256(content.encode()).hexdigest()
                plugin_name = plugin_path.stem
                
                # Check if file has been modified
                if plugin_name in self._plugin_checksums:
                    if self._plugin_checksums[plugin_name] != checksum:
                        self.logger.info(f"Plugin {plugin_name} has been modified")
                
                self._plugin_checksums[plugin_name] = checksum
                
                # Perform AST-based security analysis
                violations.extend(self._analyze_ast(tree, content))
                
                # Store violations
                self._violation_history[plugin_name] = violations
                
                return violations
                
            except SyntaxError as e:
                violations.append(SecurityViolation(
                    violation_type=ViolationType.EXECUTION,
                    description=f"Syntax error in plugin: {e}",
                    line_number=e.lineno,
                    severity="high"
                ))
                return violations
                
            except Exception as e:
                self.logger.error(f"Error validating plugin {plugin_path}: {e}")
                violations.append(SecurityViolation(
                    violation_type=ViolationType.EXECUTION,
                    description=f"Validation error: {e}",
                    severity="medium"
                ))
                return violations
    
    def is_plugin_safe(self, plugin_path: Path) -> bool:
        """
        Check if a plugin is safe to load.
        
        Args:
            plugin_path: Path to plugin file
            
        Returns:
            True if plugin is safe, False otherwise
        """
        violations = self.validate_plugin_file(plugin_path)
        
        # Check for critical violations
        critical_violations = [v for v in violations if v.severity == "critical"]
        if critical_violations:
            return False
        
        # Check for high severity violations in strict mode
        if self.policy.level == SecurityLevel.STRICT:
            high_violations = [v for v in violations if v.severity == "high"]
            if high_violations:
                return False
        
        return True
    
    def create_secure_environment(self, plugin_name: str) -> Dict[str, Any]:
        """
        Create a secure execution environment for a plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Dictionary containing secure globals
        """
        # Create restricted builtins
        safe_builtins = {}
        
        # Add allowed built-in functions
        for func_name in self.policy.allowed_functions:
            if hasattr(__builtins__, func_name):
                safe_builtins[func_name] = getattr(__builtins__, func_name)
        
        # Create secure globals
        secure_globals = {
            '__builtins__': safe_builtins,
            '__name__': f'plugin_{plugin_name}',
            '__file__': f'<plugin:{plugin_name}>',
        }
        
        return secure_globals
    
    def monitor_plugin_execution(self, plugin_name: str, 
                               execution_func: Callable) -> Any:
        """
        Monitor plugin execution for security violations.
        
        Args:
            plugin_name: Name of the plugin
            execution_func: Function to execute
            
        Returns:
            Result of execution
            
        Raises:
            SecurityError: If security violation detected
        """
        start_time = time.time()
        
        try:
            # Execute with timeout
            result = self._execute_with_timeout(
                execution_func, 
                self.policy.max_execution_time
            )
            
            execution_time = time.time() - start_time
            self.logger.debug(f"Plugin {plugin_name} executed in {execution_time:.2f}s")
            
            return result
            
        except TimeoutError:
            violation = SecurityViolation(
                violation_type=ViolationType.EXECUTION,
                description=f"Plugin execution timeout ({self.policy.max_execution_time}s)",
                severity="high"
            )
            self._record_violation(plugin_name, violation)
            raise SecurityError(f"Plugin {plugin_name} execution timeout")
        
        except Exception as e:
            violation = SecurityViolation(
                violation_type=ViolationType.EXECUTION,
                description=f"Plugin execution error: {e}",
                severity="medium"
            )
            self._record_violation(plugin_name, violation)
            raise
    
    def get_plugin_violations(self, plugin_name: str) -> List[SecurityViolation]:
        """
        Get security violations for a plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            List of security violations
        """
        with self._lock:
            return self._violation_history.get(plugin_name, [])
    
    def get_all_violations(self) -> Dict[str, List[SecurityViolation]]:
        """
        Get all security violations.
        
        Returns:
            Dictionary mapping plugin names to violation lists
        """
        with self._lock:
            return self._violation_history.copy()
    
    def clear_violations(self, plugin_name: Optional[str] = None):
        """
        Clear security violations.
        
        Args:
            plugin_name: Name of plugin to clear violations for, or None for all
        """
        with self._lock:
            if plugin_name:
                self._violation_history.pop(plugin_name, None)
            else:
                self._violation_history.clear()
    
    def update_policy(self, policy: SecurityPolicy):
        """
        Update security policy.
        
        Args:
            policy: New security policy
        """
        with self._lock:
            self.policy = policy
            self.logger.info(f"Security policy updated to {policy.level.value}")
    
    def _analyze_ast(self, tree: ast.AST, content: str) -> List[SecurityViolation]:
        """Analyze AST for security violations"""
        violations = []
        lines = content.split('\n')
        
        for node in ast.walk(tree):
            # Check imports
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                violations.extend(self._check_import_node(node, lines))
            
            # Check function calls
            elif isinstance(node, ast.Call):
                violations.extend(self._check_call_node(node, lines))
            
            # Check attribute access
            elif isinstance(node, ast.Attribute):
                violations.extend(self._check_attribute_node(node, lines))
        
        return violations
    
    def _check_import_node(self, node: ast.AST, lines: List[str]) -> List[SecurityViolation]:
        """Check import node for violations"""
        violations = []
        
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name
                if self._is_blocked_import(module_name):
                    violations.append(SecurityViolation(
                        violation_type=ViolationType.DANGEROUS_IMPORT,
                        description=f"Blocked import: {module_name}",
                        line_number=node.lineno,
                        code_snippet=lines[node.lineno - 1] if node.lineno <= len(lines) else None,
                        severity="high"
                    ))
        
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module or ''
            if self._is_blocked_import(module_name):
                violations.append(SecurityViolation(
                    violation_type=ViolationType.DANGEROUS_IMPORT,
                    description=f"Blocked import from: {module_name}",
                    line_number=node.lineno,
                    code_snippet=lines[node.lineno - 1] if node.lineno <= len(lines) else None,
                    severity="high"
                ))
        
        return violations
    
    def _check_call_node(self, node: ast.Call, lines: List[str]) -> List[SecurityViolation]:
        """Check function call node for violations"""
        violations = []
        
        # Get function name
        func_name = None
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        
        if func_name and func_name in self.policy.blocked_functions:
            violations.append(SecurityViolation(
                violation_type=ViolationType.DANGEROUS_FUNCTION,
                description=f"Blocked function call: {func_name}",
                line_number=node.lineno,
                code_snippet=lines[node.lineno - 1] if node.lineno <= len(lines) else None,
                severity="high"
            ))
        
        return violations
    
    def _check_attribute_node(self, node: ast.Attribute, lines: List[str]) -> List[SecurityViolation]:
        """Check attribute access node for violations"""
        violations = []
        
        # Check for dangerous attribute access
        dangerous_attrs = ['__import__', '__builtins__', '__globals__', '__locals__']
        
        if node.attr in dangerous_attrs:
            violations.append(SecurityViolation(
                violation_type=ViolationType.SYSTEM_ACCESS,
                description=f"Dangerous attribute access: {node.attr}",
                line_number=node.lineno,
                code_snippet=lines[node.lineno - 1] if node.lineno <= len(lines) else None,
                severity="critical"
            ))
        
        return violations
    
    def _is_blocked_import(self, module_name: str) -> bool:
        """Check if import is blocked"""
        # Check exact matches
        if module_name in self.policy.blocked_imports:
            return True
        
        # Check if it's not in allowed imports (for strict mode)
        if self.policy.level == SecurityLevel.STRICT:
            if module_name not in self.policy.allowed_imports:
                # Check for partial matches
                allowed = any(module_name.startswith(allowed + '.') 
                            for allowed in self.policy.allowed_imports)
                if not allowed:
                    return True
        
        return False
    
    def _execute_with_timeout(self, func: Callable, timeout: float) -> Any:
        """Execute function with timeout"""
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Execution timeout")
        
        # Set up timeout (Unix only)
        if hasattr(signal, 'SIGALRM'):
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(timeout))
            
            try:
                result = func()
                signal.alarm(0)  # Cancel alarm
                return result
            finally:
                signal.signal(signal.SIGALRM, old_handler)
        else:
            # Fallback for Windows - use threading
            import threading
            result = [None]
            exception = [None]
            
            def target():
                try:
                    result[0] = func()
                except Exception as e:
                    exception[0] = e
            
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout)
            
            if thread.is_alive():
                raise TimeoutError("Execution timeout")
            
            if exception[0]:
                raise exception[0]
            
            return result[0]
    
    def _record_violation(self, plugin_name: str, violation: SecurityViolation):
        """Record a security violation"""
        with self._lock:
            if plugin_name not in self._violation_history:
                self._violation_history[plugin_name] = []
            
            self._violation_history[plugin_name].append(violation)
            self.logger.warning(f"Security violation in {plugin_name}: {violation.description}")


class SecurityError(Exception):
    """Security-related exception"""
    pass