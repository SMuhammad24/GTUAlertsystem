import os
import sys
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


class Config:
    """Application configuration loader and validator."""
    
    BASE_DIR = BASE_DIR
    DB_PATH = BASE_DIR / 'circulars.db'
    
    # Telegram Credentials
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '').strip()
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '').strip()
    
    # Web Scraper URL
    GTU_CIRCULAR_URL = os.getenv('GTU_CIRCULAR_URL', 'https://www.gtu.ac.in/Circular.aspx').strip()
    
    # Daemon Mode Polling Interval
    try:
        CHECK_INTERVAL_MINUTES = int(os.getenv('CHECK_INTERVAL_MINUTES', '15'))
    except ValueError:
        CHECK_INTERVAL_MINUTES = 15
        
    # Optional Keyword Filtering
    raw_filter = os.getenv('KEYWORD_FILTER', '').strip()
    KEYWORD_FILTER = [k.strip().lower() for k in raw_filter.split(',') if k.strip()] if raw_filter else []
    
    # User-Agent for web requests
    USER_AGENT = os.getenv(
        'USER_AGENT',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    REQUEST_TIMEOUT = 30 # seconds

    @classmethod
    def validate(cls, require_telegram: bool = True) -> tuple[bool, str]:
        """Validate configuration settings."""
        if require_telegram:
            if not cls.TELEGRAM_BOT_TOKEN:
                return False, "TELEGRAM_BOT_TOKEN missing hai! Kripya .env file me bot token set karein."
            if not cls.TELEGRAM_CHAT_ID:
                return False, "TELEGRAM_CHAT_ID missing hai! Kripya .env file me chat ID set karein."
        return True, "Config OK"
