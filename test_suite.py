import unittest
import os
import tempfile
from pathlib import Path

from config import Config
from database import Database
from scraper import Scraper
from notifier import TelegramNotifier
from discord_notifier import DiscordNotifier
from tagger import CircularTagger
from extractor import DeadlineExtractor
from ai_summarizer import CircularSummarizer
from calendar_sync import CalendarSync
from translations import GujaratiTranslator
from voice_bulletin import VoiceBulletin
from telegram_bot import InteractiveTelegramBot
from web_server import GTUWebHandler
from security import (
    is_safe_url,
    is_valid_telegram_token,
    is_valid_chat_id,
    mask_secret,
    sanitize_text,
    sanitize_for_html,
    safe_db_path,
)


class TestGTUAutomation(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_db_path = Path(self.temp_dir.name) / 'test_circulars.db'
        self.db = Database(db_path=self.temp_db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_database_duplicate_prevention(self):
        sample_circular = {
            'id': 'test-12345',
            'title': 'GTU Exam Form Extension for Summer 2026',
            'date': '25-Aug-2026',
            'link': 'https://www.gtu.ac.in/circular1.pdf',
            'category': 'Exam & Timetable',
            'is_important': False
        }
        self.assertTrue(self.db.add_circular(sample_circular))
        self.assertEqual(self.db.get_total_count(), 1)
        self.assertTrue(self.db.is_processed('test-12345'))
        self.assertFalse(self.db.add_circular(sample_circular))
        self.assertEqual(self.db.get_total_count(), 1)

    def test_database_subscriptions(self):
        # Test adding subscriptions
        self.assertTrue(self.db.add_subscription("chat_user_1", "BE", 6))
        self.assertTrue(self.db.add_subscription("chat_user_2", "DIPLOMA", 0))
        
        # Test fetching
        subs = self.db.get_user_subscriptions("chat_user_1")
        self.assertEqual(len(subs), 1)
        self.assertEqual(subs[0]['course'], 'BE')
        self.assertEqual(subs[0]['semester'], 6)

        # Test matching
        matched_be6 = self.db.get_matching_subscribers(['BE'], [6])
        self.assertIn('chat_user_1', matched_be6)

        matched_dip = self.db.get_matching_subscribers(['DIPLOMA'], [4])
        self.assertIn('chat_user_2', matched_dip)

        # Test unsubscribe
        self.assertEqual(self.db.remove_subscription("chat_user_1", "BE", 6), 1)
        self.assertEqual(len(self.db.get_user_subscriptions("chat_user_1")), 0)

    def test_database_export_csv_json(self):
        self.db.add_circular({
            'title': 'BE Sem 6 Circular',
            'date': '28-Aug-2026',
            'link': 'https://gtu.ac.in/c1.pdf',
            'category': 'Exam & Timetable'
        })
        csv_str = self.db.export_to_csv()
        self.assertIn('BE Sem 6 Circular', csv_str)
        self.assertIn('Title,Date,Category', csv_str.replace(' ', ''))

        json_str = self.db.export_to_json()
        self.assertIn('BE Sem 6 Circular', json_str)

    def test_calendar_sync_url_and_ics(self):
        cal_url = CalendarSync.generate_google_calendar_url(
            "GTU BE Sem 6 Exam Form Last Date",
            "15-09-2026",
            "https://www.gtu.ac.in/notice.pdf"
        )
        self.assertIn("calendar.google.com", cal_url)
        self.assertIn("GTU+BE+Sem+6", cal_url.replace('%20', '+'))

        ics_content = CalendarSync.generate_ics(
            "GTU BE Sem 6 Exam Form Last Date",
            "15-09-2026",
            "https://www.gtu.ac.in/notice.pdf"
        )
        self.assertIn("BEGIN:VCALENDAR", ics_content)
        self.assertIn("GTU BE Sem 6 Exam Form Last Date", ics_content)

    def test_gujarati_translation(self):
        tags = {'courses': ['BE'], 'semesters': [6]}
        deadlines = {'penalties': ['₹500']}
        gu_text = GujaratiTranslator.get_gujarati_brief(
            "Circular for BE Sem 6 Late Fee",
            "Fee & Penalty",
            tags,
            deadlines
        )
        self.assertIn("ગુજરાતી સારાંશ", gu_text)
        self.assertIn("ફી અને લેટ ફી દંડ નોટિસ", gu_text)

    def test_voice_bulletin_script(self):
        circulars = [
            {'title': 'Notification for Result Declaration of BE Sem 6', 'date': '28-Aug-2026'}
        ]
        script = VoiceBulletin.generate_bulletin_script(circulars)
        self.assertIn("Hello GTU students", script)
        self.assertIn("Notification for Result", script)

    def test_circular_tagger(self):
        title = "Circular regarding Exam Form filling for B.E. Sem-6 and Sem-7 Regular & Remedial"
        tags = CircularTagger.extract_tags(title)
        self.assertIn('BE', tags['courses'])
        self.assertIn(6, tags['semesters'])
        self.assertIn(7, tags['semesters'])
        self.assertIn('#BE', tags['hashtags'])
        self.assertIn('#Sem6', tags['hashtags'])

    def test_deadline_extractor(self):
        text = "Submission of Exam Forms without penalty up to 15-09-2026 and with late fee Rs. 500 up to 20/09/2026"
        info = DeadlineExtractor.extract_info(text)
        self.assertTrue(info['has_deadline'])
        self.assertIn('₹500', info['penalties'])
        self.assertIn('15-09-2026', info['dates'])

    def test_interactive_bot_subscription_commands(self):
        bot = InteractiveTelegramBot(bot_token="1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ_1234567")
        bot.db = self.db

        # Test /subscribe BE 6
        sub_res = bot.handle_command("/subscribe BE 6", "user_100")
        self.assertIn("Subscribed successfully", sub_res)
        self.assertIn("BE Sem 6", sub_res)

        # Test /mysubscriptions
        my_subs = bot.handle_command("/mysubscriptions", "user_100")
        self.assertIn("BE", my_subs)

        # Test /unsubscribe BE 6
        unsub_res = bot.handle_command("/unsubscribe BE 6", "user_100")
        self.assertIn("Unsubscribed", unsub_res)

    def test_security_ssrf_prevention(self):
        allowed = ['www.gtu.ac.in', 'gtu.ac.in']
        safe, _ = is_safe_url('https://www.gtu.ac.in/Circular.aspx', allowed)
        self.assertTrue(safe)
        safe, _ = is_safe_url('http://127.0.0.1:8080/admin', allowed)
        self.assertFalse(safe)

    def test_init_database_silent(self):
        from main import init_database_silent
        # Verify function is importable and callable
        self.assertTrue(callable(init_database_silent))

    def test_otp_service(self):
        from otp_service import OTPService
        otp = OTPService.generate_otp('student@gtu.ac.in')
        self.assertEqual(len(otp), 4)
        self.assertTrue(otp.isdigit())

        # Test verification success
        verified, _ = OTPService.verify_otp('student@gtu.ac.in', otp)
        self.assertTrue(verified)

        # Test demo fallback code
        demo_ok, _ = OTPService.verify_otp('any@gtu.ac.in', '1234')
        self.assertTrue(demo_ok)


if __name__ == '__main__':
    unittest.main()
