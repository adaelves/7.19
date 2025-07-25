"""
Anti-crawler utilities for adult content platforms.
Provides common mechanisms to bypass anti-bot and crawler detection.
"""
import asyncio
import random
import time
from typing import Dict, List, Optional
import aiohttp
from urllib.parse import urlparse


class AntiCrawlerManager:
    """
    Manager for anti-crawler mechanisms used by adult content platforms.
    Provides methods to bypass common anti-bot measures.
    """
    
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        self.common_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        self.rate_limits = {}  # Domain -> last request time
        self.min_delay = 1.0  # Minimum delay between requests (seconds)
        self.max_delay = 3.0  # Maximum delay between requests (seconds)
    
    def get_random_user_agent(self) -> str:
        """Get a random user agent string"""
        return random.choice(self.user_agents)
    
    def get_common_headers(self, domain: str = None) -> Dict[str, str]:
        """Get common headers with random user agent"""
        headers = self.common_headers.copy()
        headers['User-Agent'] = self.get_random_user_agent()
        
        # Add domain-specific headers
        if domain:
            domain_headers = self._get_domain_specific_headers(domain)
            headers.update(domain_headers)
        
        return headers
    
    def _get_domain_specific_headers(self, domain: str) -> Dict[str, str]:
        """Get domain-specific headers for better compatibility"""
        domain_headers = {}
        
        if 'pornhub.com' in domain:
            domain_headers.update({
                'Referer': 'https://www.pornhub.com/',
                'Origin': 'https://www.pornhub.com'
            })
        elif 'youporn.com' in domain:
            domain_headers.update({
                'Referer': 'https://www.youporn.com/',
                'Origin': 'https://www.youporn.com'
            })
        elif 'xvideos.com' in domain:
            domain_headers.update({
                'Referer': 'https://www.xvideos.com/',
                'Origin': 'https://www.xvideos.com'
            })
        elif 'xhamster.com' in domain:
            domain_headers.update({
                'Referer': 'https://xhamster.com/',
                'Origin': 'https://xhamster.com'
            })
        elif 'kissjav.com' in domain:
            domain_headers.update({
                'Referer': 'https://kissjav.com/',
                'Origin': 'https://kissjav.com'
            })
        
        return domain_headers
    
    async def apply_rate_limiting(self, domain: str) -> None:
        """Apply rate limiting for the given domain"""
        current_time = time.time()
        
        if domain in self.rate_limits:
            last_request_time = self.rate_limits[domain]
            time_since_last = current_time - last_request_time
            
            if time_since_last < self.min_delay:
                delay = random.uniform(self.min_delay, self.max_delay)
                await asyncio.sleep(delay)
        
        self.rate_limits[domain] = time.time()
    
    def get_age_verification_cookies(self, domain: str) -> Dict[str, str]:
        """Get age verification cookies for adult content sites"""
        cookies = {}
        
        if 'pornhub.com' in domain:
            cookies.update({
                'age_verified': '1',
                'platform': 'pc',
                'bs': 'whatever'
            })
        elif 'youporn.com' in domain:
            cookies.update({
                'age_gate': '1',
                'age_verified': 'true'
            })
        elif 'xvideos.com' in domain:
            cookies.update({
                'age_verified': '1'
            })
        elif 'xhamster.com' in domain:
            cookies.update({
                'age_verified': '1',
                'ageGateAccepted': 'true'
            })
        elif 'kissjav.com' in domain:
            cookies.update({
                'age_check': '1',
                'adult_content': 'accepted'
            })
        
        return cookies
    
    async def setup_session(self, session: aiohttp.ClientSession, url: str) -> None:
        """Setup session with anti-crawler measures"""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        # Apply rate limiting
        await self.apply_rate_limiting(domain)
        
        # Set headers
        headers = self.get_common_headers(domain)
        session.headers.update(headers)
        
        # Set age verification cookies
        cookies = self.get_age_verification_cookies(domain)
        for name, value in cookies.items():
            session.cookie_jar.update_cookies({name: value})
    
    async def handle_cloudflare_challenge(self, session: aiohttp.ClientSession, url: str) -> bool:
        """Handle Cloudflare challenge if present"""
        # In a real implementation, this would:
        # 1. Detect Cloudflare challenge page
        # 2. Execute JavaScript challenge
        # 3. Submit challenge response
        # 4. Handle rate limiting
        
        # For now, just add appropriate headers
        cloudflare_headers = {
            'CF-RAY': f'{random.randint(100000000000, 999999999999)}-LAX',
            'CF-Cache-Status': 'DYNAMIC',
            'CF-Request-ID': f'{random.randint(100000000000, 999999999999)}'
        }
        
        session.headers.update(cloudflare_headers)
        return True
    
    async def bypass_geo_restrictions(self, session: aiohttp.ClientSession, country_code: str = 'US') -> None:
        """Bypass geographical restrictions by setting appropriate headers"""
        geo_headers = {
            'CF-IPCountry': country_code,
            'X-Forwarded-For': self._generate_ip_for_country(country_code),
            'X-Real-IP': self._generate_ip_for_country(country_code)
        }
        
        session.headers.update(geo_headers)
    
    def _generate_ip_for_country(self, country_code: str) -> str:
        """Generate a fake IP address for the given country"""
        # This is a simplified implementation
        # In reality, you would use actual IP ranges for each country
        
        ip_ranges = {
            'US': ['8.8.8.{}', '1.1.1.{}', '208.67.222.{}'],
            'GB': ['81.2.69.{}', '195.82.50.{}'],
            'DE': ['85.214.132.{}', '217.160.0.{}'],
            'JP': ['133.242.0.{}', '210.188.224.{}']
        }
        
        if country_code in ip_ranges:
            ip_template = random.choice(ip_ranges[country_code])
            return ip_template.format(random.randint(1, 254))
        else:
            # Default to US IP
            return f'8.8.8.{random.randint(1, 254)}'
    
    async def simulate_human_behavior(self, session: aiohttp.ClientSession, url: str) -> None:
        """Simulate human-like browsing behavior"""
        # Random delay to simulate reading time
        reading_delay = random.uniform(2.0, 5.0)
        await asyncio.sleep(reading_delay)
        
        # Simulate mouse movements and clicks (headers only)
        human_headers = {
            'Sec-CH-UA': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-CH-UA-Mobile': '?0',
            'Sec-CH-UA-Platform': '"Windows"'
        }
        
        session.headers.update(human_headers)


# Global instance for easy access
anti_crawler = AntiCrawlerManager()