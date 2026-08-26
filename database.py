import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from config import Config


class Database:
    """SQLite Database manager for tracking processed GTU circulars."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Config.DB_PATH
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize database schema if it doesn't exist."""
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
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_link ON circulars(link)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON circulars(created_at)")
        finally:
            conn.close()

    @staticmethod
    def generate_id(title: str, date: str, link: str) -> str:
        """Generate a unique hash identifier for a circular."""
        # Normalize title, date and link
        raw_str = f"{title.strip().lower()}|{date.strip()}|{link.strip()}"
        return hashlib.sha256(raw_str.encode('utf-8')).hexdigest()

    def is_processed(self, circular_id: str) -> bool:
        """Check if circular with given ID has already been recorded."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM circulars WHERE id = ?", (circular_id,))
            return cursor.fetchone() is not None
        finally:
            conn.close()

    def add_circular(self, circular: Dict) -> bool:
        """
        Add a new circular to the database.
        Returns True if newly inserted, False if already exists.
        """
        cid = circular.get('id') or self.generate_id(
            circular['title'],
            circular['date'],
            circular['link']
        )
        if self.is_processed(cid):
            return False

        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO circulars (id, title, date, link, category, is_important)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    cid,
                    circular['title'],
                    circular['date'],
                    circular['link'],
                    circular.get('category', 'General'),
                    1 if circular.get('is_important') else 0
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
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM circulars ORDER BY created_at DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
