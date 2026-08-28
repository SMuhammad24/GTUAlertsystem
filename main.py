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
from discord_notifier import DiscordNotifier
from tagger import CircularTagger
from extractor import DeadlineExtractor
from ai_summarizer import CircularSummarizer


def matches_filter(title: str, filters: List[str]) -> bool:
    """Check if title matches any keyword in filters."""
    if not filters:
        return True
    t = title.lower()
    return any(f in t for f in filters)


def run_check(dry_run: bool = False, limit: int = 15) -> int:
    """
    Run one cycle of circular checking.
    Processes, enriches with tags/deadlines, and sends multi-platform alerts.
    Returns the count of newly detected and processed circulars.
    """
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🔍 Scanning GTU Website: {Config.GTU_CIRCULAR_URL} ...")
    
    db = Database()
    scraper = Scraper()
    telegram_notifier = TelegramNotifier()
    discord_notifier = DiscordNotifier()
    
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
                # Enrich circular metadata
                tags = CircularTagger.extract_tags(c['title'])
                deadline_info = DeadlineExtractor.extract_info(c['title'])
                summary = CircularSummarizer.get_ai_summary(c['title'], c['category'], tags, deadline_info)
                
                c['tags'] = ", ".join(tags['hashtags'])
                c['summary'] = summary
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
        print(f"    Tags:     {c.get('tags')}")
        print(f"    PDF Link: {c['link']}")

        if dry_run:
            print("    [DRY RUN] Message simulated. Stored in DB.")
            db.add_circular(c)
            sent_count += 1
            continue

        # 1. Send Telegram alert
        tg_ok, tg_msg = telegram_notifier.send_circular_alert(c)
        if tg_ok:
            print("    ✅ Telegram alert sent successfully!")
        else:
            print(f"    ⚠️ Telegram notice skipped/failed: {tg_msg}")

        # 2. Send Discord alert (if configured)
        if discord_notifier.is_configured():
            dc_ok, dc_msg = discord_notifier.send_circular_alert(c)
            if dc_ok:
                print("    ✅ Discord embed alert sent successfully!")
            else:
                print(f"    ⚠️ Discord notice skipped/failed: {dc_msg}")

        # Record in database
        db.add_circular(c)
        sent_count += 1
        time.sleep(1.5)

    print(f"\n🎯 Cycle complete. {sent_count} new circulars recorded & notified.")
    return sent_count


def generate_digest(send_telegram: bool = False) -> str:
    """Generate a daily morning digest of recent updates & active deadlines."""
    db = Database()
    todays = db.get_todays_circulars()
    if not todays:
        todays = db.get_recent_circulars(limit=5)
        header = "🌅 <b>GTU Daily Bulletin (Recent Updates)</b>\n"
    else:
        header = f"🌅 <b>GTU Daily Bulletin ({len(todays)} New Notices Today)</b>\n"

    lines = [
        header,
        "━━━━━━━━━━━━━━━━━━━━━",
        f"📅 <b>Date:</b> {datetime.now().strftime('%d %B %Y')}\n"
    ]

    for idx, c in enumerate(todays[:6], 1):
        tags = CircularTagger.extract_tags(c['title'])
        course_badge = f" [<code>{', '.join(tags['courses'])}</code>]" if tags['courses'] else ""
        lines.append(f"<b>{idx}. {c['title']}</b>{course_badge}")
        lines.append(f"   🏷️ {c.get('category', 'General')} | 🔗 <a href=\"{c['link']}\">PDF Link</a>\n")

    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    lines.append("⚡ <i>Stay ahead of exam & fee deadlines with GTU Alert Bot!</i>")
    
    digest_text = "\n".join(lines)
    print("\n" + "=" * 50)
    print("📋 GENERATED DAILY DIGEST:")
    print("=" * 50)
    print(digest_text)
    print("=" * 50 + "\n")

    if send_telegram:
        notifier = TelegramNotifier()
        ok, msg = notifier.send_message(digest_text)
        if ok:
            print("✅ Digest successfully broadcasted to Telegram!")
        else:
            print(f"❌ Failed to send digest: {msg}")

    return digest_text


