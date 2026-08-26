import unittest
import os
import tempfile
from pathlib import Path

from config import Config
from database import Database
from scraper import Scraper
from notifier import TelegramNotifier


class TestGTUAutomation(unittest.TestCase):

    def setUp(self):
        # Create a temporary database for testing
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
            'link': 'https://example.com/circular1.pdf',
            'category': 'Exam & Timetable',
            'is_important': False
        }

        # First insertion should return True
        self.assertTrue(self.db.add_circular(sample_circular))
        self.assertEqual(self.db.get_total_count(), 1)
        self.assertTrue(self.db.is_processed('test-12345'))

        # Second insertion of same item should return False
        self.assertFalse(self.db.add_circular(sample_circular))
        self.assertEqual(self.db.get_total_count(), 1)

    def test_categorization(self):
        scraper = Scraper()
        self.assertEqual(scraper.categorize("Circular regarding Term Fee Payment and Late Fine"), "Fee & Penalty")
        self.assertEqual(scraper.categorize("Winter 2026 Examination Schedule & Timetable"), "Exam & Timetable")
        self.assertEqual(scraper.categorize("Notification for Result Declaration of BE Sem-6"), "Result")
        self.assertEqual(scraper.categorize("Admission Process for ME 2026"), "Admission & Enrollment")
        self.assertEqual(scraper.categorize("Syllabus of Artificial Intelligence Semester 5"), "Academics & Syllabus")
        self.assertEqual(scraper.categorize("General Independence Day Celebration"), "General Circular")

    def test_message_formatting(self):
        notifier = TelegramNotifier(bot_token="dummy_token", chat_id="123456")
        sample_circular = {
            'id': 'hash1',
            'title': 'Notification regarding Exam Fee Penalty Deadline',
            'date': '25-Aug-2026',
            'link': 'https://s3.amazonaws.com/gtu/fee_notice.pdf',
            'category': 'Fee & Penalty'
        }
        msg = notifier.format_circular_message(sample_circular)
        self.assertIn("FEE & PENALTY ALERT", msg)
        self.assertIn("25-Aug-2026", msg)
        self.assertIn("Notification regarding Exam Fee Penalty Deadline", msg)
        self.assertIn("https://s3.amazonaws.com/gtu/fee_notice.pdf", msg)

    def test_live_gtu_scraper(self):
        scraper = Scraper()
        circulars = scraper.get_latest_circulars()
        print(f"\n[Scraper Test] Successfully extracted {len(circulars)} live circulars from GTU.")
        self.assertGreater(len(circulars), 0, "GTU circular list should not be empty")
        first = circulars[0]
        self.assertTrue(bool(first['title']))
        self.assertTrue(bool(first['link']))
        self.assertTrue(bool(first['date']))
        print(f"Sample circular parsed:\n  Title: {first['title']}\n  Date: {first['date']}\n  Category: {first['category']}\n  Link: {first['link']}")

    def test_compliance_and_safety_rules(self):
        """Test strict enforcement of legal & safety compliance rules."""
        # 1. Allowed public GTU URLs should pass
        is_safe, _ = Config.is_safe_public_url('https://www.gtu.ac.in/Circular.aspx')
        self.assertTrue(is_safe)

        # 2. Prohibited private/login/auth endpoints must be rejected
        is_safe_login, reason = Config.is_safe_public_url('https://www.gtu.ac.in/student_login.aspx')
        self.assertFalse(is_safe_login)
        self.assertIn("strictly prohibited", reason)

        is_safe_admin, _ = Config.is_safe_public_url('https://www.gtu.ac.in/admin/dashboard')
        self.assertFalse(is_safe_admin)

        # 3. Third-party or unknown domains must be rejected
        is_safe_unknown, reason = Config.is_safe_public_url('https://malicious-site.com/hack.pdf')
        self.assertFalse(is_safe_unknown)
        self.assertIn("not in the allowed public GTU domains", reason)

        # 4. Scraper initialization with unsafe URL must raise PermissionError
        with self.assertRaises(PermissionError):
            Scraper(url='https://www.gtu.ac.in/login')


if __name__ == '__main__':
    unittest.main()
