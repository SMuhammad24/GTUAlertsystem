import sys
import time
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

# Ensure UTF-8 output on Windows terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from config import Config
from database import Database
from notifier import TelegramNotifier
from tagger import CircularTagger
from extractor import DeadlineExtractor
from voice_bulletin import VoiceBulletin
from security import sanitize_for_html, sanitize_text, mask_secret


class InteractiveTelegramBot:
    """
    Interactive 2-Way Telegram Bot listener for GTU Circulars.
    Handles student commands:
      /start, /help, /latest, /search, /exams, /results, /fees, /stats, /digest
      /subscribe <course> [sem], /unsubscribe <course> [sem], /mysubscriptions, /voice
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
        
        cmd = parts[0].lower().split('@')[0]
        args = parts[1:] if len(parts) > 1 else []

        if cmd in ['/start', '/help']:
            return (
                "🤖 <b>Welcome to GTU Circular Automation Bot!</b>\n\n"
                "Aap yahan GTU ke official circulars, exam timetables, results aur fee deadlines dekh sakte hain.\n\n"
                "📌 <b>Commands Menu:</b>\n"
                "🔹 <code>/ask &lt;sawal&gt;</code> - 🤖 Ask GTU AI Assistant (Natural Language Q&amp;A)\n"
                "🔹 <code>/latest [n]</code> - Pichle 5 ya N naye circulars\n"
                "🔹 <code>/search &lt;query&gt;</code> - Instant search (e.g. <code>/search fee</code>)\n"
                "🔹 <code>/exams</code> - Exam & Timetable updates\n"
                "🔹 <code>/results</code> - Result declarations\n"
                "🔹 <code>/fees</code> - Fee & Penalty notices\n"
                "🔹 <code>/stats</code> - Database statistics\n"
                "🔹 <code>/digest</code> - Daily morning bulletin\n"
                "🔹 <code>/voice</code> - 30-sec audio news bulletin\n\n"
                "🎯 <b>Personalized Subscriptions (Zero Spam):</b>\n"
                "🔹 <code>/subscribe BE 6</code> - Sirf BE Sem 6 alerts paayein\n"
                "🔹 <code>/subscribe Diploma</code> - Diploma ke alerts paayein\n"
                "🔹 <code>/mysubscriptions</code> - Apni active subscriptions dekhein\n"
                "🔹 <code>/unsubscribe BE 6</code> - Unsubscribe karein\n\n"
                "⚡ <i>Auto-alerts & Google Calendar reminders active!</i>"
            )

        elif cmd == '/subscribe':
            if not args:
                return (
                    "⚠️ <b>Usage:</b> <code>/subscribe &lt;Course&gt; [Semester]</code>\n"
                    "Examples:\n"
                    "• <code>/subscribe BE 6</code>\n"
                    "• <code>/subscribe Diploma 4</code>\n"
                    "• <code>/subscribe MBA</code>\n"
                    "• <code>/subscribe BPharm 2</code>"
                )
            course = args[0].upper()
            sem = int(args[1]) if len(args) > 1 and args[1].isdigit() else 0
            
            ok = self.db.add_subscription(chat_id, course, sem)
            sem_str = f" Sem {sem}" if sem > 0 else " (All Semesters)"
            if ok:
                return f"✅ <b>Subscribed successfully!</b>\nAapko <b>{course}{sem_str}</b> ke circular aane par direct personalized alert milega."
            else:
                return f"ℹ️ Aap pehle se hi <b>{course}{sem_str}</b> ke liye subscribed hain."

        elif cmd == '/unsubscribe':
            if not args:
                return "⚠️ <b>Usage:</b> <code>/unsubscribe &lt;Course&gt; [Semester]</code>\nExample: <code>/unsubscribe BE 6</code>"
            course = args[0].upper()
            sem = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
            count = self.db.remove_subscription(chat_id, course, sem)
            if count > 0:
                return f"✅ <b>Unsubscribed!</b> {course} ke alerts hata diye gaye hain."
            return f"ℹ️ {course} ki koi active subscription nahi mili."

        elif cmd == '/mysubscriptions':
            subs = self.db.get_user_subscriptions(chat_id)
            if not subs:
                return "ℹ️ Aapne abhi koi specific course subscribe nahi kiya hai.\nSubscribe karne ke liye likhein: <code>/subscribe BE 6</code>"
            lines = ["🎯 <b>Aapki Active Subscriptions:</b>\n"]
            for idx, s in enumerate(subs, 1):
                sem_str = f"Sem {s['semester']}" if s['semester'] > 0 else "All Semesters"
                lines.append(f"{idx}. <b>{s['course']}</b> ({sem_str})")
            lines.append("\nUnsubscribe karne ke liye: <code>/unsubscribe &lt;Course&gt;</code>")
            return "\n".join(lines)

        elif cmd == '/voice':
            circulars = self.db.get_todays_circulars() or self.db.get_recent_circulars(limit=3)
            script = VoiceBulletin.generate_bulletin_script(circulars)
            return (
                "🎙️ <b>GTU Daily 30-Second Voice News Script:</b>\n\n"
                f"<i>\"{sanitize_for_html(script, max_length=500)}\"</i>\n\n"
                "💡 <i>Audio synthesis active.</i>"
            )

        elif cmd == '/ask':
            if not args:
                return (
                    "🤖 <b>Ask GTU AI Assistant</b>\n\n"
                    "Aap mujhse GTU circulars ya deadlines ke baare mein natural language mein pooch sakte hain!\n"
                    "<b>Usage:</b> <code>/ask &lt;aapka sawal&gt;</code>\n\n"
                    "<b>Examples:</b>\n"
                    "• <code>/ask when is the ME dissertation deadline?</code>\n"
                    "• <code>/ask Pharmacy recheck result updates</code>\n"
                    "• <code>/ask show exam fee penalty</code>"
                )
            query = " ".join(args).strip()
            circulars = self.db.get_recent_circulars(limit=75)
            q_lower = query.lower()
            tokens = [t for t in q_lower.replace('?', '').replace('!', '').split() if len(t) > 1]

            best_c = None
            best_score = -1
            for c in circulars:
                score = 0
                title_lower = c['title'].lower()
                for tok in tokens:
                    if tok in title_lower:
                        score += 10
                if 'me' in q_lower and ('me ' in title_lower or 'me(' in title_lower):
                    score += 25
                if 'diploma' in q_lower and 'diploma' in title_lower:
                    score += 25
                if 'pharmacy' in q_lower and 'pharm' in title_lower:
                    score += 25
                if 'dissertation' in q_lower and 'dissertation' in title_lower:
                    score += 30
                if 'result' in q_lower and ('result' in title_lower or c.get('category') == 'Result'):
                    score += 15
                if score > best_score:
                    best_score = score
                    best_c = c

            if best_c and best_score >= 8:
                tags = CircularTagger.extract_tags(best_c['title'])
                deadlines = DeadlineExtractor.extract_info(best_c['title'])
                from ai_summarizer import CircularSummarizer
                summary = CircularSummarizer.get_ai_summary(
                    best_c['title'],
                    best_c.get('category', 'General'),
                    tags,
                    deadlines
                )
                dates = deadlines.get('dates', [])
                dates_str = f"\n⏰ <b>Key Dates / Deadline:</b> <code>{', '.join(dates)}</code>" if dates else ""

                return (
                    f"🤖 <b>GTU AI Verified Answer:</b>\n\n"
                    f"📄 <b>Official Notice:</b>\n<a href=\"{best_c['link']}\">{sanitize_for_html(best_c['title'])}</a>\n\n"
                    f"📅 <b>Published:</b> {best_c.get('date', 'Recent')}"
                    f"{dates_str}\n\n"
                    f"💡 <b>AI Summary:</b>\n{sanitize_for_html(summary)}\n\n"
                    f"🔗 <a href=\"{best_c['link']}\">Click here to open Official PDF</a>"
                )
            else:
                return (
                    f"🤖 <b>GTU AI Assistant:</b>\n\n"
                    f"Mujhe aapke sawal (<i>\"{sanitize_for_html(query)}\"</i>) ke liye direct circular nahi mila.\n"
                    f"Aap <code>/latest</code> se recent circulars dekh sakte hain ya keyword se <code>/search</code> kar sakte hain."
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
            todays = self.db.get_todays_circulars() or self.db.get_recent_circulars(limit=5)
            header = f"📋 <b>GTU Circulars Digest ({len(todays)} updates):</b>\n"

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
        print("💡 Supported: /start, /subscribe, /unsubscribe, /mysubscriptions, /voice, /latest, /search, /stats")
        while True:
            try:
                self.poll_once()
                time.sleep(1.0)
            except KeyboardInterrupt:
                print("\n👋 Bot listener stopped.")
                break
            except Exception:
                time.sleep(3.0)
