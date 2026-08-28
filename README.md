# 🎓 GTU Circulars, Telegram & Discord Automation Hub

> **GTU (Gujarat Technological University) ki website par aane wale har ek circular, exam timetable, result, aur fee notification ko instant Telegram Group, Discord Server ya Web Dashboard par direct PDF download link, 1-Click Google Calendar Reminders, smart tagging (#BE #Sem6), aur personalized subscriptions ke sath push alert bhejta hai.**

---

## 🌟 Supercharged Features (Zero GTU Server Load)

- ⚡ **Real-Time Push Alerts:** GTU website par circular aate hi turant mobile par Telegram aur Discord alert.
- 🎯 **Personalized Student Subscriptions:**
  - `/subscribe BE 6` – Sirf apne course aur semester ke circulars personal DM me receive karein (**Zero Spam!**).
  - `/mysubscriptions` & `/unsubscribe`
- 📅 **1-Click Google Calendar Sync:**
  - Har exam date aur fee deadline ke sath direct `[ 📅 Add to Google Calendar ]` button — phone calendar me auto-reminder lag jata hai.
- 🏷️ **Smart Branch & Semester Tagging:** Course (`#BE`, `#Diploma`, `#BPharm`, `#MBA`, `#MCA`) aur Semester (`#Sem4`, `#Sem6`) auto-detect karke clickable hashtags generate karta hai.
- 💰 **Deadline & Fee Penalty Extractor:** Late fee amount (₹500, ₹1000, ₹2000) aur submission dates automatically extract karke highlight badge me dikhata hai.
- 🇮🇳 **Gujarati + English Dual Language Briefs:** Important circulars ka clean ગુજરાતી સારાંશ.
- 🎙️ **30-Second Daily Voice Bulletin:** Spoken audio news update (`python main.py --voice` ya bot command `/voice`).
- 🤖 **Interactive 2-Way Telegram Bot:**
  - `/latest [n]`, `/search <keyword>`, `/exams`, `/results`, `/fees`, `/stats`, `/digest`, `/subscribe`, `/voice`.
- 🌐 **Modern Glassmorphic Web Dashboard & PWA Mobile App:**
  - Live searchable circulars feed with branch & category pills.
  - Interactive Notice Category breakdown chart.
  - **PWA Mobile App:** Installable directly on Android & iOS home screen!
  - **Data Export:** 1-Click **Export to CSV** & **Export to JSON** buttons.
- 📡 **REST API & RSS Feed:**
  - REST API: `GET /api/circulars`, `GET /api/stats`
  - RSS 2.0 XML: `GET /feed.xml` for RSS readers.
- 👾 **Discord Webhook Support:** Rich Discord Embeds with category-matched color schemes.
- 🛡️ **Duplicate Prevention & Security:** SQLite Database (`circulars.db`), SSRF protection, DoS memory limits, and rate limiting.
- ☁️ **24/7 Free Cloud Hosting:** GitHub Actions workflow included hai — aapka PC band hone par bhi cloud par 24/7 free scan hota rahega!

---

## 🚀 Quick Setup Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment (`.env`)
Aap direct interactive wizard chala sakte hain:
```bash
python setup_bot.py
```
Ya fir `.env.example` ko copy karke `.env` create karein:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_or_group_id

# Optional:
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
GEMINI_API_KEY=your_gemini_api_key
WEB_PORT=8080
```

---

## 💻 Running the Automation

### 1. 🌐 Modern Web Dashboard & PWA
Start the live dashboard & REST API on `http://127.0.0.1:8080`:
```bash
python main.py --web
```

### 2. 🤖 Interactive Telegram Bot Listener (2-Way Commands & Subscriptions)
```bash
python main.py --bot
```

### 3. 🎙️ 30-Second Voice News Bulletin
```bash
python main.py --voice
```

### 4. 📥 Export Circulars to CSV
```bash
python main.py --export-csv gtu_data.csv
```

### 5. ⏱️ Daemon Monitor Mode (Background Polling)
```bash
python main.py --daemon
```

### 6. 📋 Daily Bulletin / Morning Digest
```bash
python main.py --digest
```

### 7. 🧪 Run Test Suite
```bash
python -m unittest test_suite.py
```

---

## 📁 Project Structure

```
gtu-automation/
├── web/
│   ├── index.html              # Glassmorphic Dark Dashboard with Charts
│   ├── style.css               # Modern CSS, Chart & PWA styles
│   ├── app.js                  # Interactive frontend logic & CSV export
│   ├── manifest.json           # PWA Mobile App Manifest
│   └── sw.js                   # Service Worker for offline caching
├── .github/workflows/
│   └── gtu_circulars.yml       # 24/7 Free GitHub Actions Cloud Cron
├── calendar_sync.py            # 1-Click Google Calendar & ICS Sync
├── translations.py             # Gujarati-English Dual Language Translator
├── pdf_inspector.py            # Server-Safe Cached PDF Text/Table Parser
├── voice_bulletin.py           # 30-Second Audio News Briefing Generator
├── tagger.py                   # Smart Course/Branch/Semester & Hashtags
├── extractor.py                # Deadlines & Fee Penalty Extractor
├── ai_summarizer.py            # AI & Heuristic Summaries
├── database.py                 # SQLite DB with Subscriptions & Data Export
├── notifier.py                 # Rich HTML Telegram Notifier with Calendar
├── discord_notifier.py         # Discord Webhook Embed Alerts
├── telegram_bot.py             # Interactive 2-Way Bot Command Listener
├── web_server.py               # Lightweight Web Server, REST API & RSS
├── main.py                     # Central CLI & Automation Hub
├── setup_bot.py                # Interactive setup wizard
├── test_suite.py               # Comprehensive Unit Tests (100% Pass)
├── requirements.txt            # Python dependencies
└── README.md                   # Full documentation
```

---

## ⚖️ Legal & Zero Server Load Compliance

1. **Zero GTU Server Load:** Subscriptions, Calendar sync, Audio synthesis, Dashboard charts, and Translations execute **100% locally or client-side**. GTU official server is never overloaded.
2. **Public Webpages Only:** Scrapes only publicly accessible GTU notice boards (`https://www.gtu.ac.in/Circular.aspx`).
3. **No Access Control Bypass:** Strictly does NOT access private/student portals or CAPTCHAs.
4. **Server-Friendly:** Respectful polling intervals (minimum 5-15 mins) and local permanent caching.
