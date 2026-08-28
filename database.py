import sqlite3
import hashlib
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional, Any
from config import Config
from security import safe_db_path, sanitize_text


class Database:
    """Secure SQLite Database manager for tracking and querying processed GTU circulars."""

    def __init__(self, db_path: Optional[Path] = None):
        target = db_path or Config.DB_PATH
        # Enforce Path Traversal Protection
        if db_path is not None:
            self.db_path = Path(target).resolve()
        else:
            self.db_path = safe_db_path(target, Config.BASE_DIR)
            
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=15.0)
        conn.row_factory = sqlite3.Row
        # Enable WAL mode and foreign keys for durability and concurrency
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
        except Exception:
            pass
        return conn

    def _init_db(self):
        """Initialize database schema, indexes, and apply backward-compatible migrations."""
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS circulars (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        date TEXT NOT NULL,
                        link TEXT NOT NULL,
                        category TEXT,
                        is_important INTEGER DEFAULT 0,
                        tags TEXT DEFAULT '',
                        summary TEXT DEFAULT '',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_link ON circulars(link)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON circulars(created_at)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON circulars(category)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_date ON circulars(date)")

                # Automatic schema migration for existing databases
                cursor.execute("PRAGMA table_info(circulars)")
                columns = [row['name'] for row in cursor.fetchall()]
                if 'tags' not in columns:
                    cursor.execute("ALTER TABLE circulars ADD COLUMN tags TEXT DEFAULT ''")
                if 'summary' not in columns:
                    cursor.execute("ALTER TABLE circulars ADD COLUMN summary TEXT DEFAULT ''")
        finally:
            conn.close()

    @staticmethod
    def generate_id(title: str, date: str, link: str) -> str:
        """Generate a unique SHA-256 hash identifier for a circular."""
        norm_title = sanitize_text(title, max_length=400).strip().lower()
        norm_date = sanitize_text(date, max_length=50).strip()
        norm_link = sanitize_text(link, max_length=1000).strip()
        raw_str = f"{norm_title}|{norm_date}|{norm_link}"
        return hashlib.sha256(raw_str.encode('utf-8')).hexdigest()

    def is_processed(self, circular_id: str) -> bool:
        """Check if circular with given ID has already been recorded."""
        if not circular_id or not isinstance(circular_id, str):
            return False
        clean_id = sanitize_text(circular_id, max_length=64)
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM circulars WHERE id = ?", (clean_id,))
            return cursor.fetchone() is not None
        finally:
            conn.close()

    def add_circular(self, circular: Dict) -> bool:
        """
        Add a new circular to the database.
        Returns True if newly inserted, False if already exists.
        """
        clean_title = sanitize_text(circular.get('title', ''), max_length=400)
        clean_date = sanitize_text(circular.get('date', 'Recent'), max_length=50)
        clean_link = sanitize_text(circular.get('link', ''), max_length=1000)
        clean_cat = sanitize_text(circular.get('category', 'General'), max_length=50)
        clean_tags = sanitize_text(circular.get('tags', ''), max_length=200)
        clean_sum = sanitize_text(circular.get('summary', ''), max_length=400)
        
        cid = circular.get('id') or self.generate_id(clean_title, clean_date, clean_link)
        cid = sanitize_text(cid, max_length=64)

        if self.is_processed(cid):
            return False

        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO circulars (id, title, date, link, category, is_important, tags, summary)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    cid,
                    clean_title,
                    clean_date,
                    clean_link,
                    clean_cat,
                    1 if circular.get('is_important') else 0,
                    clean_tags,
                    clean_sum
                ))
                return True
        finally:
            conn.close()

    def get_total_count(self) -> int:
        """Return total number of saved circulars."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM circulars")
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def get_recent_circulars(self, limit: int = 10) -> List[Dict]:
        """Fetch the most recently stored circulars."""
        safe_limit = max(1, min(int(limit), 200))
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM circulars ORDER BY created_at DESC, id DESC LIMIT ?", (safe_limit,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def search_circulars(self, query: str, limit: int = 10) -> List[Dict]:
        """Search circulars by title, tags, or category."""
        if not query or not query.strip():
            return self.get_recent_circulars(limit)
            
        clean_query = sanitize_text(query, max_length=100).strip()
        search_pattern = f"%{clean_query}%"
        safe_limit = max(1, min(int(limit), 100))
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM circulars 
                WHERE title LIKE ? OR category LIKE ? OR tags LIKE ?
                ORDER BY created_at DESC 
                LIMIT ?
            """, (search_pattern, search_pattern, search_pattern, safe_limit))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_circulars_by_category(self, category: str, limit: int = 10) -> List[Dict]:
        """Fetch circulars belonging to a specific category."""
        clean_cat = sanitize_text(category, max_length=50).strip()
        search_pattern = f"%{clean_cat}%"
        safe_limit = max(1, min(int(limit), 100))
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM circulars 
                WHERE category LIKE ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (search_pattern, safe_limit))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_category_stats(self) -> Dict[str, int]:
        """Get count breakdown of circulars by category."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT category, COUNT(*) as count 
                FROM circulars 
                GROUP BY category 
                ORDER BY count DESC
            """)
            stats = {}
            for row in cursor.fetchall():
                cat = row['category'] or 'General'
                stats[cat] = row['count']
            return stats
        finally:
            conn.close()

    def get_todays_circulars(self) -> List[Dict]:
        """Fetch circulars added today."""
        today_str = datetime.now().strftime('%Y-%m-%d')
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM circulars 
                WHERE created_at LIKE ? 
                ORDER BY created_at DESC
            """, (f"{today_str}%",))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
