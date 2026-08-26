import html
import time
import requests
from typing import Dict, Optional, Tuple
from config import Config


class TelegramNotifier:
    """Telegram Bot Notifier for sending GTU Circular alerts."""

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

    def format_circular_message(self, circular: Dict) -> str:
        """Create a clean, beautiful HTML formatted Telegram message."""
        category = circular.get('category', 'General Circular')
        header_tag = self.CATEGORY_EMOJIS.get(category, '📢 <b>GTU CIRCULAR UPDATE</b> 📌')
        
        safe_title = html.escape(circular.get('title', 'Untitled Circular'))
        date_str = html.escape(circular.get('date', 'Recent'))
        pdf_link = circular.get('link', Config.GTU_CIRCULAR_URL)
        
        message = (
            f"{header_tag}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 <b>Date:</b> {date_str}\n"
            f"🏷️ <b>Category:</b> {category}\n\n"
            f"📌 <b>Circular:</b>\n{safe_title}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔗 <a href=\"{pdf_link}\">👉 [ CLICK HERE TO VIEW / DOWNLOAD PDF ]</a>\n"
            f"🌐 <a href=\"{Config.GTU_CIRCULAR_URL}\">Official GTU Portal</a>\n\n"
            f"<i>⚡ Automated GTU Alert Bot</i>"
        )
        return message

    def send_message(self, text: str, parse_mode: str = "HTML") -> Tuple[bool, str]:
        """Send message to Telegram chat/group."""
        if not self.bot_token or not self.chat_id:
            return False, "Bot token or Chat ID is not configured."

        endpoint = f"{self.api_url}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': text,
            'parse_mode': parse_mode,
            'disable_web_page_preview': False
        }

        try:
            response = requests.post(endpoint, json=payload, timeout=20)
            res_data = response.json()
            if response.status_code == 200 and res_data.get('ok'):
                return True, "Message sent successfully"
            elif response.status_code == 429:
                # Rate limit hit, wait requested retry_after
                retry_after = res_data.get('parameters', {}).get('retry_after', 3)
                time.sleep(retry_after)
                # Retry once
                response = requests.post(endpoint, json=payload, timeout=20)
                if response.status_code == 200:
                    return True, "Message sent after retry"
            return False, f"Telegram API Error: {res_data.get('description', response.text)}"
        except requests.exceptions.RequestException as e:
            return False, f"Network error sending Telegram message: {e}"

    def send_circular_alert(self, circular: Dict) -> Tuple[bool, str]:
        """Format and send circular alert."""
        text = self.format_circular_message(circular)
        return self.send_message(text)

    def test_connection(self) -> Tuple[bool, str]:
        """Send a test message to verify Telegram configuration."""
        test_msg = (
            "🤖 <b>GTU Automation Bot Connected!</b>\n\n"
            "✅ <i>Congratulations! Aapka Telegram Bot successfully connect ho chuka hai.</i>\n"
            "Ab jab bhi GTU website par koi naya circular ya fee/exam update aayega, direct yahan notify ho jayega.\n\n"
            "⚡ <i>Stay updated & avoid late fee penalties!</i>"
        )
        return self.send_message(test_msg)
