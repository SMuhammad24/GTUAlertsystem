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

    def test_database_search_and_stats(self):
        items = [
            {'title': 'BE Sem 6 Remedial Exam Form', 'date': '26-Aug-2026', 'link': 'https://gtu.ac.in/1.pdf', 'category': 'Exam & Timetable'},
            {'title': 'Diploma Fee Payment with late fine', 'date': '26-Aug-2026', 'link': 'https://gtu.ac.in/2.pdf', 'category': 'Fee & Penalty'},
            {'title': 'MBA Results Declared Sem 2', 'date': '26-Aug-2026', 'link': 'https://gtu.ac.in/3.pdf', 'category': 'Result'},
        ]
        for item in items:
            self.db.add_circular(item)

        self.assertEqual(self.db.get_total_count(), 3)
        
        # Test search
        res = self.db.search_circulars('Diploma')
        self.assertEqual(len(res), 1)
        self.assertIn('Diploma', res[0]['title'])

        # Test category filter
        exam_list = self.db.get_circulars_by_category('Exam')
        self.assertEqual(len(exam_list), 1)

        # Test category stats
        stats = self.db.get_category_stats()
        self.assertEqual(stats.get('Fee & Penalty'), 1)
        self.assertEqual(stats.get('Result'), 1)

    def test_circular_tagger(self):
        # 1. Test BE & Semester 6 detection
        title1 = "Circular regarding Exam Form filling for B.E. Sem-6 and Sem-7 Regular & Remedial"
        tags1 = CircularTagger.extract_tags(title1)
        self.assertIn('BE', tags1['courses'])
        self.assertIn(6, tags1['semesters'])
        self.assertIn(7, tags1['semesters'])
        self.assertIn('Regular', tags1['exam_types'])
        self.assertIn('Remedial', tags1['exam_types'])
        self.assertIn('#BE', tags1['hashtags'])
        self.assertIn('#Sem6', tags1['hashtags'])

        # 2. Test Diploma & MBA detection
        title2 = "Diploma Engineering Sem 4 and MBA Summer 2026 Timetable"
        tags2 = CircularTagger.extract_tags(title2)
        self.assertIn('Diploma', tags2['courses'])
        self.assertIn('MBA', tags2['courses'])
        self.assertIn(4, tags2['semesters'])
        self.assertIn('#Diploma', tags2['hashtags'])
        self.assertIn('#MBA', tags2['hashtags'])

    def test_deadline_extractor(self):
        text = "Submission of Exam Forms without penalty up to 15-09-2026 and with late fee Rs. 500 up to 20/09/2026"
        info = DeadlineExtractor.extract_info(text)
        self.assertTrue(info['has_deadline'])
        self.assertIn('₹500', info['penalties'])
        self.assertIn('15-09-2026', info['dates'])
        self.assertIn('20/09/2026', info['dates'])
        
        badge = DeadlineExtractor.format_deadline_badge(info)
        self.assertIsNotNone(badge)
        self.assertIn('Late Fee', badge)

    def test_ai_heuristic_summarizer(self):
        title = "Circular regarding exam fees submission for B.E. Sem 6 students with late fine Rs. 500"
        tags = CircularTagger.extract_tags(title)
        deadlines = DeadlineExtractor.extract_info(title)
        summary = CircularSummarizer.get_heuristic_summary(title, "Fee & Penalty", tags, deadlines)
        
        self.assertTrue(len(summary) > 10)
        self.assertIn("fee", summary.lower())
        self.assertIn("BE", summary)

    def test_discord_notifier_embed_structure(self):
        notifier = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/123/abc")
        self.assertTrue(notifier.is_configured())
        
        sample_circular = {
            'title': 'B.E. Sem-4 Remedial Examination Schedule',
            'date': '27-Aug-2026',
            'link': 'https://www.gtu.ac.in/exam_notice.pdf',
            'category': 'Exam & Timetable'
        }
        embed = notifier.format_embed(sample_circular)
        self.assertIn('Exam & Timetable', embed['title'])
        self.assertEqual(embed['color'], DiscordNotifier.CATEGORY_COLORS['Exam & Timetable'])
        self.assertTrue(any('#BE' in embed['description'] for _ in [1]))

    def test_interactive_telegram_bot_commands(self):
        bot = InteractiveTelegramBot(bot_token="1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ_1234567")
        bot.db = self.db

        # Seed test data
        self.db.add_circular({
            'title': 'BE Sem 6 Result Declared',
            'date': '28-Aug-2026',
            'link': 'https://www.gtu.ac.in/res.pdf',
            'category': 'Result'
        })

        # Test /start command
        start_res = bot.handle_command("/start", "12345")
        self.assertIn("Welcome to GTU Circular Automation Bot", start_res)

        # Test /latest command
        latest_res = bot.handle_command("/latest", "12345")
        self.assertIn("BE Sem 6 Result Declared", latest_res)

        # Test /search command
        search_res = bot.handle_command("/search BE", "12345")
        self.assertIn("BE Sem 6 Result Declared", search_res)

        # Test /stats command
        stats_res = bot.handle_command("/stats", "12345")
        self.assertIn("Total Tracked Circulars", stats_res)

    def test_rss_feed_generation(self):
        handler = GTUWebHandler
        items = [{
            'id': 'cid-1',
            'title': 'GTU Timetable Notification 2026',
            'link': 'https://www.gtu.ac.in/tt.pdf',
            'category': 'Exam & Timetable',
            'date': '28-Aug-2026'
        }]
        xml_str = handler._generate_rss(None, items)
        self.assertIn('<rss version="2.0">', xml_str)
        self.assertIn('GTU Timetable Notification 2026', xml_str)
        self.assertIn('https://www.gtu.ac.in/tt.pdf', xml_str)

    def test_categorization(self):
        scraper = Scraper()
        self.assertEqual(scraper.categorize("Circular regarding Term Fee Payment and Late Fine"), "Fee & Penalty")
        self.assertEqual(scraper.categorize("Winter 2026 Examination Schedule & Timetable"), "Exam & Timetable")
        self.assertEqual(scraper.categorize("Notification for Result Declaration of BE Sem-6"), "Result")
        self.assertEqual(scraper.categorize("Admission Process for ME 2026"), "Admission & Enrollment")
        self.assertEqual(scraper.categorize("Syllabus of Artificial Intelligence Semester 5"), "Academics & Syllabus")
        self.assertEqual(scraper.categorize("General Independence Day Celebration"), "General Circular")

    def test_message_formatting_and_xss_protection(self):
        notifier = TelegramNotifier(bot_token="1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ_1234567", chat_id="123456")
        malicious_circular = {
            'id': 'hash_malicious',
            'title': 'GTU Notice for BE Sem 6 <script>alert("hacked")</script> & <b>bold</b> "quotes"',
            'date': '25-Aug-2026',
            'link': 'https://www.gtu.ac.in/fee_notice.pdf',
            'category': 'Fee & Penalty'
        }
        msg = notifier.format_circular_message(malicious_circular)
        self.assertNotIn('<script>', msg)
        self.assertIn('&lt;script&gt;', msg)
        self.assertIn('&quot;quotes&quot;', msg)
        self.assertIn("FEE & PENALTY ALERT", msg)
        self.assertIn("#BE", msg)

    def test_security_ssrf_prevention(self):
        allowed = ['www.gtu.ac.in', 'gtu.ac.in']
        safe, _ = is_safe_url('https://www.gtu.ac.in/Circular.aspx', allowed)
        self.assertTrue(safe)
        safe, reason = is_safe_url('http://127.0.0.1:8080/admin', allowed)
        self.assertFalse(safe)
        safe, _ = is_safe_url('http://169.254.169.254/latest/meta-data/', allowed)
        self.assertFalse(safe)
        safe, _ = is_safe_url('javascript:alert(1)', allowed)
        self.assertFalse(safe)
        safe, _ = is_safe_url('file:///etc/passwd', allowed)
        self.assertFalse(safe)

    def test_security_token_and_chat_id_validation(self):
        self.assertTrue(is_valid_telegram_token('1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ_1234567'))
        self.assertFalse(is_valid_telegram_token('invalid_token'))
        self.assertTrue(is_valid_chat_id('123456789'))
        self.assertTrue(is_valid_chat_id('-1001234567890'))
        self.assertTrue(is_valid_chat_id('@my_gtu_channel'))
        self.assertFalse(is_valid_chat_id('abc'))

    def test_security_secret_masking(self):
        raw_token = '1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ_1234567'
        masked = mask_secret(raw_token)
        self.assertNotIn(raw_token, masked)
        self.assertTrue(masked.startswith('1234...'))
        self.assertTrue(masked.endswith('4567'))


if __name__ == '__main__':
    unittest.main()
