import time
import requests
from typing import Dict, Optional, Tuple, Any
from config import Config
from security import sanitize_for_html, sanitize_text, is_safe_url, mask_secret
from tagger import CircularTagger
from extractor import DeadlineExtractor
from ai_summarizer import CircularSummarizer


class TelegramNotifier:
    """Telegram Bot Notifier for sending rich, secure GTU Circular alerts."""

    CATEGORY_EMOJIS = {
        'Fee & Penalty': '🚨 <b>FEE & PENALTY ALERT</b> 💰',
        'Exam & Timetable': '📝 <b>EXAM & TIMETABLE UPDATE</b> ⏰',
        'Result': '📊 <b>RESULT DECLARATION</b> 🏆',
        'Admission & Enrollment': '🎓 <b>ADMISSION & ENROLLMENT</b> 📋',
        'Academics & Syllabus': '📚 <b>ACADEMICS & SYLLABUS</b> 📖',
        'Student Support': '🌟 <b>STUDENT SUPPORT / SCHOLARSHIP</b> 🎯',
        'General Circular': '📢 <b>GTU CIRCULAR UPDATE</b> 📌'
    }

    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.bot_token = (bot_token or Config.TELEGRAM_BOT_TOKEN).strip()
        self.chat_id = (chat_id or Config.TELEGRAM_CHAT_ID).strip()
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"

    def format_circular_message(self, circular: Dict[str, Any], include_summary: bool = True) -> str:
        """Create a clean, feature-rich HTML-escaped Telegram message."""
        raw_category = circular.get('category', 'General Circular')
        category = sanitize_text(raw_category, max_length=50)
        header_tag = self.CATEGORY_EMOJIS.get(category, '📢 <b>GTU CIRCULAR UPDATE</b> 📌')
        
        raw_title = circular.get('title', 'Untitled Circular')
        safe_title = sanitize_for_html(raw_title, max_length=400)
        date_str = sanitize_for_html(circular.get('date', 'Recent'), max_length=50)
        
        # Tags & Hashtags
        tags = CircularTagger.extract_tags(raw_title)
        hashtag_str = sanitize_for_html(CircularTagger.format_hashtag_string(tags), max_length=200)
        
        # Deadlines & Penalties
        deadline_info = DeadlineExtractor.extract_info(raw_title)
        deadline_badge = DeadlineExtractor.format_deadline_badge(deadline_info)
        
        raw_link = circular.get('link', Config.GTU_CIRCULAR_URL)
        is_safe, _ = is_safe_url(raw_link, allowed_domains=Config.ALLOWED_DOMAINS)
        pdf_link = raw_link if is_safe else Config.GTU_CIRCULAR_URL
        safe_pdf_link = sanitize_for_html(pdf_link, max_length=1000)
        safe_portal_url = sanitize_for_html(Config.GTU_CIRCULAR_URL, max_length=500)

        # Target courses/semester badge if available
        target_parts = []
        if tags['courses']:
            target_parts.append(f"🎓 <b>Course:</b> {', '.join(tags['courses'])}")
        if tags['semesters']:
            target_parts.append(f"📚 <b>Sem:</b> {', '.join(str(s) for s in tags['semesters'])}")
        target_badge = "\n".join(target_parts)

        # Summary line
        summary_block = ""
        if include_summary:
            summary_text = CircularSummarizer.get_heuristic_summary(raw_title, category, tags, deadline_info)
            safe_summary = sanitize_for_html(summary_text, max_length=300)
            summary_block = f"\n💡 <i>TL;DR: {safe_summary}</i>\n"
        
        msg_parts = [
            header_tag,
            "━━━━━━━━━━━━━━━━━━━━━",
            f"📅 <b>Date:</b> {date_str}",
            f"🏷️ <b>Category:</b> {category}",
        ]
        
        if target_badge:
            msg_parts.append(target_badge)
            
        msg_parts.extend([
            "",
            f"📌 <b>Circular:</b>\n{safe_title}",
        ])

        if deadline_badge:
            msg_parts.extend(["", deadline_badge])

        if summary_block:
            msg_parts.append(summary_block)

        msg_parts.extend([
            "━━━━━━━━━━━━━━━━━━━━━",
            f"🔗 <a href=\"{safe_pdf_link}\">👉 [ CLICK HERE TO VIEW / DOWNLOAD PDF ]</a>",
            f"🌐 <a href=\"{safe_portal_url}\">Official GTU Portal</a>",
            f"\n<code>{hashtag_str}</code>",
            f"\n<i>⚡ Automated GTU Alert Bot</i>"
        ])

        return "\n".join(msg_parts)

    def send_message(self, text: str, parse_mode: str = "HTML", chat_id: Optional[str] = None) -> Tuple[bool, str]:
        """Send message to Telegram chat/group with masked error logging."""
        target_chat = (chat_id or self.chat_id).strip()
        if not self.bot_token or not target_chat:
            return False, "Bot token or Chat ID is not configured."

        endpoint = f"{self.api_url}/sendMessage"
        payload = {
            'chat_id': target_chat,
            'text': text,
            'parse_mode': parse_mode,
            'disable_web_page_preview': False
        }

        try:
            response = requests.post(endpoint, json=payload, timeout=Config.REQUEST_TIMEOUT, verify=True)
            res_data = response.json()
            if response.status_code == 200 and res_data.get('ok'):
                return True, "Message sent successfully"
            elif response.status_code == 429:
                retry_after = res_data.get('parameters', {}).get('retry_after', 3)
                time.sleep(retry_after)
                response = requests.post(endpoint, json=payload, timeout=Config.REQUEST_TIMEOUT, verify=True)
                if response.status_code == 200:
                    return True, "Message sent after retry"
            
            raw_err = res_data.get('description', 'Unknown Telegram Error')
            redacted_err = raw_err.replace(self.bot_token, mask_secret(self.bot_token))
            return False, f"Telegram API Error: {redacted_err}"
        except requests.exceptions.RequestException as e:
            err_str = str(e).replace(self.bot_token, mask_secret(self.bot_token))
            return False, f"Network error sending Telegram message: {err_str}"

    def send_circular_alert(self, circular: Dict[str, Any]) -> Tuple[bool, str]:
        """Format and send circular alert."""
        text = self.format_circular_message(circular)
        return self.send_message(text)

    def test_connection(self) -> Tuple[bool, str]:
        """Send a test message to verify Telegram configuration."""
        test_msg = (
            "🤖 <b>GTU Automation Bot Connected!</b>\n\n"
            "✅ <i>Congratulations! Aapka Telegram Bot successfully connect ho chuka hai.</i>\n"
            "Ab jab bhi GTU website par koi naya circular ya fee/exam update aayega, direct yahan notify ho jayega.\n\n"
            "💡 <b>Features active:</b>\n"
            "• Smart Tagging (#BE #Diploma #Sem4)\n"
            "• Important Date & Penalty Extractor\n"
            "• Interactive 2-way bot commands (/latest, /search)\n\n"
            "⚡ <i>Stay updated & avoid late fee penalties!</i>"
        )
        return self.send_message(test_msg)
