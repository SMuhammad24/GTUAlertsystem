import os
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests
from config import Config
from security import is_safe_url, sanitize_text


class PDFInspector:
    """
    Lightweight, Server-Safe PDF Text & Table Inspector for GTU Circulars.
    
    SAFETY & ZERO-LOAD COMPLIANCE:
    - Streams at most 2MB per file (strictly guards GTU bandwidth).
    - Caches inspected PDFs locally (never downloads the same PDF twice).
    - Throttled and executed ONLY on newly detected circulars (0-2 per day).
    """

    CACHE_DIR = Config.BASE_DIR / 'cache' / 'pdfs'
    MAX_PDF_BYTES = 2 * 1024 * 1024  # 2MB maximum limit

    @classmethod
    def _get_cache_path(cls, url: str) -> Path:
        cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        return cls.CACHE_DIR / f"{url_hash}.txt"

    @classmethod
    def extract_text_safe(cls, pdf_url: str) -> str:
        """
        Safely stream and extract text from public GTU PDF with caching.
        """
        if not pdf_url or not pdf_url.lower().endswith('.pdf'):
            return ""

        is_safe, _ = is_safe_url(pdf_url, allowed_domains=Config.ALLOWED_DOMAINS)
        if not is_safe:
            return ""

        cache_file = cls._get_cache_path(pdf_url)
        if cache_file.exists():
            try:
                return cache_file.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                pass

        try:
            # Stream with size limit
            resp = requests.get(pdf_url, stream=True, timeout=Config.REQUEST_TIMEOUT, headers={'User-Agent': Config.USER_AGENT})
            if resp.status_code != 200:
                return ""

            pdf_bytes = bytearray()
            for chunk in resp.iter_content(chunk_size=8192):
                pdf_bytes.extend(chunk)
                if len(pdf_bytes) > cls.MAX_PDF_BYTES:
                    break

            text = ""
            # Try pypdf if installed
            try:
                import io
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(pdf_bytes))
                for page in reader.pages[:3]:  # inspect at most first 3 pages
                    text += page.extract_text() or ""
            except ImportError:
                # Fallback: Extract ASCII text streams
                text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', ' ', pdf_bytes.decode('latin-1', errors='ignore'))
                text = re.sub(r'\s+', ' ', text)

            clean_text = sanitize_text(text, max_length=5000)
            
            # Save to cache
            try:
                cache_file.write_text(clean_text, encoding='utf-8', errors='ignore')
            except Exception:
                pass

            return clean_text
        except Exception:
            return ""

    @classmethod
    def inspect_tables_and_deadlines(cls, pdf_url: str) -> Dict[str, Any]:
        """
        Inspect PDF content for branch-specific form dates or penalty slabs.
        """
        text = cls.extract_text_safe(pdf_url)
        if not text:
            return {'has_extra': False, 'extracted_dates': [], 'penalty_slabs': []}

        # Date extraction
        dates = re.findall(r'\b\d{1,2}[-\/\.]\d{1,2}[-\/\.]20\d\d\b', text)
        penalties = re.findall(r'(?:Rs\.?|₹)\s*(\d{2,4})', text)

        return {
            'has_extra': bool(dates or penalties),
            'extracted_dates': list(set(dates))[:4],
            'penalty_slabs': list(set(penalties))[:3]
        }
