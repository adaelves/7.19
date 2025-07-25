"""
Cookie management system for video downloader.
Handles cookie import/export and browser cookie extraction.
"""
import json
import sqlite3
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import base64
import platform
from urllib.parse import urlparse


class CookieManager:
    """Cookie management for web scraping and downloads"""
    
    # Browser cookie database paths
    BROWSER_PATHS = {
        'chrome': {
            'windows': os.path.expanduser('~\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Cookies'),
            'darwin': os.path.expanduser('~/Library/Application Support/Google/Chrome/Default/Cookies'),
            'linux': os.path.expanduser('~/.config/google-chrome/Default/Cookies')
        },
        'firefox': {
            'windows': os.path.expanduser('~\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles'),
            'darwin': os.path.expanduser('~/Library/Application Support/Firefox/Profiles'),
            'linux': os.path.expanduser('~/.mozilla/firefox')
        },
        'edge': {
            'windows': os.path.expanduser('~\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\Cookies'),
            'darwin': os.path.expanduser('~/Library/Application Support/Microsoft Edge/Default/Cookies'),
            'linux': os.path.expanduser('~/.config/microsoft-edge/Default/Cookies')
        },
        'safari': {
            'darwin': os.path.expanduser('~/Library/Cookies/Cookies.binarycookies')
        }
    }
    
    def __init__(self, cookie_dir: Optional[str] = None):
        """
        Initialize cookie manager.
        
        Args:
            cookie_dir: Directory to store cookie files
        """
        self.cookie_dir = cookie_dir or os.path.expanduser('~/.video_downloader/cookies')
        self._ensure_cookie_dir()
        self.cookies: Dict[str, List[Dict[str, Any]]] = {}
    
    def _ensure_cookie_dir(self):
        """Ensure cookie directory exists"""
        os.makedirs(self.cookie_dir, exist_ok=True)
    
    def import_cookies_from_browser(self, browser: str, profile: Optional[str] = None) -> bool:
        """
        Import cookies from browser.
        
        Args:
            browser: Browser name ('chrome', 'firefox', 'edge', 'safari')
            profile: Browser profile name (for Firefox)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            system = platform.system().lower()
            if system == 'darwin':
                system = 'darwin'
            elif system == 'windows':
                system = 'windows'
            else:
                system = 'linux'
            
            browser_paths = self.BROWSER_PATHS.get(browser, {})
            cookie_path = browser_paths.get(system)
            
            if not cookie_path:
                print(f"Browser {browser} not supported on {system}")
                return False
            
            if browser == 'firefox':
                return self._import_firefox_cookies(cookie_path, profile)
            elif browser == 'safari':
                return self._import_safari_cookies(cookie_path)
            else:
                return self._import_chromium_cookies(cookie_path)
                
        except Exception as e:
            print(f"Error importing cookies from {browser}: {e}")
            return False
    
    def _import_chromium_cookies(self, cookie_db_path: str) -> bool:
        """Import cookies from Chromium-based browsers"""
        if not os.path.exists(cookie_db_path):
            print(f"Cookie database not found: {cookie_db_path}")
            return False
        
        try:
            # Create temporary copy of the database
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
                shutil.copy2(cookie_db_path, temp_file.name)
                temp_db_path = temp_file.name
            
            # Connect to the database
            conn = sqlite3.connect(temp_db_path)
            cursor = conn.cursor()
            
            # Query cookies
            cursor.execute("""
                SELECT host_key, name, value, path, expires_utc, is_secure, is_httponly, samesite
                FROM cookies
                WHERE expires_utc > ? OR expires_utc = 0
            """, (int(datetime.now().timestamp() * 1000000),))
            
            cookies_by_domain = {}
            
            for row in cursor.fetchall():
                host_key, name, value, path, expires_utc, is_secure, is_httponly, samesite = row
                
                # Convert Chrome timestamp to Unix timestamp
                if expires_utc > 0:
                    # Chrome uses microseconds since 1601-01-01
                    expires = (expires_utc / 1000000) - 11644473600
                else:
                    expires = 0
                
                cookie = {
                    'name': name,
                    'value': value,
                    'domain': host_key,
                    'path': path,
                    'expires': expires,
                    'secure': bool(is_secure),
                    'httpOnly': bool(is_httponly),
                    'sameSite': samesite or 'no_restriction'
                }
                
                domain = host_key.lstrip('.')
                if domain not in cookies_by_domain:
                    cookies_by_domain[domain] = []
                cookies_by_domain[domain].append(cookie)
            
            conn.close()
            os.unlink(temp_db_path)
            
            # Store cookies
            self.cookies.update(cookies_by_domain)
            
            print(f"Imported cookies for {len(cookies_by_domain)} domains")
            return True
            
        except Exception as e:
            print(f"Error importing Chromium cookies: {e}")
            return False
    
    def _import_firefox_cookies(self, profile_dir: str, profile_name: Optional[str] = None) -> bool:
        """Import cookies from Firefox"""
        try:
            # Find Firefox profile
            if profile_name:
                cookie_db_path = os.path.join(profile_dir, profile_name, 'cookies.sqlite')
            else:
                # Find default profile
                profiles = [d for d in os.listdir(profile_dir) if d.endswith('.default') or d.endswith('.default-release')]
                if not profiles:
                    print("No Firefox profile found")
                    return False
                cookie_db_path = os.path.join(profile_dir, profiles[0], 'cookies.sqlite')
            
            if not os.path.exists(cookie_db_path):
                print(f"Firefox cookie database not found: {cookie_db_path}")
                return False
            
            # Create temporary copy
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
                shutil.copy2(cookie_db_path, temp_file.name)
                temp_db_path = temp_file.name
            
            conn = sqlite3.connect(temp_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT host, name, value, path, expiry, isSecure, isHttpOnly, sameSite
                FROM moz_cookies
                WHERE expiry > ? OR expiry = 0
            """, (int(datetime.now().timestamp()),))
            
            cookies_by_domain = {}
            
            for row in cursor.fetchall():
                host, name, value, path, expiry, is_secure, is_httponly, same_site = row
                
                cookie = {
                    'name': name,
                    'value': value,
                    'domain': host,
                    'path': path,
                    'expires': expiry or 0,
                    'secure': bool(is_secure),
                    'httpOnly': bool(is_httponly),
                    'sameSite': same_site or 'no_restriction'
                }
                
                domain = host.lstrip('.')
                if domain not in cookies_by_domain:
                    cookies_by_domain[domain] = []
                cookies_by_domain[domain].append(cookie)
            
            conn.close()
            os.unlink(temp_db_path)
            
            self.cookies.update(cookies_by_domain)
            
            print(f"Imported Firefox cookies for {len(cookies_by_domain)} domains")
            return True
            
        except Exception as e:
            print(f"Error importing Firefox cookies: {e}")
            return False
    
    def _import_safari_cookies(self, cookie_path: str) -> bool:
        """Import cookies from Safari (macOS only)"""
        # Safari uses a binary format that's more complex to parse
        # For now, we'll return False and suggest manual export
        print("Safari cookie import not yet implemented. Please export cookies manually.")
        return False
    
    def import_cookies_from_file(self, file_path: str, format_type: str = 'netscape') -> bool:
        """
        Import cookies from file.
        
        Args:
            file_path: Path to cookie file
            format_type: Format type ('netscape', 'json', 'mozilla')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                print(f"Cookie file not found: {file_path}")
                return False
            
            if format_type == 'json':
                return self._import_json_cookies(file_path)
            elif format_type == 'netscape':
                return self._import_netscape_cookies(file_path)
            else:
                print(f"Unsupported cookie format: {format_type}")
                return False
                
        except Exception as e:
            print(f"Error importing cookies from file: {e}")
            return False
    
    def _import_json_cookies(self, file_path: str) -> bool:
        """Import cookies from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                # Array of cookies
                cookies_by_domain = {}
                for cookie in data:
                    domain = cookie.get('domain', '').lstrip('.')
                    if domain not in cookies_by_domain:
                        cookies_by_domain[domain] = []
                    cookies_by_domain[domain].append(cookie)
                
                self.cookies.update(cookies_by_domain)
            
            elif isinstance(data, dict):
                # Domain-organized cookies
                self.cookies.update(data)
            
            return True
            
        except Exception as e:
            print(f"Error importing JSON cookies: {e}")
            return False
    
    def _import_netscape_cookies(self, file_path: str) -> bool:
        """Import cookies from Netscape format file"""
        try:
            cookies_by_domain = {}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split('\t')
                    if len(parts) < 7:
                        continue
                    
                    domain, domain_specified, path, secure, expires, name, value = parts[:7]
                    
                    cookie = {
                        'name': name,
                        'value': value,
                        'domain': domain,
                        'path': path,
                        'expires': int(expires) if expires.isdigit() else 0,
                        'secure': secure.upper() == 'TRUE',
                        'httpOnly': False,  # Not specified in Netscape format
                        'sameSite': 'no_restriction'
                    }
                    
                    domain_key = domain.lstrip('.')
                    if domain_key not in cookies_by_domain:
                        cookies_by_domain[domain_key] = []
                    cookies_by_domain[domain_key].append(cookie)
            
            self.cookies.update(cookies_by_domain)
            return True
            
        except Exception as e:
            print(f"Error importing Netscape cookies: {e}")
            return False
    
    def export_cookies_to_file(self, file_path: str, format_type: str = 'json', 
                              domains: Optional[List[str]] = None) -> bool:
        """
        Export cookies to file.
        
        Args:
            file_path: Output file path
            format_type: Format type ('json', 'netscape')
            domains: List of domains to export (all if None)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cookies_to_export = self.cookies
            
            if domains:
                cookies_to_export = {
                    domain: cookies for domain, cookies in self.cookies.items()
                    if domain in domains
                }
            
            if format_type == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(cookies_to_export, f, indent=2, ensure_ascii=False)
            
            elif format_type == 'netscape':
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("# Netscape HTTP Cookie File\n")
                    f.write("# Generated by Video Downloader\n\n")
                    
                    for domain, domain_cookies in cookies_to_export.items():
                        for cookie in domain_cookies:
                            line = f"{cookie['domain']}\tTRUE\t{cookie['path']}\t"
                            line += f"{'TRUE' if cookie['secure'] else 'FALSE'}\t"
                            line += f"{int(cookie['expires'])}\t"
                            line += f"{cookie['name']}\t{cookie['value']}\n"
                            f.write(line)
            
            else:
                print(f"Unsupported export format: {format_type}")
                return False
            
            print(f"Exported cookies to {file_path}")
            return True
            
        except Exception as e:
            print(f"Error exporting cookies: {e}")
            return False
    
    def get_cookies_for_domain(self, domain: str) -> List[Dict[str, Any]]:
        """
        Get cookies for a specific domain.
        
        Args:
            domain: Domain name
            
        Returns:
            List of cookies for the domain
        """
        # Check exact match first
        if domain in self.cookies:
            return self.cookies[domain]
        
        # Check for parent domains
        domain_parts = domain.split('.')
        for i in range(len(domain_parts)):
            parent_domain = '.'.join(domain_parts[i:])
            if parent_domain in self.cookies:
                return self.cookies[parent_domain]
        
        return []
    
    def get_cookie_header(self, url: str) -> str:
        """
        Get cookie header string for a URL.
        
        Args:
            url: Target URL
            
        Returns:
            Cookie header string
        """
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        path = parsed_url.path or '/'
        is_secure = parsed_url.scheme == 'https'
        
        cookies = self.get_cookies_for_domain(domain)
        valid_cookies = []
        
        current_time = datetime.now().timestamp()
        
        for cookie in cookies:
            # Check expiration
            if cookie['expires'] > 0 and cookie['expires'] < current_time:
                continue
            
            # Check secure flag
            if cookie['secure'] and not is_secure:
                continue
            
            # Check path
            if not path.startswith(cookie['path']):
                continue
            
            valid_cookies.append(f"{cookie['name']}={cookie['value']}")
        
        return '; '.join(valid_cookies)
    
    def add_cookie(self, domain: str, name: str, value: str, **kwargs):
        """
        Add a cookie manually.
        
        Args:
            domain: Cookie domain
            name: Cookie name
            value: Cookie value
            **kwargs: Additional cookie attributes
        """
        cookie = {
            'name': name,
            'value': value,
            'domain': domain,
            'path': kwargs.get('path', '/'),
            'expires': kwargs.get('expires', 0),
            'secure': kwargs.get('secure', False),
            'httpOnly': kwargs.get('httpOnly', False),
            'sameSite': kwargs.get('sameSite', 'no_restriction')
        }
        
        if domain not in self.cookies:
            self.cookies[domain] = []
        
        # Remove existing cookie with same name
        self.cookies[domain] = [c for c in self.cookies[domain] if c['name'] != name]
        
        # Add new cookie
        self.cookies[domain].append(cookie)
    
    def remove_cookie(self, domain: str, name: str) -> bool:
        """
        Remove a specific cookie.
        
        Args:
            domain: Cookie domain
            name: Cookie name
            
        Returns:
            True if cookie was removed, False if not found
        """
        if domain not in self.cookies:
            return False
        
        original_count = len(self.cookies[domain])
        self.cookies[domain] = [c for c in self.cookies[domain] if c['name'] != name]
        
        return len(self.cookies[domain]) < original_count
    
    def clear_cookies(self, domain: Optional[str] = None):
        """
        Clear cookies.
        
        Args:
            domain: Specific domain to clear (all if None)
        """
        if domain:
            if domain in self.cookies:
                del self.cookies[domain]
        else:
            self.cookies.clear()
    
    def get_cookie_summary(self) -> Dict[str, int]:
        """
        Get summary of stored cookies.
        
        Returns:
            Dictionary with domain -> cookie count mapping
        """
        return {domain: len(cookies) for domain, cookies in self.cookies.items()}
    
    def cleanup_expired_cookies(self) -> int:
        """
        Remove expired cookies.
        
        Returns:
            Number of cookies removed
        """
        current_time = datetime.now().timestamp()
        removed_count = 0
        
        for domain in list(self.cookies.keys()):
            original_count = len(self.cookies[domain])
            self.cookies[domain] = [
                cookie for cookie in self.cookies[domain]
                if cookie['expires'] == 0 or cookie['expires'] > current_time
            ]
            removed_count += original_count - len(self.cookies[domain])
            
            # Remove empty domains
            if not self.cookies[domain]:
                del self.cookies[domain]
        
        return removed_count


# Global cookie manager instance
cookie_manager = CookieManager()