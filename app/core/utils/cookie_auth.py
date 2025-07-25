"""
Cookie authentication system for accessing private content.
Handles cookie management, authentication, and session persistence.
"""
import json
import time
from typing import Dict, List, Optional, Any
import aiohttp
from pathlib import Path
from urllib.parse import urlparse


class CookieAuthManager:
    """
    Manager for cookie-based authentication across platforms.
    Handles cookie storage, session management, and authentication verification.
    """
    
    def __init__(self, config_dir: str = ".config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.cookie_files = {
            'twitter': self.config_dir / 'twitter_cookies.json',
            'pixiv': self.config_dir / 'pixiv_cookies.json',
            'fc2': self.config_dir / 'fc2_cookies.json',
            'tumblr': self.config_dir / 'tumblr_cookies.json',
            'weibo': self.config_dir / 'weibo_cookies.json'
        }
        
        self.sessions = {}  # Platform -> session data
        self.load_all_cookies()
    
    def load_all_cookies(self) -> None:
        """Load all saved cookies from files"""
        for platform, cookie_file in self.cookie_files.items():
            self.sessions[platform] = self.load_cookies_from_file(cookie_file)
    
    def load_cookies_from_file(self, cookie_file: Path) -> Dict[str, Any]:
        """Load cookies from a specific file"""
        if cookie_file.exists():
            try:
                with open(cookie_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def save_cookies_to_file(self, platform: str, cookies: Dict[str, Any]) -> None:
        """Save cookies to a specific platform file"""
        cookie_file = self.cookie_files.get(platform)
        if cookie_file:
            try:
                cookies['timestamp'] = time.time()
                with open(cookie_file, 'w', encoding='utf-8') as f:
                    json.dump(cookies, f, indent=2, ensure_ascii=False)
                self.sessions[platform] = cookies
            except IOError:
                pass  # Ignore save errors
    
    def import_cookies_from_browser(self, platform: str, browser: str = 'chrome') -> bool:
        """Import cookies from browser (placeholder implementation)"""
        # In a real implementation, this would:
        # 1. Access browser cookie database
        # 2. Extract relevant cookies for the platform
        # 3. Convert to our format
        # 4. Save to our cookie files
        
        # Simulated browser cookie import
        if platform == 'twitter':
            browser_cookies = {
                'auth_token': 'imported_auth_token',
                'ct0': 'imported_csrf_token',
                'twid': 'imported_user_id',
                'source': f'{browser}_import'
            }
        elif platform == 'pixiv':
            browser_cookies = {
                'PHPSESSID': 'imported_session_id',
                'device_token': 'imported_device_token',
                'login_ever': '1',
                'source': f'{browser}_import'
            }
        else:
            return False
        
        self.save_cookies_to_file(platform, browser_cookies)
        return True
    
    def export_cookies_to_netscape(self, platform: str, output_file: str) -> bool:
        """Export cookies to Netscape format for external tools"""
        cookies = self.sessions.get(platform, {})
        if not cookies:
            return False
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("# Netscape HTTP Cookie File\n")
                f.write("# This is a generated file! Do not edit.\n\n")
                
                domain = self._get_platform_domain(platform)
                for name, value in cookies.items():
                    if name not in ['timestamp', 'source']:
                        # Format: domain, domain_flag, path, secure, expiration, name, value
                        f.write(f"{domain}\tTRUE\t/\tTRUE\t{int(time.time()) + 86400}\t{name}\t{value}\n")
            
            return True
        except IOError:
            return False
    
    def _get_platform_domain(self, platform: str) -> str:
        """Get the main domain for a platform"""
        domains = {
            'twitter': '.twitter.com',
            'pixiv': '.pixiv.net',
            'fc2': '.fc2.com',
            'tumblr': '.tumblr.com',
            'weibo': '.weibo.com'
        }
        return domains.get(platform, '.example.com')
    
    async def apply_cookies_to_session(self, session: aiohttp.ClientSession, platform: str) -> bool:
        """Apply saved cookies to an aiohttp session"""
        cookies = self.sessions.get(platform, {})
        if not cookies:
            return False
        
        # Apply cookies to session
        for name, value in cookies.items():
            if name not in ['timestamp', 'source']:
                session.cookie_jar.update_cookies({name: value})
        
        # Set platform-specific headers
        self._set_platform_headers(session, platform, cookies)
        return True
    
    def _set_platform_headers(self, session: aiohttp.ClientSession, platform: str, cookies: Dict[str, Any]) -> None:
        """Set platform-specific authentication headers"""
        if platform == 'twitter':
            if 'ct0' in cookies:
                session.headers.update({
                    'X-CSRF-Token': cookies['ct0'],
                    'Authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA'
                })
        elif platform == 'pixiv':
            session.headers.update({
                'Referer': 'https://www.pixiv.net/',
                'X-Requested-With': 'XMLHttpRequest'
            })
        elif platform == 'fc2':
            session.headers.update({
                'Referer': 'https://video.fc2.com/',
                'Accept-Language': 'ja-JP,ja;q=0.9'
            })
    
    def is_authenticated(self, platform: str) -> bool:
        """Check if we have valid authentication for a platform"""
        cookies = self.sessions.get(platform, {})
        if not cookies:
            return False
        
        # Check if cookies are not too old (24 hours)
        timestamp = cookies.get('timestamp', 0)
        if time.time() - timestamp > 86400:
            return False
        
        # Platform-specific authentication checks
        if platform == 'twitter':
            return 'auth_token' in cookies and 'ct0' in cookies
        elif platform == 'pixiv':
            return 'PHPSESSID' in cookies
        elif platform == 'fc2':
            return 'FC2_MEMBER_ID' in cookies
        elif platform == 'tumblr':
            return 'logged_in' in cookies
        elif platform == 'weibo':
            return 'SUB' in cookies
        
        return False
    
    def get_authentication_status(self, platform: str) -> Dict[str, Any]:
        """Get detailed authentication status for a platform"""
        cookies = self.sessions.get(platform, {})
        
        return {
            'platform': platform,
            'authenticated': self.is_authenticated(platform),
            'cookie_count': len([k for k in cookies.keys() if k not in ['timestamp', 'source']]),
            'last_updated': cookies.get('timestamp'),
            'source': cookies.get('source', 'unknown'),
            'expires_in': max(0, 86400 - (time.time() - cookies.get('timestamp', 0))) if cookies.get('timestamp') else 0
        }
    
    def clear_cookies(self, platform: str) -> None:
        """Clear cookies for a specific platform"""
        if platform in self.sessions:
            self.sessions[platform] = {}
        
        cookie_file = self.cookie_files.get(platform)
        if cookie_file and cookie_file.exists():
            cookie_file.unlink()
    
    def clear_all_cookies(self) -> None:
        """Clear all saved cookies"""
        for platform in self.sessions:
            self.clear_cookies(platform)
    
    async def verify_authentication(self, session: aiohttp.ClientSession, platform: str) -> bool:
        """Verify that authentication is working by making a test request"""
        # Apply cookies first
        if not await self.apply_cookies_to_session(session, platform):
            return False
        
        # Platform-specific verification endpoints
        verification_urls = {
            'twitter': 'https://api.twitter.com/1.1/account/verify_credentials.json',
            'pixiv': 'https://www.pixiv.net/ajax/user/self',
            'fc2': 'https://video.fc2.com/api/v1/user/me',
            'tumblr': 'https://www.tumblr.com/api/v2/user/info',
            'weibo': 'https://weibo.com/ajax/profile/info'
        }
        
        verification_url = verification_urls.get(platform)
        if not verification_url:
            return False
        
        try:
            async with session.get(verification_url) as response:
                if response.status == 200:
                    # Update timestamp on successful verification
                    if platform in self.sessions:
                        self.sessions[platform]['timestamp'] = time.time()
                        self.save_cookies_to_file(platform, self.sessions[platform])
                    return True
                else:
                    return False
        except Exception:
            return False
    
    def get_cookie_instructions(self, platform: str) -> Dict[str, Any]:
        """Get instructions for manually obtaining cookies"""
        instructions = {
            'twitter': {
                'steps': [
                    '1. Open Twitter/X in your browser and log in',
                    '2. Open Developer Tools (F12)',
                    '3. Go to Application/Storage tab',
                    '4. Find Cookies for twitter.com',
                    '5. Copy auth_token and ct0 values',
                    '6. Import using the cookie import feature'
                ],
                'required_cookies': ['auth_token', 'ct0', 'twid'],
                'optional_cookies': ['personalization_id', 'guest_id']
            },
            'pixiv': {
                'steps': [
                    '1. Open Pixiv in your browser and log in',
                    '2. Open Developer Tools (F12)',
                    '3. Go to Application/Storage tab',
                    '4. Find Cookies for pixiv.net',
                    '5. Copy PHPSESSID and device_token values',
                    '6. Import using the cookie import feature'
                ],
                'required_cookies': ['PHPSESSID', 'device_token'],
                'optional_cookies': ['login_ever', 'p_ab_id']
            },
            'fc2': {
                'steps': [
                    '1. Open FC2 Video in your browser and log in',
                    '2. Open Developer Tools (F12)',
                    '3. Go to Application/Storage tab',
                    '4. Find Cookies for fc2.com',
                    '5. Copy FC2_MEMBER_ID and FC2_SESSION values',
                    '6. Import using the cookie import feature'
                ],
                'required_cookies': ['FC2_MEMBER_ID', 'FC2_SESSION'],
                'optional_cookies': ['FC2_PREMIUM']
            }
        }
        
        return instructions.get(platform, {
            'steps': ['Platform-specific instructions not available'],
            'required_cookies': [],
            'optional_cookies': []
        })


# Global instance for easy access
cookie_auth = CookieAuthManager()