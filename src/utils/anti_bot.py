# src/utils/anti_bot.py

import random
import time
import asyncio
from typing import Dict, Optional

class AntiBot:
    def __init__(self):
        self.request_count = 0
        self.start_time = time.time()
        self.backoff_factor = 1.0
        self.max_backoff = 30.0
        
    def reset_backoff(self):
        """Reset backoff factor on successful request"""
        self.backoff_factor = 1.0

# Global instance for stateful backoff tracking
_anti_bot = AntiBot()

# Realistic and rotating user agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]

# Proxy placeholders — fill with actual proxy dicts if needed
PROXIES = [
    None,  # Direct connection
    # {"http": "http://proxy1:8080", "https": "http://proxy1:8080"},
    # {"http": "http://proxy2:8080", "https": "http://proxy2:8080"},
]

# Accept languages for rotation
ACCEPT_LANGUAGES = [
    "en-US,en;q=0.9",
    "en-US,en;q=0.8,es;q=0.7",
    "en-GB,en;q=0.9,en-US;q=0.8",
    "en-US,en;q=0.9,fr;q=0.8",
]

def get_headers() -> Dict[str, str]:
    """
    Generate realistic rotated HTTP headers to mimic real browsers.
    """
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": random.choice(ACCEPT_LANGUAGES),
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }
    
    # Occasionally add extra security headers for realism
    if random.random() < 0.3:
        headers.update({
            "Sec-CH-UA": '"Not_A Brand";v="8", "Chromium";v="120"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": random.choice(['"Windows"', '"macOS"', '"Linux"']),
        })
    
    return headers

def rotate_proxy() -> Optional[Dict[str, str]]:
    """
    Return a randomly selected proxy config or empty dict for direct connection.
    """
    proxy = random.choice(PROXIES)
    if proxy is None:
        return {}
    return proxy

def backoff(increase: bool = False) -> None:
    """
    Synchronous backoff with exponential increase after errors.
    Includes basic rate limiting to max 10 requests/min.
    """
    global _anti_bot
    
    if increase:
        _anti_bot.backoff_factor = min(_anti_bot.backoff_factor * 1.5, _anti_bot.max_backoff)
        sleep_time = random.uniform(_anti_bot.backoff_factor * 2, _anti_bot.backoff_factor * 4)
    else:
        _anti_bot.reset_backoff()
        sleep_time = random.uniform(1, 3)
    
    _anti_bot.request_count += 1
    elapsed = time.time() - _anti_bot.start_time
    if elapsed < 60 and _anti_bot.request_count > 10:
        sleep_time += 60 - elapsed
        _anti_bot.request_count = 0
        _anti_bot.start_time = time.time()
    
    time.sleep(sleep_time)

async def async_backoff(increase: bool = False) -> None:
    """
    Async version of backoff for use with asyncio / playwright workflows.
    """
    global _anti_bot
    
    if increase:
        _anti_bot.backoff_factor = min(_anti_bot.backoff_factor * 1.5, _anti_bot.max_backoff)
        sleep_time = random.uniform(_anti_bot.backoff_factor * 2, _anti_bot.backoff_factor * 4)
    else:
        _anti_bot.reset_backoff()
        sleep_time = random.uniform(1, 3)
    
    await asyncio.sleep(sleep_time)

def detect_captcha(response_text: str) -> bool:
    """
    Detect CAPTCHA presence in page content by matching common keywords.
    """
    captcha_indicators = [
        "captcha", "recaptcha", "hcaptcha", "cloudflare",
        "please verify", "security check", "robot verification",
        "prove you're human"
    ]
    response_lower = response_text.lower()
    return any(indicator in response_lower for indicator in captcha_indicators)

def detect_rate_limit(response_text: str, status_code: int) -> bool:
    """
    Detect if response indicates rate limiting (status 429 or common keywords).
    """
    if status_code == 429:
        return True
    
    rate_limit_indicators = [
        "rate limit", "too many requests", "slow down", "exceeded",
        "throttled", "temporarily blocked"
    ]
    response_lower = response_text.lower()
    return any(indicator in response_lower for indicator in rate_limit_indicators)

def get_session_config() -> Dict:
    """
    Provide default session config dict for `requests` library.
    """
    return {
        "headers": get_headers(),
        "timeout": 15,
        "allow_redirects": True,
        "max_redirects": 5,
    }

class SessionManager:
    """
    Manage multiple rotating requests sessions for anti-bot evasion.
    """
    def __init__(self, max_sessions: int = 3):
        self.sessions = []
        self.max_sessions = max_sessions
        self.current_session = 0
        self._initialize_sessions()
    
    def _initialize_sessions(self):
        import requests
        for _ in range(self.max_sessions):
            session = requests.Session()
            session.headers.update(get_headers())
            self.sessions.append(session)
    
    def get_session(self) -> 'requests.Session':
        """
        Rotate and return the next requests.Session instance with fresh headers.
        """
        session = self.sessions[self.current_session]
        self.current_session = (self.current_session + 1) % self.max_sessions
        session.headers.update(get_headers())
        return session
    
    def close_all(self):
        for session in self.sessions:
            session.close()

# Global session manager instance
_session_manager = SessionManager()

def get_rotated_session():
    """
    Get a rotated requests session for each request cycle.
    """
    return _session_manager.get_session()
