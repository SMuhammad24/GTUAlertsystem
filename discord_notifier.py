import os
import requests
from typing import Dict, Optional, Tuple, Any
from config import Config
from security import sanitize_text, is_safe_url, mask_secret
from tagger import CircularTagger
from extractor import DeadlineExtractor


class DiscordNotifier:
    """
    Discord Webhook Notifier for GTU Circular Alerts.
    Sends beautifully formatted Rich Embeds with color codes, branch badges, and direct PDF links.
    """

    CATEGORY_COLORS = {
        'Fee & Penalty': 0xE74C3C,          # Red
        'Exam & Timetable': 0x3498DB,        # Blue
        'Result': 0x2ECC71,                  # Green
        'Admission & Enrollment': 0xE67E22,  # Orange
        'Academics & Syllabus': 0x9B59B6,    # Purple
        'Student Support': 0xF1C40F,         # Yellow
        'General Circular': 0x34495E         # Dark Slate
    }

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = (webhook_url or os.getenv('DISCORD_WEBHOOK_URL', '')).strip()

    def is_configured(self) -> bool:
        """Check if Discord webhook is provided."""
        return bool(self.webhook_url and self.webhook_url.startswith('https://discord.com/api/webhooks/'))

    def format_embed(self, circular: Dict[str, Any]) -> Dict[str, Any]:
        """Create a structured Discord Embed object for a circular."""
        category = circular.get('category', 'General Circular')
        color = self.CATEGORY_COLORS.get(category, 0x34495E)
        
        title = sanitize_text(circular.get('title', 'GTU Circular'), max_length=250)
        date_str = sanitize_text(circular.get('date', 'Recent'), max_length=50)
        link = circular.get('link', Config.GTU_CIRCULAR_URL)
        
        # Tags and deadlines
        tags = CircularTagger.extract_tags(title)
        deadline_info = DeadlineExtractor.extract_info(title)
        
        fields = [
            {"name": "📅 Date", "value": date_str, "inline": True},
            {"name": "🏷️ Category", "value": category, "inline": True},
        ]

        if tags.get('courses') or tags.get('semesters'):
            course_str = ", ".join(tags['courses']) if tags['courses'] else "All Courses"
            sem_str = "Sem " + ", ".join(str(s) for s in tags['semesters']) if tags['semesters'] else ""
            tag_val = f"{course_str} {sem_str}".strip()
            fields.append({"name": "🎯 Target", "value": tag_val, "inline": True})

        if deadline_info.get('penalties') or deadline_info.get('dates'):
            deadline_lines = []
            if deadline_info.get('penalties'):
                deadline_lines.append(f"💰 **Late Fee:** {', '.join(deadline_info['penalties'])}")
            if deadline_info.get('dates'):
                deadline_lines.append(f"⏰ **Key Date:** {', '.join(deadline_info['dates'])}")
            fields.append({"name": "📌 Important Deadlines", "value": "\n".join(deadline_lines), "inline": False})

        fields.append({"name": "📄 Action", "value": f"[👉 Click to Download PDF]({link})", "inline": False})

        hashtag_str = " ".join(tags.get('hashtags', ['#GTU']))

        embed = {
            "title": f"📢 GTU Alert: {category}",
            "description": f"**{title}**\n\n`{hashtag_str}`",
            "url": link,
            "color": color,
            "fields": fields,
            "footer": {
                "text": "GTU Automation Bot • Official Public Notification",
                "icon_url": "https://www.gtu.ac.in/images/gtu_logo.png"
            }
        }
        return embed

    def send_circular_alert(self, circular: Dict[str, Any]) -> Tuple[bool, str]:
        """Send Discord webhook alert."""
        if not self.is_configured():
            return False, "Discord webhook URL is not configured or invalid."

        embed = self.format_embed(circular)
        payload = {
            "username": "GTU Circular Bot",
            "avatar_url": "https://www.gtu.ac.in/images/gtu_logo.png",
            "embeds": [embed]
        }

        try:
            resp = requests.post(self.webhook_url, json=payload, timeout=Config.REQUEST_TIMEOUT)
            if resp.status_code in [200, 204]:
                return True, "Discord alert sent successfully."
            return False, f"Discord Webhook error: HTTP {resp.status_code}"
        except requests.exceptions.RequestException as e:
            return False, f"Network error sending Discord alert: {e}"

    def test_connection(self) -> Tuple[bool, str]:
        """Send a test message to Discord."""
        if not self.is_configured():
            return False, "Discord webhook URL is not set."

        test_payload = {
            "username": "GTU Circular Bot",
            "embeds": [{
                "title": "✅ GTU Discord Alerts Connected!",
                "description": "Discord webhook alerts are now active for GTU circulars.",
                "color": 0x2ECC71,
                "footer": {"text": "GTU Automation"}
            }]
        }
        try:
            resp = requests.post(self.webhook_url, json=test_payload, timeout=Config.REQUEST_TIMEOUT)
            if resp.status_code in [200, 204]:
                return True, "Discord test alert sent successfully!"
            return False, f"Discord Webhook error: HTTP {resp.status_code}"
        except Exception as e:
            return False, f"Discord connection test failed: {e}"
