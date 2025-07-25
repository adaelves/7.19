"""
Browser fingerprint spoofing and User-Agent management.
Provides realistic browser fingerprints to avoid detection.
"""
import random
import json
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import platform


class UserAgentManager:
    """Manages browser fingerprints and User-Agent strings"""
    
    # Common browser versions and their market share weights
    BROWSER_DATA = {
        'chrome': {
            'versions': [
                '120.0.0.0', '119.0.0.0', '118.0.0.0', '117.0.0.0', '116.0.0.0',
                '115.0.0.0', '114.0.0.0', '113.0.0.0', '112.0.0.0', '111.0.0.0'
            ],
            'weight': 65,  # Market share percentage
            'template': 'Mozilla/5.0 ({os_string}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36'
        },
        'firefox': {
            'versions': [
                '121.0', '120.0', '119.0', '118.0', '117.0',
                '116.0', '115.0', '114.0', '113.0', '112.0'
            ],
            'weight': 20,
            'template': 'Mozilla/5.0 ({os_string}; rv:{version}) Gecko/20100101 Firefox/{version}'
        },
        'safari': {
            'versions': [
                '17.1', '17.0', '16.6', '16.5', '16.4',
                '16.3', '16.2', '16.1', '16.0', '15.6'
            ],
            'weight': 10,
            'template': 'Mozilla/5.0 ({os_string}) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{version} Safari/605.1.15'
        },
        'edge': {
            'versions': [
                '120.0.0.0', '119.0.0.0', '118.0.0.0', '117.0.0.0', '116.0.0.0',
                '115.0.0.0', '114.0.0.0', '113.0.0.0', '112.0.0.0', '111.0.0.0'
            ],
            'weight': 5,
            'template': 'Mozilla/5.0 ({os_string}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36 Edg/{version}'
        }
    }
    
    # Operating system strings
    OS_STRINGS = {
        'windows': [
            'Windows NT 10.0; Win64; x64',
            'Windows NT 10.0; WOW64',
            'Windows NT 6.3; Win64; x64',
            'Windows NT 6.1; Win64; x64',
            'Windows NT 6.1; WOW64'
        ],
        'macos': [
            'Macintosh; Intel Mac OS X 10_15_7',
            'Macintosh; Intel Mac OS X 10_15_6',
            'Macintosh; Intel Mac OS X 10_14_6',
            'Macintosh; Intel Mac OS X 10_13_6',
            'Macintosh; Intel Mac OS X 11_7_10',
            'Macintosh; Intel Mac OS X 12_7_1'
        ],
        'linux': [
            'X11; Linux x86_64',
            'X11; Ubuntu; Linux x86_64',
            'X11; Linux i686',
            'X11; CrOS x86_64'
        ]
    }
    
    # Mobile User-Agents
    MOBILE_USER_AGENTS = [
        # iPhone
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
        
        # Android Chrome
        'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        'Mozilla/5.0 (Linux; Android 12; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36',
        
        # Android Firefox
        'Mozilla/5.0 (Mobile; rv:121.0) Gecko/121.0 Firefox/121.0',
        'Mozilla/5.0 (Mobile; rv:120.0) Gecko/120.0 Firefox/120.0'
    ]
    
    # Common screen resolutions
    SCREEN_RESOLUTIONS = [
        (1920, 1080), (1366, 768), (1536, 864), (1440, 900),
        (1280, 720), (1600, 900), (2560, 1440), (3840, 2160),
        (1024, 768), (1280, 1024)
    ]
    
    # Browser languages
    LANGUAGES = [
        'en-US,en;q=0.9',
        'en-GB,en;q=0.9',
        'zh-CN,zh;q=0.9',
        'ja-JP,ja;q=0.9',
        'ko-KR,ko;q=0.9',
        'de-DE,de;q=0.9',
        'fr-FR,fr;q=0.9',
        'es-ES,es;q=0.9',
        'pt-BR,pt;q=0.9',
        'ru-RU,ru;q=0.9'
    ]
    
    def __init__(self):
        self.current_fingerprint: Optional[Dict] = None
        self.fingerprint_cache: Dict[str, Dict] = {}
        self.last_rotation = datetime.now()
        self.rotation_interval = timedelta(hours=1)  # Rotate fingerprint every hour
    
    def generate_user_agent(self, browser: Optional[str] = None, 
                           os_type: Optional[str] = None,
                           mobile: bool = False) -> str:
        """
        Generate a realistic User-Agent string.
        
        Args:
            browser: Specific browser ('chrome', 'firefox', 'safari', 'edge')
            os_type: Operating system ('windows', 'macos', 'linux')
            mobile: Generate mobile User-Agent
            
        Returns:
            User-Agent string
        """
        if mobile:
            return random.choice(self.MOBILE_USER_AGENTS)
        
        # Select browser based on market share if not specified
        if not browser:
            browser = self._select_weighted_browser()
        
        # Select OS if not specified
        if not os_type:
            os_type = self._select_os_for_browser(browser)
        
        browser_data = self.BROWSER_DATA[browser]
        version = random.choice(browser_data['versions'])
        os_string = random.choice(self.OS_STRINGS[os_type])
        
        # Special handling for Safari (only on macOS)
        if browser == 'safari' and os_type != 'macos':
            os_string = random.choice(self.OS_STRINGS['macos'])
        
        user_agent = browser_data['template'].format(
            os_string=os_string,
            version=version
        )
        
        return user_agent
    
    def _select_weighted_browser(self) -> str:
        """Select browser based on market share weights"""
        total_weight = sum(data['weight'] for data in self.BROWSER_DATA.values())
        random_value = random.randint(1, total_weight)
        
        current_weight = 0
        for browser, data in self.BROWSER_DATA.items():
            current_weight += data['weight']
            if random_value <= current_weight:
                return browser
        
        return 'chrome'  # Fallback
    
    def _select_os_for_browser(self, browser: str) -> str:
        """Select appropriate OS for browser"""
        if browser == 'safari':
            return 'macos'
        
        # Weight OS selection
        os_weights = {'windows': 70, 'macos': 20, 'linux': 10}
        total_weight = sum(os_weights.values())
        random_value = random.randint(1, total_weight)
        
        current_weight = 0
        for os_type, weight in os_weights.items():
            current_weight += weight
            if random_value <= current_weight:
                return os_type
        
        return 'windows'  # Fallback
    
    def generate_browser_fingerprint(self, domain: Optional[str] = None) -> Dict[str, str]:
        """
        Generate a complete browser fingerprint.
        
        Args:
            domain: Domain to generate fingerprint for (for caching)
            
        Returns:
            Dictionary with browser fingerprint data
        """
        # Check cache first
        if domain and domain in self.fingerprint_cache:
            cached_fingerprint = self.fingerprint_cache[domain]
            # Check if fingerprint is still fresh
            if datetime.now() - cached_fingerprint['created'] < self.rotation_interval:
                return cached_fingerprint
        
        # Generate new fingerprint
        browser = self._select_weighted_browser()
        os_type = self._select_os_for_browser(browser)
        
        fingerprint = {
            'user_agent': self.generate_user_agent(browser, os_type),
            'accept': self._generate_accept_header(),
            'accept_language': random.choice(self.LANGUAGES),
            'accept_encoding': 'gzip, deflate, br',
            'dnt': random.choice(['1', '0']),  # Do Not Track
            'connection': 'keep-alive',
            'upgrade_insecure_requests': '1',
            'sec_fetch_dest': 'document',
            'sec_fetch_mode': 'navigate',
            'sec_fetch_site': 'none',
            'sec_fetch_user': '?1',
            'cache_control': 'max-age=0',
            'browser': browser,
            'os': os_type,
            'screen_resolution': random.choice(self.SCREEN_RESOLUTIONS),
            'timezone': self._generate_timezone(),
            'created': datetime.now()
        }
        
        # Add browser-specific headers
        if browser == 'chrome' or browser == 'edge':
            fingerprint.update({
                'sec_ch_ua': self._generate_sec_ch_ua(browser),
                'sec_ch_ua_mobile': '?0',
                'sec_ch_ua_platform': f'"{os_type.title()}"'
            })
        
        # Cache fingerprint
        if domain:
            self.fingerprint_cache[domain] = fingerprint
        
        self.current_fingerprint = fingerprint
        return fingerprint
    
    def _generate_accept_header(self) -> str:
        """Generate Accept header"""
        accept_headers = [
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        ]
        return random.choice(accept_headers)
    
    def _generate_sec_ch_ua(self, browser: str) -> str:
        """Generate Sec-CH-UA header for Chromium browsers"""
        if browser == 'chrome':
            version = random.choice(self.BROWSER_DATA['chrome']['versions']).split('.')[0]
            return f'"Not_A Brand";v="8", "Chromium";v="{version}", "Google Chrome";v="{version}"'
        elif browser == 'edge':
            version = random.choice(self.BROWSER_DATA['edge']['versions']).split('.')[0]
            return f'"Not_A Brand";v="8", "Chromium";v="{version}", "Microsoft Edge";v="{version}"'
        return ''
    
    def _generate_timezone(self) -> str:
        """Generate timezone offset"""
        timezones = [
            'America/New_York', 'America/Los_Angeles', 'Europe/London',
            'Europe/Berlin', 'Asia/Tokyo', 'Asia/Shanghai', 'Asia/Seoul',
            'Australia/Sydney', 'America/Toronto', 'Europe/Paris'
        ]
        return random.choice(timezones)
    
    def get_headers_for_request(self, url: str, referer: Optional[str] = None) -> Dict[str, str]:
        """
        Get HTTP headers for a request.
        
        Args:
            url: Target URL
            referer: Referer URL
            
        Returns:
            Dictionary of HTTP headers
        """
        from urllib.parse import urlparse
        
        domain = urlparse(url).netloc
        fingerprint = self.generate_browser_fingerprint(domain)
        
        headers = {
            'User-Agent': fingerprint['user_agent'],
            'Accept': fingerprint['accept'],
            'Accept-Language': fingerprint['accept_language'],
            'Accept-Encoding': fingerprint['accept_encoding'],
            'DNT': fingerprint['dnt'],
            'Connection': fingerprint['connection'],
            'Upgrade-Insecure-Requests': fingerprint['upgrade_insecure_requests']
        }
        
        # Add Chromium-specific headers
        if 'sec_ch_ua' in fingerprint:
            headers.update({
                'Sec-CH-UA': fingerprint['sec_ch_ua'],
                'Sec-CH-UA-Mobile': fingerprint['sec_ch_ua_mobile'],
                'Sec-CH-UA-Platform': fingerprint['sec_ch_ua_platform'],
                'Sec-Fetch-Dest': fingerprint['sec_fetch_dest'],
                'Sec-Fetch-Mode': fingerprint['sec_fetch_mode'],
                'Sec-Fetch-Site': fingerprint['sec_fetch_site'],
                'Sec-Fetch-User': fingerprint['sec_fetch_user']
            })
        
        # Add referer if provided
        if referer:
            headers['Referer'] = referer
        
        return headers
    
    def rotate_fingerprint(self, domain: Optional[str] = None):
        """
        Force rotation of browser fingerprint.
        
        Args:
            domain: Specific domain to rotate (all if None)
        """
        if domain:
            if domain in self.fingerprint_cache:
                del self.fingerprint_cache[domain]
        else:
            self.fingerprint_cache.clear()
            self.current_fingerprint = None
        
        self.last_rotation = datetime.now()
    
    def should_rotate_fingerprint(self) -> bool:
        """Check if fingerprint should be rotated"""
        return datetime.now() - self.last_rotation > self.rotation_interval
    
    def get_mobile_user_agent(self, platform: str = 'random') -> str:
        """
        Get mobile User-Agent string.
        
        Args:
            platform: Mobile platform ('ios', 'android', 'random')
            
        Returns:
            Mobile User-Agent string
        """
        if platform == 'ios':
            ios_agents = [ua for ua in self.MOBILE_USER_AGENTS if 'iPhone' in ua]
            return random.choice(ios_agents)
        elif platform == 'android':
            android_agents = [ua for ua in self.MOBILE_USER_AGENTS if 'Android' in ua]
            return random.choice(android_agents)
        else:
            return random.choice(self.MOBILE_USER_AGENTS)
    
    def get_fingerprint_summary(self) -> Dict[str, any]:
        """
        Get summary of current fingerprint.
        
        Returns:
            Dictionary with fingerprint summary
        """
        if not self.current_fingerprint:
            return {'status': 'No fingerprint generated'}
        
        return {
            'browser': self.current_fingerprint.get('browser'),
            'os': self.current_fingerprint.get('os'),
            'user_agent': self.current_fingerprint.get('user_agent'),
            'screen_resolution': self.current_fingerprint.get('screen_resolution'),
            'language': self.current_fingerprint.get('accept_language'),
            'created': self.current_fingerprint.get('created'),
            'cached_domains': len(self.fingerprint_cache)
        }
    
    def clear_cache(self):
        """Clear fingerprint cache"""
        self.fingerprint_cache.clear()
        self.current_fingerprint = None
    
    def export_fingerprint(self, file_path: str) -> bool:
        """
        Export current fingerprint to file.
        
        Args:
            file_path: Output file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.current_fingerprint:
                return False
            
            # Convert datetime to string for JSON serialization
            export_data = self.current_fingerprint.copy()
            export_data['created'] = export_data['created'].isoformat()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Error exporting fingerprint: {e}")
            return False
    
    def import_fingerprint(self, file_path: str) -> bool:
        """
        Import fingerprint from file.
        
        Args:
            file_path: Input file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert string back to datetime
            if 'created' in data:
                data['created'] = datetime.fromisoformat(data['created'])
            
            self.current_fingerprint = data
            return True
            
        except Exception as e:
            print(f"Error importing fingerprint: {e}")
            return False


# Global user agent manager instance
user_agent_manager = UserAgentManager()