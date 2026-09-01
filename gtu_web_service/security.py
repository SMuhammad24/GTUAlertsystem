"""
Security & Compliance Module for GTU Alert Automation.

Provides defense against:
- SSRF (Server-Side Request Forgery) and Private IP scanning
- XSS / HTML Injection in messaging alerts
- Credential & Token exposure in logs or stack traces
- Path Traversal on SQLite database paths
- Buffer & Memory Exhaustion (DoS)
"""

import ipaddress
import os
import re
import socket
import urllib.parse
from pathlib import Path
from typing import Tuple, List, Optional


# Regex for standard Telegram Bot Token: e.g. 1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ_1234567
TELEGRAM_BOT_TOKEN_PATTERN = re.compile(r'^\d{8,12}:[A-Za-z0-9_-]{30,50}$')

# Regex for Telegram Chat ID: e.g. 123456789 or -1001234567890 or @channel_username
TELEGRAM_CHAT_ID_PATTERN = re.compile(r'^(-?\d{5,18}|@[a-zA-Z0-9_]{4,32})$')

# Forbidden URL schemes
FORBIDDEN_SCHEMES = {'javascript', 'data', 'file', 'ftp', 'gopher', 'dict', 'ldap'}

# Dangerous private IP networks (SSRF prevention)
PRIVATE_NETWORKS = [
    ipaddress.ip_network('127.0.0.0/8'),      # Loopback
    ipaddress.ip_network('10.0.0.0/8'),       # Private-use Class A
    ipaddress.ip_network('172.16.0.0/12'),    # Private-use Class B
    ipaddress.ip_network('192.168.0.0/16'),   # Private-use Class C
    ipaddress.ip_network('169.254.0.0/16'),   # Link-local / Cloud Metadata (AWS/GCP/Azure)
    ipaddress.ip_network('0.0.0.0/8'),        # Current network
    ipaddress.ip_network('::1/128'),          # IPv6 loopback
    ipaddress.ip_network('fc00::/7'),         # IPv6 unique local
    ipaddress.ip_network('fe80::/10'),        # IPv6 link-local
]


def mask_secret(secret: str, visible_start: int = 4, visible_end: int = 4) -> str:
    """
    Mask sensitive secrets (Tokens, Passwords, Chat IDs) for safe logging.
    Example: '1234567890:ABCDEFGHIJK...' -> '1234...IJK'
    """
    if not secret:
        return "<EMPTY>"
    secret_str = str(secret).strip()
    if len(secret_str) <= (visible_start + visible_end):
        return "***"
    return f"{secret_str[:visible_start]}...{secret_str[-visible_end:]}"


def is_valid_telegram_token(token: str) -> bool:
    """Validate Telegram Bot Token format."""
    if not token or not isinstance(token, str):
        return False
    return bool(TELEGRAM_BOT_TOKEN_PATTERN.match(token.strip()))


def is_valid_chat_id(chat_id: str) -> bool:
    """Validate Telegram Chat ID format."""
    if not chat_id or not isinstance(chat_id, (str, int)):
        return False
    return bool(TELEGRAM_CHAT_ID_PATTERN.match(str(chat_id).strip()))


def is_ip_private(ip_str: str) -> bool:
    """Check if an IP address belongs to a private, loopback, or cloud-metadata network."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return any(ip in net for net in PRIVATE_NETWORKS) or ip.is_private or ip.is_loopback or ip.is_link_local
    except ValueError:
        return True  # If invalid, treat as unsafe


def is_safe_url(url: str, allowed_domains: Optional[List[str]] = None) -> Tuple[bool, str]:
    """
    Verify URL safety against SSRF, dangerous protocols, and unauthorized domains.
    """
    if not url or not isinstance(url, str):
        return False, "URL cannot be empty."

    url = url.strip()
    if len(url) > 2048:
        return False, "URL length exceeds safe limit (2048 characters)."

    try:
        parsed = urllib.parse.urlparse(url)
    except Exception as e:
        return False, f"Failed to parse URL: {e}"

    scheme = (parsed.scheme or '').lower()
    if scheme in FORBIDDEN_SCHEMES:
        return False, f"Prohibited URL scheme: '{scheme}'"

    if scheme not in ('http', 'https'):
        return False, f"Invalid scheme '{scheme}'. Only HTTP/HTTPS allowed."

    hostname = (parsed.hostname or '').lower()
    if not hostname:
        return False, "URL hostname is missing."

    # Check localhost / numeric IP directly
    if hostname in ('localhost', '127.0.0.1', '::1', '0.0.0.0', '169.254.169.254'):
        return False, "Access to localhost or cloud metadata IP is prohibited."

    # Domain whitelist verification
    if allowed_domains:
        domain_matched = any(
            hostname == d.lower() or hostname.endswith('.' + d.lower())
            for d in allowed_domains
        )
        if not domain_matched:
            return False, f"Domain '{hostname}' is not in the allowed domains list."

    # Prohibited path keywords (Login, Auth, Admin portals)
    prohibited_keywords = [
        'login', 'signin', 'admin', 'auth', 'student_portal', 'studentportal',
        'account', 'captcha', 'pwd', 'password', 'session', 'dashboard', 'profile'
    ]
    path_and_query = (parsed.path + '?' + (parsed.query or '')).lower()
    for forbidden in prohibited_keywords:
        if forbidden in path_and_query:
            return False, f"Access to sensitive endpoint containing '{forbidden}' is prohibited."

    return True, "URL is safe and verified."


def sanitize_text(text: str, max_length: int = 500) -> str:
    """
    Clean and sanitize raw strings:
    - Strips null bytes and control characters
    - Normalizes multiple whitespaces
    - Truncates to safe max length
    """
    if not text:
        return ""
    # Remove null bytes and non-printable control characters (except newline/tab)
    cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', str(text))
    # Normalize whitespaces
    cleaned = re.sub(r'[ \t]+', ' ', cleaned).strip()
    return cleaned[:max_length]


def sanitize_for_html(text: str, max_length: int = 500) -> str:
    """
    Sanitize text and escape HTML special characters to prevent HTML/XSS injection.
    """
    import html
    clean_str = sanitize_text(text, max_length=max_length)
    return html.escape(clean_str, quote=True)


def safe_db_path(target_path: Path, base_dir: Path) -> Path:
    """
    Ensure the SQLite database file resides strictly inside the allowed project directory.
    Prevents Path Traversal attacks (e.g. `../../etc/passwd` or `../../system32`).
    """
    resolved_target = Path(target_path).resolve()
    resolved_base = Path(base_dir).resolve()

    try:
        resolved_target.relative_to(resolved_base)
    except ValueError:
        raise PermissionError(f"Security Alert: Path Traversal detected. '{target_path}' is outside base directory.")

    return resolved_target
