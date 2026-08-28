import time
import requests
from typing import Dict, List, Optional, Tuple, Any
from config import Config
from database import Database
from notifier import TelegramNotifier
from tagger import CircularTagger
from extractor import DeadlineExtractor
from security import sanitize_for_html, sanitize_text, mask_secret


class InteractiveTelegramBot:
    """
    Interactive 2-Way Telegram Bot listener for GTU Circulars.
    Handles student commands (/start, /latest, /search, /exams, /results, /fees, /stats, /digest, /help)
    using server-safe Telegram long-polling.
    """

    def __init__(self, bot_token: Optional[str] = None):
        self.bot_token = (bot_token or Config.TELEGRAM_BOT_TOKEN).strip()
        self.notifier = TelegramNotifier(bot_token=self.bot_token)
        self.db = Database()
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.last_update_id = 0

    def handle_command(self, text: str, chat_id: str) -> str:
        """Process incoming student commands and return HTML response."""
        parts = text.strip().split()
        if not parts:
            return ""
        
        cmd = parts[0].lower().split('@')[0]  # strip bot username if present (e.g. /latest@bot)
        args = parts[1:] if len(parts) > 1 else []

        if cmd in ['/start', '/help']:
            return (
                "🤖 <b>Welcome to GTU Circular Automation Bot!</b>\n\n"
                "Aap yahan GTU ke sare official circulars, exam updates aur fee deadlines dekh sakte hain.\n\n"
                "📌 <b>Available Commands:</b>\n"
                "🔹 <code>/latest [n]</code> - Dekhein pichle 5 ya N naye circulars\n"
                "🔹 <code>/search &lt;keyword&gt;</code> - Circulars search karein (e.g. <code>/search fee</code>)\n"
                "🔹 <code>/exams</code> - Recent Exam & Timetable updates\n"
                "🔹 <code>/results</code> - Recent Results & Rechecking circulars\n"
                "🔹 <code>/fees</code> - Fee & Penalty notifications\n"
                "🔹 <code>/stats</code> - Database aur tracking statistics\n"
                "🔹 <code>/digest</code> - Aaj ke circulars aur active deadlines\n\n"
                "⚡ <i>Auto-alerts active for new GTU notifications!</i>"
            )

        elif cmd == '/latest':
            limit = 5
            if args and args[0].isdigit():
                limit = max(1, min(int(args[0]), 10))
            
            circulars = self.db.get_recent_circulars(limit=limit)
            if not circulars:
                return "ℹ️ Abhi database me koi circulars nahi hain."
            
            lines = [f"📢 <b>Latest {len(circulars)} GTU Circulars:</b>\n"]
            for idx, c in enumerate(circulars, 1):
                safe_title = sanitize_for_html(c['title'], max_length=200)
                safe_link = sanitize_for_html(c['link'], max_length=1000)
                date_str = sanitize_for_html(c['date'], max_length=30)
                cat = sanitize_for_html(c.get('category', 'General'), max_length=30)
                lines.append(f"<b>{idx}. {safe_title}</b>")
                lines.append(f"   📅 {date_str} | 🏷️ {cat}")
                lines.append(f"   🔗 <a href=\"{safe_link}\">Download PDF</a>\n")
            return "\n".join(lines)

        elif cmd == '/search':
            if not args:
                return "⚠️ Kripya search term enter karein. Example: <code>/search fee</code> ya <code>/search BE sem 6</code>"
            
            query = " ".join(args)
            results = self.db.search_circulars(query, limit=5)
            if not results:
                safe_q = sanitize_for_html(query, max_length=50)
                return f"🔍 '<b>{safe_q}</b>' ke related koi circular nahi mila."
            
            lines = [f"🔍 <b>Search results for '{sanitize_for_html(query, 50)}'</b> ({len(results)} found):\n"]
            for idx, c in enumerate(results, 1):
                safe_title = sanitize_for_html(c['title'], max_length=200)
                safe_link = sanitize_for_html(c['link'], max_length=1000)
                date_str = sanitize_for_html(c['date'], max_length=30)
                lines.append(f"<b>{idx}. {safe_title}</b>")
                lines.append(f"   📅 {date_str} | 🔗 <a href=\"{safe_link}\">PDF Link</a>\n")
            return "\n".join(lines)

        elif cmd == '/exams':
            circulars = self.db.get_circulars_by_category('Exam', limit=5)
            if not circulars:
                return "ℹ️ Koi exam circular nahi mila."
            lines = ["📝 <b>Recent Exam & Timetable Circulars:</b>\n"]
            for idx, c in enumerate(circulars, 1):
                lines.append(f"<b>{idx}. {sanitize_for_html(c['title'], 200)}</b>")
                lines.append(f"   📅 {c['date']} | 🔗 <a href=\"{sanitize_for_html(c['link'], 1000)}\">View PDF</a>\n")
            return "\n".join(lines)

        elif cmd == '/results':
            circulars = self.db.get_circulars_by_category('Result', limit=5)
            if not circulars:
                return "ℹ️ Koi result circular nahi mila."
            lines = ["🏆 <b>Recent Result Declarations:</b>\n"]
            for idx, c in enumerate(circulars, 1):
                lines.append(f"<b>{idx}. {sanitize_for_html(c['title'], 200)}</b>")
                lines.append(f"   📅 {c['date']} | 🔗 <a href=\"{sanitize_for_html(c['link'], 1000)}\">View PDF</a>\n")
            return "\n".join(lines)

        elif cmd == '/fees':
            circulars = self.db.get_circulars_by_category('Fee', limit=5)
            if not circulars:
                return "ℹ️ Koi fee/penalty circular nahi mila."
            lines = ["🚨 <b>Recent Fee & Penalty Notifications:</b>\n"]
            for idx, c in enumerate(circulars, 1):
                lines.append(f"<b>{idx}. {sanitize_for_html(c['title'], 200)}</b>")
                lines.append(f"   📅 {c['date']} | 🔗 <a href=\"{sanitize_for_html(c['link'], 1000)}\">View PDF</a>\n")
            return "\n".join(lines)

        elif cmd == '/stats':
            total = self.db.get_total_count()
            cat_stats = self.db.get_category_stats()
            today_count = len(self.db.get_todays_circulars())
            
            lines = [
                "📊 <b>GTU Automation Bot Statistics:</b>",
                "━━━━━━━━━━━━━━━━━━━━━",
                f"📈 <b>Total Tracked Circulars:</b> {total}",
                f"📅 <b>Processed Today:</b> {today_count}",
                "\n📂 <b>Category Breakdown:</b>"
            ]
            for cat, count in cat_stats.items():
                lines.append(f"  • {cat}: {count}")
            lines.append("\n⚡ <i>System status: Active & Monitoring</i>")
            return "\n".join(lines)

        elif cmd == '/digest':
            todays = self.db.get_todays_circulars()
            if not todays:
                # Fallback to recent 5 if none today
                todays = self.db.get_recent_circulars(limit=5)
                header = "📋 <b>GTU Circulars Digest (Recent Updates):</b>\n"
            else:
                header = f"📋 <b>Today's GTU Circulars Digest ({len(todays)} new):</b>\n"

            lines = [header]
            for idx, c in enumerate(todays[:5], 1):
                tags = CircularTagger.extract_tags(c['title'])
                tag_str = f" [{', '.join(tags['courses'])}]" if tags['courses'] else ""
                lines.append(f"<b>{idx}. {sanitize_for_html(c['title'], 180)}</b>{tag_str}")
                lines.append(f"   🔗 <a href=\"{sanitize_for_html(c['link'], 1000)}\">PDF Link</a>\n")
            return "\n".join(lines)

        return ""

    def poll_once(self) -> int:
        """Fetch pending updates from Telegram and reply to commands."""
        if not self.bot_token:
            return 0

        url = f"{self.api_url}/getUpdates"
        params = {
            'offset': self.last_update_id + 1,
            'timeout': 10,
            'allowed_updates': ['message']
        }

        try:
            resp = requests.get(url, params=params, timeout=15)
            if resp.status_code != 200:
                return 0
            data = resp.json()
            if not data.get('ok'):
                return 0

            updates = data.get('result', [])
            processed = 0
            for u in updates:
                self.last_update_id = u['update_id']
                msg = u.get('message', {})
                text = msg.get('text', '')
                chat_id = str(msg.get('chat', {}).get('id', ''))
                
                if text.startswith('/') and chat_id:
                    reply = self.handle_command(text, chat_id)
                    if reply:
                        self.notifier.send_message(reply, chat_id=chat_id)
                        processed += 1
            return processed
        except Exception:
            return 0

    def start_polling(self):
        """Start infinite interactive polling loop."""
        print("🤖 Interactive Telegram Bot Listener started...")
        print("💡 Supported commands: /start, /latest, /search <kw>, /exams, /results, /fees, /stats, /digest")
        while True:
            try:
                self.poll_once()
                time.sleep(1.0)
            except KeyboardInterrupt:
                print("\n👋 Bot listener stopped.")
                break
            except Exception as e:
                time.sleep(3.0)
