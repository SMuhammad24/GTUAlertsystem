import os
import sys
import time
import requests
from pathlib import Path

# Ensure UTF-8 output in Windows terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

ENV_FILE = Path(__file__).resolve().parent / '.env'


from security import is_valid_telegram_token, is_valid_chat_id, mask_secret


def print_banner():
    print("=" * 65)
    print("🚀 GTU Circular Automation - Telegram Bot Setup Wizard")
    print("=" * 65)
    print("Ye wizard aapko Telegram Bot configure karne me step-by-step help karega.\n")


def get_bot_info(token: str):
    """Verify bot token and get bot profile."""
    if not is_valid_telegram_token(token):
        return None
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        res = requests.get(url, timeout=10, verify=True)
        data = res.json()
        if res.status_code == 200 and data.get('ok'):
            return data.get('result')
        return None
    except Exception:
        return None


def get_recent_chat_ids(token: str):
    """Fetch recent chat IDs from getUpdates endpoint."""
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    chats = {}
    try:
        res = requests.get(url, timeout=10, verify=True)
        data = res.json()
        if data.get('ok'):
            for update in data.get('result', []):
                msg = update.get('message') or update.get('channel_post') or update.get('my_chat_member')
                if msg and 'chat' in msg:
                    chat = msg['chat']
                    cid = str(chat['id'])
                    title = chat.get('title') or chat.get('username') or chat.get('first_name', 'Unknown Chat')
                    ctype = chat.get('type', 'chat')
                    chats[cid] = f"{title} (Type: {ctype}, ID: {mask_secret(cid)})"
    except Exception as e:
        print(f"⚠️ Error fetching updates: {e}")
    return chats


def test_telegram_message(token: str, chat_id: str):
    """Send a live test message."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': (
            "🎉 <b>GTU Automation Bot Setup Successful!</b>\n\n"
            "✅ Aapka Telegram Bot ab ready hai!\n"
            "Ab jab bhi GTU official website par koi naya circular, fee payment date ya exam notice aayegi, "
            "to direct PDF link ke saath alert yahan receive hoga.\n\n"
            "⚡ <i>Developed for GTU Students</i>"
        ),
        'parse_mode': 'HTML'
    }
    try:
        res = requests.post(url, json=payload, timeout=15, verify=True)
        return res.json()
    except Exception as e:
        return {'ok': False, 'description': str(e)}


def save_to_env(token: str, chat_id: str, interval: int = 15, keyword_filter: str = ""):
    """Save credentials to .env file."""
    env_content = f"""# GTU Circular Automation Configuration
TELEGRAM_BOT_TOKEN={token}
TELEGRAM_CHAT_ID={chat_id}
CHECK_INTERVAL_MINUTES={interval}
KEYWORD_FILTER={keyword_filter}
GTU_CIRCULAR_URL=https://www.gtu.ac.in/Circular.aspx
"""
    with open(ENV_FILE, 'w', encoding='utf-8') as f:
        f.write(env_content)
    print(f"\n💾 Saved credentials securely to {ENV_FILE}")


def main():
    print_banner()

    print("📌 STEP 1: Telegram Bot Token")
    print("1. Telegram open karein aur search karein: @BotFather")
    print("2. /newbot command send karein aur bot ka name & username select karein.")
    print("3. BotFather aapko ek API Token dega (e.g. 1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ_1234567).\n")

    token = ""
    while True:
        token = input("👉 Enter Telegram Bot Token: ").strip()
        if not token:
            print("Token khali nahi ho sakta!")
            continue

        if not is_valid_telegram_token(token):
            print("❌ Invalid Bot Token format! Token must be like: 1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ_1234567\n")
            continue

        print("🔍 Verifying Token...")
        bot_info = get_bot_info(token)
        if bot_info:
            print(f"✅ Bot Verified! Name: {bot_info.get('first_name')} (@{bot_info.get('username')})\n")
            break
        else:
            print("❌ Invalid Bot Token! Kripya sahi token check karke dobara enter karein.\n")

    print("=" * 65)
    print("📌 STEP 2: Telegram Chat ID / Group ID")
    print("Option A: Personal Chat - Bot ko Telegram par /start message bhejein.")
    print("Option B: Group / Channel - Bot ko apne Group me Add karein (Admin banayein) aur group me ek message bhejein.\n")
    
    input("👉 Bot ko message bhej diya ho to press [ENTER] to auto-detect Chat ID...")

    chats = get_recent_chat_ids(token)
    chat_id = ""
    
    if chats:
        print("\n🎉 Auto-detected recent chats:")
        chat_list = list(chats.items())
        for idx, (cid, desc) in enumerate(chat_list, 1):
            print(f"  [{idx}] {desc}")
        
        choice = input(f"\n👉 Select Chat number (1-{len(chat_list)}) ya enter manual ID: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(chat_list):
            chat_id = chat_list[int(choice) - 1][0]
        else:
            chat_id = choice
    else:
        print("\n⚠️ Auto-detect me chat nahi mili (Telegram cache hone me kuch second lag sakta hai).")
        chat_id = input("👉 Enter Chat ID manually (e.g. -1001234567890 ya @username ya personal ID): ").strip()

    print(f"\nSelected Chat ID: {mask_secret(chat_id)}")
    print("📡 Sending Test Message to Telegram...")
    res = test_telegram_message(token, chat_id)
    if res.get('ok'):
        print("✅ Success! Test message aapke Telegram par deliver ho gaya hai. Check your Telegram!")
    else:
        print(f"⚠️ Warning: Message deliver nahi hua. Reason: {res.get('description')}")
        print("Tip: Make sure group me bot added hai aur uske paas message post permission hai.")

    print("\n" + "=" * 65)
    print("📌 STEP 3: Polling Interval & Filter")
    interval_in = input("👉 Check interval in minutes (Default: 15): ").strip()
    interval = int(interval_in) if interval_in.isdigit() else 15

    filter_in = input("👉 Keyword filter (Leave empty for ALL circulars, or e.g. fee,exam,result): ").strip()

    # Save to .env
    save_to_env(token, chat_id, interval, filter_in)

    print("\n" + "=" * 65)
    init_choice = input("👉 Kya aap abhi existing circulars ko database me initialize karna chahte hain? (Y/n): ").strip().lower()
    if init_choice != 'n':
        from main import init_database_silent
        init_database_silent()

    print("\n🎉 SETUP COMPLETED!")
    print("Commands to run:")
    print("  • python main.py --check    -> Ek baar scan karega aur naye circulars send karega")
    print("  • python main.py --daemon   -> 24/7 background me har 15 min scan karega")
    print("  • run_bot.bat               -> Double click to start on Windows")


if __name__ == '__main__':
    main()
