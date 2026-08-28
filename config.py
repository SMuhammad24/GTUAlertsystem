import os
import sys
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root if it exists
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / '.env'

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    # Also load standard environment variables (e.g. in GitHub Actions)
    load_dotenv()


from security import (
    is_safe_url,
    is_valid_telegram_token,
    is_valid_chat_id,
    mask_secret,
    safe_db_path,
)


class Config:
    """
    Application configuration loader and security/compliance policy validator.
    
    LEGAL & SAFETY COMPLIANCE RULES:
    ALLOWED:
      1. Monitor only publicly accessible GTU webpages and public notifications.
      2. Share only publicly available GTU notification info in Telegram/Discord.
      3. Check GTU at reasonable intervals without creating excessive server load.
    DO NOT:
      1. Do not bypass login, authentication, CAPTCHA, or access controls.
      2. Do not collect, store, or forward private or student-specific info.
      3. Do not overload GTU servers or perform deep bulk extraction.
    """
    
    BASE_DIR = BASE_DIR
    DB_PATH = safe_db_path(BASE_DIR / 'circulars.db', BASE_DIR)
    
    # Telegram Credentials
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '').strip()
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '').strip()

    # Discord Credentials (Optional)
    DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '').strip()

    # AI Integration (Optional Gemini API Key)
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '').strip()

    # Web Dashboard Settings
    WEB_PORT = int(os.getenv('WEB_PORT', '8080'))
    WEB_HOST = os.getenv('WEB_HOST', '127.0.0.1')
    
    # Public Notification URL (Only official public circular board allowed)
    GTU_CIRCULAR_URL = os.getenv('GTU_CIRCULAR_URL', 'https://www.gtu.ac.in/Circular.aspx').strip()
    
    # Safety: Enforce allowed domains for public circulars only
    ALLOWED_DOMAINS = ['www.gtu.ac.in', 'gtu.ac.in', 's3-ap-southeast-1.amazonaws.com', 's3.amazonaws.com']
    
    # Safety: Prohibit access to private/authenticated/student-specific endpoints
    PROHIBITED_PATH_KEYWORDS = [
        'login', 'signin', 'admin', 'auth', 'student_portal', 'studentportal',
        'account', 'captcha', 'pwd', 'password', 'session', 'dashboard', 'profile'
    ]
    
    # Safety: Minimum allowed polling interval in minutes to prevent excessive server load
    MIN_CHECK_INTERVAL_MINUTES = 5
    
    # Daemon Mode Polling Interval (clamped to minimum safe interval)
    try:
        _raw_interval = int(os.getenv('CHECK_INTERVAL_MINUTES', '15'))
        CHECK_INTERVAL_MINUTES = max(_raw_interval, MIN_CHECK_INTERVAL_MINUTES)
    except ValueError:
        CHECK_INTERVAL_MINUTES = 15
        
    # Optional Keyword Filtering
    raw_filter = os.getenv('KEYWORD_FILTER', '').strip()
    KEYWORD_FILTER = [k.strip().lower() for k in raw_filter.split(',') if k.strip()] if raw_filter else []
    
    # Polite User-Agent clearly identifying public notification check
    USER_AGENT = os.getenv(
        'USER_AGENT',
        'GTU-Public-Notification-Monitor/1.0 (+https://www.gtu.ac.in/Circular.aspx; Polite-Public-Notice-Reader)'
    )
    
    # Granular Connection Timeouts: (connect_timeout, read_timeout) in seconds
    CONNECT_TIMEOUT = 10
    READ_TIMEOUT = 25
    REQUEST_TIMEOUT = (CONNECT_TIMEOUT, READ_TIMEOUT)
    
    # Max allowed response payload size (5 MB) to prevent DoS memory exhaustion
    MAX_RESPONSE_BYTES = 5 * 1024 * 1024

    @classmethod
    def is_safe_public_url(cls, url: str) -> tuple[bool, str]:
        """
        Verify that URL complies with security & safety rules:
        - Rejects SSRF, localhost, private IPs, and non-whitelisted domains.
        - Rejects any login, authentication, CAPTCHA, or student-specific portals.
        """
        return is_safe_url(url, allowed_domains=cls.ALLOWED_DOMAINS)

    @classmethod
    def validate(cls, require_telegram: bool = True) -> tuple[bool, str]:
        """Validate configuration settings, token formats, and compliance rules."""
        if require_telegram:
            if not cls.TELEGRAM_BOT_TOKEN:
                return False, "TELEGRAM_BOT_TOKEN missing hai! Kripya .env file me bot token set karein."
            if not is_valid_telegram_token(cls.TELEGRAM_BOT_TOKEN):
                masked = mask_secret(cls.TELEGRAM_BOT_TOKEN)
                return False, f"TELEGRAM_BOT_TOKEN format invalid hai ({masked}). Format must be like: 1234567890:ABCdef..."
            if not cls.TELEGRAM_CHAT_ID:
                return False, "TELEGRAM_CHAT_ID missing hai! Kripya .env file me chat ID set karein."
            if not is_valid_chat_id(cls.TELEGRAM_CHAT_ID):
                masked_chat = mask_secret(cls.TELEGRAM_CHAT_ID)
                return False, f"TELEGRAM_CHAT_ID format invalid hai ({masked_chat}). Format must be numeric ID or @channel."
        
        is_safe, reason = cls.is_safe_public_url(cls.GTU_CIRCULAR_URL)
        if not is_safe:
            return False, f"Safety Compliance Error: {reason}"
            
        return True, "Config OK"