def init_database_silent():
    """Populate database with all currently visible circulars without sending notifications."""
    print("📦 Initializing database with current live circulars...")
    db = Database()
    scraper = Scraper()
    
    try:
        circulars = scraper.get_latest_circulars()
        added = 0
        for c in circulars:
            tags = CircularTagger.extract_tags(c['title'])
            c['tags'] = ", ".join(tags['hashtags'])
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
    print("🤖 GTU Circular Automation - Background Daemon Active")
    print(f"⏱️ Polling Interval: Every {safe_interval} minutes (Server-Safe)")
    print(f"📁 Database: {Config.DB_PATH}")
    if Config.KEYWORD_FILTER:
        print(f"🔍 Keyword Filter: {', '.join(Config.KEYWORD_FILTER)}")
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
    parser = argparse.ArgumentParser(description="GTU Circular to Telegram & Discord Automation Hub")
    parser.add_argument('--check', action='store_true', help="Run single check cycle and exit")
    parser.add_argument('--daemon', action='store_true', help="Run continuous background loop")
    parser.add_argument('--bot', action='store_true', help="Run interactive 2-way Telegram Bot listener (/latest, /search)")
    parser.add_argument('--web', action='store_true', help="Start modern Web Dashboard & REST/RSS API")
    parser.add_argument('--port', type=int, default=8080, help="Port for web dashboard (default: 8080)")
    parser.add_argument('--digest', action='store_true', help="Generate and print/send morning daily bulletin digest")
    parser.add_argument('--send-digest', action='store_true', help="Send generated digest to Telegram")
    parser.add_argument('--dry-run', action='store_true', help="Scrape without sending real messages")
    parser.add_argument('--search', type=str, help="Search circulars from database by keyword")
    parser.add_argument('--init-db', action='store_true', help="Mark current circulars as read without sending alerts")
    parser.add_argument('--test-telegram', action='store_true', help="Send a test message to verify Telegram setup")
    parser.add_argument('--discord-test', action='store_true', help="Send a test embed to verify Discord Webhook")
    parser.add_argument('--limit', type=int, default=15, help="Max circulars to send in one run (default: 15)")

    args = parser.parse_args()

    if args.discord_test:
        print("📡 Testing Discord Webhook Connection...")
        notifier = DiscordNotifier()
        ok, res = notifier.test_connection()
        if ok:
            print("✅ Discord test alert sent successfully!")
        else:
            print(f"❌ Discord test failed: {res}")
        return

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

    if args.search:
        db = Database()
        results = db.search_circulars(args.search, limit=args.limit)
        print(f"\n🔍 Search results for '{args.search}' ({len(results)} matches):")
        print("-" * 60)
        for idx, r in enumerate(results, 1):
            print(f"{idx}. [{r['date']}] {r['title']}")
            print(f"   Category: {r.get('category')} | Link: {r['link']}\n")
        return

    if args.digest:
        generate_digest(send_telegram=args.send_digest)
        return

    if args.bot:
        is_valid, msg = Config.validate(require_telegram=True)
        if not is_valid:
            print(f"❌ Telegram config error: {msg}")
            sys.exit(1)
        from telegram_bot import InteractiveTelegramBot
        bot = InteractiveTelegramBot()
        bot.start_polling()
        return

    if args.web:
        from web_server import run_server
        run_server(port=args.port, host=Config.WEB_HOST)
        return

    if args.init_db:
        init_database_silent()
        return

    if args.check:
        is_valid, msg = Config.validate(require_telegram=not args.dry_run)
        if not is_valid:
            print(f"❌ Configuration error: {msg}")
            sys.exit(1)
        run_check(dry_run=args.dry_run, limit=args.limit)
        return

    if args.daemon:
        is_valid, msg = Config.validate(require_telegram=True)
        if not is_valid:
            print(f"❌ Configuration error: {msg}")
            sys.exit(1)
        daemon_mode()
        return

    # Default action: single check
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
