import argparse
import sys
import time
from datetime import datetime
from typing import List, Dict

# Ensure UTF-8 output in Windows terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from config import Config
from database import Database
from scraper import Scraper
from notifier import TelegramNotifier


def matches_filter(title: str, filters: List[str]) -> bool:
    """Check if title matches any keyword in filters."""
    if not filters:
        return True
    t = title.lower()
    return any(f in t for f in filters)


def run_check(dry_run: bool = False, limit: int = 15) -> int:
    """
    Run one cycle of circular checking.
    Returns the count of newly detected and processed circulars.
    """
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🔍 Scanning GTU Website: {Config.GTU_CIRCULAR_URL} ...")
    
    db = Database()
    scraper = Scraper()
    notifier = TelegramNotifier()
    
    try:
        circulars = scraper.get_latest_circulars()
    except Exception as e:
        print(f"❌ Error scraping GTU portal: {e}")
        return 0

    print(f"📄 Found {len(circulars)} circulars on GTU portal.")
    
    # Identify new circulars (reverse list so oldest new circular is sent first)
    new_circulars: List[Dict] = []
    for c in reversed(circulars):
        if not db.is_processed(c['id']):
            if matches_filter(c['title'], Config.KEYWORD_FILTER):
                new_circulars.append(c)

    if not new_circulars:
        print("✅ No new circulars found. Everything is up to date.")
        return 0

    print(f"🚨 Detected {len(new_circulars)} new circular(s)!")
    
    # Cap to limit to avoid spamming if bot runs after long time
    to_send = new_circulars[:limit]
    if len(new_circulars) > limit:
        print(f"⚠️ Limiting notifications to the most recent {limit} items.")

    sent_count = 0
    for idx, c in enumerate(to_send, 1):
        print(f"\n[{idx}/{len(to_send)}] Processing: {c['title']} ({c['date']})")
        print(f"    Category: {c['category']}")
        print(f"    PDF Link: {c['link']}")

        if dry_run:
            print("    [DRY RUN] Message not sent to Telegram. Simulated DB record added.")
            db.add_circular(c)
            sent_count += 1
            continue

        # Send Telegram alert
        success, msg = notifier.send_circular_alert(c)
        if success:
            print("    ✅ Telegram alert sent successfully!")
            db.add_circular(c)
            sent_count += 1
            # Small delay between messages to respect Telegram limits
            time.sleep(1.5)
        else:
            print(f"    ❌ Failed to send Telegram alert: {msg}")

    print(f"\n🎯 Cycle complete. {sent_count} new circulars recorded & notified.")
    return sent_count


def init_database_silent():
    """
    Populate the database with all currently visible circulars
    WITHOUT sending notifications. Useful for initial fresh setup.
    """
    print("📦 Initializing database with current live circulars...")
    db = Database()
    scraper = Scraper()
    
    try:
        circulars = scraper.get_latest_circulars()
        added = 0
        for c in circulars:
            if db.add_circular(c):
                added += 1
        print(f"✅ Initialized database with {added} existing circulars. Future new circulars will trigger notifications.")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")


def daemon_mode():
    """Run continuous background monitoring loop with strict rate-limiting compliance."""
    safe_interval = max(Config.CHECK_INTERVAL_MINUTES, Config.MIN_CHECK_INTERVAL_MINUTES)
    interval_sec = safe_interval * 60
    print("=" * 60)
    print("🤖 GTU Circular Automation - Background Daemon Mode Active")
    print("⚖️ Legal & Safety Policy: Strict Public Notification Mode")
    print(f"⏱️ Polling Interval: Every {safe_interval} minutes (Server-Safe)")
    print(f"📁 Database: {Config.DB_PATH}")
    if Config.KEYWORD_FILTER:
        print(f"🔍 Keyword Filter: {', '.join(Config.KEYWORD_FILTER)}")
    else:
        print("🔍 Filter: Receiving ALL circulars")
    print("=" * 60)

    while True:
        try:
            run_check()
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped by user. Exiting...")
            break
        except Exception as e:
            print(f"⚠️ Unexpected error in daemon loop: {e}")

        print(f"\n😴 Sleeping for {safe_interval} minutes until next check...")
        try:
            time.sleep(interval_sec)
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped by user. Exiting...")
            break


def main():
    parser = argparse.ArgumentParser(description="GTU Circular to Telegram Automation")
    parser.add_argument('--check', action='store_true', help="Run single check cycle and exit (for cron / GitHub Actions)")
    parser.add_argument('--daemon', action='store_true', help="Run continuous background loop")
    parser.add_argument('--dry-run', action='store_true', help="Scrape without sending real Telegram messages")
    parser.add_argument('--init-db', action='store_true', help="Mark current circulars as read without sending alerts")
    parser.add_argument('--test-telegram', action='store_true', help="Send a test message to verify Telegram setup")
    parser.add_argument('--limit', type=int, default=15, help="Max circulars to send in one run (default: 15)")

    args = parser.parse_args()

    if args.test_telegram:
        print("📡 Testing Telegram Bot Connection...")
        is_valid, msg = Config.validate(require_telegram=True)
        if not is_valid:
            print(f"❌ Configuration error: {msg}")
            sys.exit(1)
        notifier = TelegramNotifier()
        ok, res = notifier.test_connection()
        if ok:
            print("✅ Test message sent successfully! Check your Telegram chat/group.")
        else:
            print(f"❌ Failed to send test message: {res}")
        return

    if args.init_db:
        init_database_silent()
        return

    if args.check:
        is_valid, msg = Config.validate(require_telegram=not args.dry_run)
        if not is_valid:
            print(f"❌ Configuration error: {msg}")
            print("💡 Tip: Run 'python setup_bot.py' to configure your Telegram bot credentials.")
            sys.exit(1)
        run_check(dry_run=args.dry_run, limit=args.limit)
        return

    if args.daemon:
        is_valid, msg = Config.validate(require_telegram=True)
        if not is_valid:
            print(f"❌ Configuration error: {msg}")
            print("💡 Tip: Run 'python setup_bot.py' to configure your Telegram bot credentials.")
            sys.exit(1)
        daemon_mode()
        return

    # Default action if no arguments provided:
    # If config missing, prompt setup; else run single check
    is_valid, _ = Config.validate(require_telegram=True)
    if not is_valid:
        print("⚠️ Telegram credentials not found.")
        print("👉 Running interactive setup wizard...\n")
        import setup_bot
        setup_bot.main()
    else:
        run_check(limit=args.limit)


if __name__ == '__main__':
    main()
