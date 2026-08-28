import argparse
import sys
import time
from datetime import datetime
from pathlib import Path
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
from voice_bulletin import VoiceBulletin
from pdf_inspector import PDFInspector


def matches_filter(title: str, filters: List[str]) -> bool:
    """Check if title matches any keyword in filters."""
    if not filters:
        return True
    t = title.lower()
    return any(f in t for f in filters)


def run_check(dry_run: bool = False, limit: int = 15) -> int:
    """
    Run one cycle of circular checking.
    Enriches with tags, deadlines, sends channel broadcast and personalized subscriber DMs.
    Zero extra server load: only queries public notice board at safe intervals.
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
    
    new_circulars: List[Dict] = []
    for c in reversed(circulars):
        if not db.is_processed(c['id']):
            if matches_filter(c['title'], Config.KEYWORD_FILTER):
                tags = CircularTagger.extract_tags(c['title'])
                deadline_info = DeadlineExtractor.extract_info(c['title'])
                summary = CircularSummarizer.get_ai_summary(c['title'], c['category'], tags, deadline_info)
                
                c['tags'] = ", ".join(tags['hashtags'])
                c['summary'] = summary
                c['courses'] = tags['courses']
                c['semesters'] = tags['semesters']
                new_circulars.append(c)

    if not new_circulars:
        print("✅ No new circulars found. Everything is up to date.")
        return 0

    print(f"🚨 Detected {len(new_circulars)} new circular(s)!")
    to_send = new_circulars[:limit]

    sent_count = 0
    for idx, c in enumerate(to_send, 1):
        print(f"\n[{idx}/{len(to_send)}] Processing: {c['title']} ({c['date']})")
        print(f"    Category: {c['category']}")
        print(f"    Tags:     {c.get('tags')}")

        if dry_run:
            print("    [DRY RUN] Message simulated. Stored in DB.")
            db.add_circular(c)
            sent_count += 1
            continue

        # 1. Main Broadcast Alert
        tg_ok, tg_msg = telegram_notifier.send_circular_alert(c)
        if tg_ok:
            print("    ✅ Telegram main broadcast alert sent successfully!")
        else:
            print(f"    ⚠️ Telegram notice skipped/failed: {tg_msg}")

        # 2. Personalized Subscriber DM Alerts (Zero spam)
        courses = c.get('courses', [])
        semesters = c.get('semesters', [])
        subscribers = db.get_matching_subscribers(courses, semesters)
        if subscribers:
            print(f"    🎯 Notifying {len(subscribers)} subscribed student(s) directly...")
            for sub_chat in subscribers:
                if sub_chat != Config.TELEGRAM_CHAT_ID:
                    telegram_notifier.send_message(
                        f"🔔 <b>Personalized Alert for your branch:</b>\n\n" + telegram_notifier.format_circular_message(c),
                        chat_id=sub_chat
                    )
                    time.sleep(0.5)

        # 3. Discord Alert (if configured)
        if discord_notifier.is_configured():
            dc_ok, dc_msg = discord_notifier.send_circular_alert(c)
            if dc_ok:
                print("    ✅ Discord embed alert sent successfully!")

        db.add_circular(c)
        sent_count += 1
        if tg_ok:
            time.sleep(1.5)

    print(f"\n🎯 Cycle complete. {sent_count} new circulars recorded & notified.")
    export_static_json()
    return sent_count


def export_static_json():
    """Export circulars and stats to web/data.json for zero-server GitHub Pages static hosting."""
    try:
        db = Database()
        circulars = db.get_recent_circulars(limit=200)
        enriched = []
        for r in circulars:
            tags = CircularTagger.extract_tags(r['title'])
            deadlines = DeadlineExtractor.extract_info(r['title'])
            item = dict(r)
            item['tags'] = ", ".join(tags['hashtags'])
            item['courses'] = tags['courses']
            item['semesters'] = tags['semesters']
            item['deadlines'] = deadlines['dates']
            item['penalties'] = deadlines['penalties']
            enriched.append(item)
            
        stats = {
            'total': db.get_total_count(),
            'today': len(db.get_todays_circulars()),
            'categories': db.get_category_stats(),
            'status': 'online',
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        data = {'stats': stats, 'circulars': enriched}
        out_file = Config.BASE_DIR / 'web' / 'data.json'
        with open(out_file, 'w', encoding='utf-8') as f:
            import json
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Warning: Could not export web/data.json: {e}")


def init_database_silent(limit: int = 50) -> int:
    """
    Initialize database silently with current GTU circulars to prevent spamming old notices on first launch.
    """
    print("📥 Initializing database with existing circulars (no alerts will be sent)...")
    count = run_check(dry_run=True, limit=limit)
    print(f"✅ Initialized {count} existing circulars in database.")
    return count


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


def daemon_mode():
    """Run continuous background monitoring loop with strict rate-limiting compliance."""
    safe_interval = max(Config.CHECK_INTERVAL_MINUTES, Config.MIN_CHECK_INTERVAL_MINUTES)
    interval_sec = safe_interval * 60
    print("=" * 60)
    print("🤖 GTU Circular Automation - Background Daemon Active")
    print(f"⏱️ Polling Interval: Every {safe_interval} minutes (Server-Safe)")
    print(f"📁 Database: {Config.DB_PATH}")
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
    parser.add_argument('--bot', action='store_true', help="Run interactive 2-way Telegram Bot (/subscribe, /latest, /search)")
    parser.add_argument('--web', action='store_true', help="Start modern Web Dashboard & REST/RSS API")
    parser.add_argument('--port', type=int, default=8080, help="Port for web dashboard (default: 8080)")
    parser.add_argument('--digest', action='store_true', help="Generate daily morning bulletin")
    parser.add_argument('--send-digest', action='store_true', help="Send generated digest to Telegram")
    parser.add_argument('--voice', action='store_true', help="Generate 30-sec daily spoken audio bulletin")
    parser.add_argument('--export-csv', type=str, help="Export circulars to CSV file path")
    parser.add_argument('--dry-run', action='store_true', help="Scrape without sending real messages")
    parser.add_argument('--search', type=str, help="Search circulars from database by keyword")
    parser.add_argument('--test-telegram', action='store_true', help="Send test message to verify Telegram")
    parser.add_argument('--discord-test', action='store_true', help="Send test embed to verify Discord")
    parser.add_argument('--limit', type=int, default=15, help="Max circulars to process (default: 15)")

    args = parser.parse_args()

    if args.voice:
        print("🎙️ Generating Daily Audio Bulletin...")
        audio_path = VoiceBulletin.generate_audio()
        if audio_path:
            print(f"✅ Voice bulletin generated: {audio_path}")
        return

    if args.export_csv:
        db = Database()
        csv_data = db.export_to_csv()
        Path(args.export_csv).write_text(csv_data, encoding='utf-8')
        print(f"✅ Exported circulars to {args.export_csv}")
        return

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
            print("✅ Test message sent successfully!")
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

    # Default action
    is_valid, _ = Config.validate(require_telegram=True)
    if not is_valid:
        import setup_bot
        setup_bot.main()
    else:
        run_check(limit=args.limit)


if __name__ == '__main__':
    main()
