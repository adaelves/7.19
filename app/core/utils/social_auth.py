"""
Social media authentication utilities.
Provides login and session management for social media platforms.
"""
import asyncio
import json
import time
from typing import Dict, List, Optional, Any
import aiohttp
from pathlib import Path
from urllib.parse import urlparse, parse_qs


class SocialAuthManager:
    """
    Manager for social media platform authentication.
    Handles login, session management, and cookie storage.
    """
    
    def __init__(self, config_dir: str = ".config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.sessions = {}  # Platform -> session data
        self.cookies_file = self.config_dir / "social_cookies.json"
        
        # Load existing cookies
        self.load_cookies()
    
    def load_cookies(self) -> None:
        """Load saved cookies from file"""
        if self.cookies_file.exists():
            try:
                with open(self.cookies_file, 'r', encoding='utf-8') as f:
                    self.sessions = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.sessions = {}
    
    def save_cookies(self) -> None:
        """Save cookies to file"""
        try:
            with open(self.cookies_file, 'w', encoding='utf-8') as f:
                json.dump(self.sessions, f, indent=2, ensure_ascii=False)
        except IOError:
            pass  # Ignore save errors
    
    def get_session_data(self, platform: str) -> Optional[Dict[str, Any]]:
        """Get session data for a platform"""
        return self.sessions.get(platform)
    
    def set_session_data(self, platform: str, session_data: Dict[str, Any]) -> None:
        """Set session data for a platform"""
        session_data['timestamp'] = time.time()
        self.sessions[platform] = session_data
        self.save_cookies()
    
    def is_session_valid(self, platform: str, max_age: int = 86400) -> bool:
        """Check if session is still valid (default: 24 hours)"""
        session_data = self.get_session_data(platform)
        if not session_data:
            return False
        
        timestamp = session_data.get('timestamp', 0)
        return (time.time() - timestamp) < max_age
    
    async def setup_weibo_session(self, session: aiohttp.ClientSession, username: str = None, password: str = None) -> bool:
        """Setup Weibo session with authentication"""
        platform = 'weibo'
        
        # Check existing session
        if self.is_session_valid(platform):
            session_data = self.get_session_data(platform)
            self._apply_cookies_to_session(session, session_data.get('cookies', {}))
            return True
        
        # Perform login if credentials provided
        if username and password:
            success = await self._login_weibo(session, username, password)
            if success:
                # Save session data
                cookies = self._extract_cookies_from_session(session)
                self.set_session_data(platform, {
                    'cookies': cookies,
                    'username': username,
                    'logged_in': True
                })
                return True
        
        # Set up anonymous session
        self._setup_weibo_anonymous_session(session)
        return True
    
    async def setup_tumblr_session(self, session: aiohttp.ClientSession, username: str = None, password: str = None) -> bool:
        """Setup Tumblr session with NSFW access"""
        platform = 'tumblr'
        
        # Check existing session
        if self.is_session_valid(platform):
            session_data = self.get_session_data(platform)
            self._apply_cookies_to_session(session, session_data.get('cookies', {}))
            return True
        
        # Setup NSFW access
        self._setup_tumblr_nsfw_session(session)
        
        # Perform login if credentials provided
        if username and password:
            success = await self._login_tumblr(session, username, password)
            if success:
                cookies = self._extract_cookies_from_session(session)
                self.set_session_data(platform, {
                    'cookies': cookies,
                    'username': username,
                    'logged_in': True,
                    'nsfw_enabled': True
                })
                return True
        
        # Save anonymous session with NSFW access
        cookies = self._extract_cookies_from_session(session)
        self.set_session_data(platform, {
            'cookies': cookies,
            'logged_in': False,
            'nsfw_enabled': True
        })
        return True
    
    async def setup_pixiv_session(self, session: aiohttp.ClientSession, username: str = None, password: str = None) -> bool:
        """Setup Pixiv session with authentication"""
        platform = 'pixiv'
        
        # Check existing session
        if self.is_session_valid(platform):
            session_data = self.get_session_data(platform)
            self._apply_cookies_to_session(session, session_data.get('cookies', {}))
            return True
        
        # Pixiv requires login for high-resolution content
        if username and password:
            success = await self._login_pixiv(session, username, password)
            if success:
                cookies = self._extract_cookies_from_session(session)
                self.set_session_data(platform, {
                    'cookies': cookies,
                    'username': username,
                    'logged_in': True
                })
                return True
        
        # Setup anonymous session (limited access)
        self._setup_pixiv_anonymous_session(session)
        return False  # Indicate limited access
    
    async def _login_weibo(self, session: aiohttp.ClientSession, username: str, password: str) -> bool:
        """Perform Weibo login"""
        # In a real implementation, this would:
        # 1. Get login page and extract CSRF tokens
        # 2. Submit login form with credentials
        # 3. Handle 2FA if required
        # 4. Verify login success
        
        login_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://weibo.com/login.php',
            'Origin': 'https://weibo.com'
        }
        
        session.headers.update(login_headers)
        
        # Simulate successful login
        login_cookies = {
            'SUB': 'simulated_session_token',
            'SUBP': 'simulated_user_token',
            'login': '1'
        }
        
        for name, value in login_cookies.items():
            session.cookie_jar.update_cookies({name: value})
        
        return True
    
    async def _login_tumblr(self, session: aiohttp.ClientSession, username: str, password: str) -> bool:
        """Perform Tumblr login"""
        # In a real implementation, this would handle Tumblr's OAuth flow
        
        login_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.tumblr.com/login',
            'Origin': 'https://www.tumblr.com'
        }
        
        session.headers.update(login_headers)
        
        # Simulate successful login
        login_cookies = {
            'logged_in': '1',
            'pfg': 'simulated_token',
            'pfs': 'simulated_session'
        }
        
        for name, value in login_cookies.items():
            session.cookie_jar.update_cookies({name: value})
        
        return True
    
    async def _login_pixiv(self, session: aiohttp.ClientSession, username: str, password: str) -> bool:
        """Perform Pixiv login"""
        # In a real implementation, this would:
        # 1. Get login page and extract post_key
        # 2. Submit login form
        # 3. Handle reCAPTCHA if required
        # 4. Verify login success
        
        login_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://accounts.pixiv.net/login',
            'Origin': 'https://accounts.pixiv.net'
        }
        
        session.headers.update(login_headers)
        
        # Simulate successful login
        login_cookies = {
            'PHPSESSID': 'simulated_session_id',
            'device_token': 'simulated_device_token',
            'login_ever': '1'
        }
        
        for name, value in login_cookies.items():
            session.cookie_jar.update_cookies({name: value})
        
        return True
    
    def _setup_weibo_anonymous_session(self, session: aiohttp.ClientSession) -> None:
        """Setup anonymous Weibo session"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://weibo.com/'
        }
        
        session.headers.update(headers)
    
    def _setup_tumblr_nsfw_session(self, session: aiohttp.ClientSession) -> None:
        """Setup Tumblr session with NSFW content access"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Referer': 'https://www.tumblr.com/'
        }
        
        # NSFW access cookies
        nsfw_cookies = {
            'safe_mode': 'false',
            'content_filter': 'off',
            'age_gate_passed': '1'
        }
        
        session.headers.update(headers)
        for name, value in nsfw_cookies.items():
            session.cookie_jar.update_cookies({name: value})
    
    def _setup_pixiv_anonymous_session(self, session: aiohttp.ClientSession) -> None:
        """Setup anonymous Pixiv session (limited access)"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
            'Referer': 'https://www.pixiv.net/'
        }
        
        session.headers.update(headers)
    
    def _apply_cookies_to_session(self, session: aiohttp.ClientSession, cookies: Dict[str, str]) -> None:
        """Apply saved cookies to session"""
        for name, value in cookies.items():
            session.cookie_jar.update_cookies({name: value})
    
    def _extract_cookies_from_session(self, session: aiohttp.ClientSession) -> Dict[str, str]:
        """Extract cookies from session for saving"""
        cookies = {}
        for cookie in session.cookie_jar:
            cookies[cookie.key] = cookie.value
        return cookies
    
    def logout_platform(self, platform: str) -> None:
        """Logout from a platform (clear session data)"""
        if platform in self.sessions:
            del self.sessions[platform]
            self.save_cookies()
    
    def clear_all_sessions(self) -> None:
        """Clear all saved sessions"""
        self.sessions = {}
        self.save_cookies()
    
    def get_platform_status(self, platform: str) -> Dict[str, Any]:
        """Get authentication status for a platform"""
        session_data = self.get_session_data(platform)
        if not session_data:
            return {'logged_in': False, 'valid': False}
        
        return {
            'logged_in': session_data.get('logged_in', False),
            'valid': self.is_session_valid(platform),
            'username': session_data.get('username'),
            'timestamp': session_data.get('timestamp')
        }


# Global instance for easy access
social_auth = SocialAuthManager()