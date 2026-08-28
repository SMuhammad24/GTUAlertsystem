# 🎓 GTU Circulars, Telegram & Discord Automation Hub

> **GTU (Gujarat Technological University) ki website par aane wale har ek circular, exam timetable, result, aur fee notification ko instant Telegram Group, Discord Server ya Web Dashboard par direct PDF download link, smart tagging (#BE #Sem6), aur deadline extractor ke sath push alert bhejta hai.**

---

## 🌟 Supercharged Features

- ⚡ **Real-Time Push Alerts:** GTU website par circular aate hi turant mobile par Telegram aur Discord alert.
- 🏷️ **Smart Branch & Semester Tagging:** Course (`#BE`, `#Diploma`, `#BPharm`, `#MBA`, `#MCA`) aur Semester (`#Sem4`, `#Sem6`) auto-detect karke clickable hashtags generate karta hai.
- 💰 **Deadline & Fee Penalty Extractor:** Late fee amount (₹500, ₹1000, ₹2000) aur submission dates automatically extract karke highlight badge me dikhata hai.
- 🤖 **Interactive 2-Way Telegram Bot:**
  - `/latest [n]` – Pichle 5 ya N naye circulars dekhein.
  - `/search <keyword>` – Search circulars (e.g. `/search exam fee`).
  - `/exams`, `/results`, `/fees` – Category-wise quick filter.
  - `/stats` – Database analytics aur tracking status.
  - `/digest` – Aaj ka consolidated morning bulletin.
- 🌐 **Modern Glassmorphic Web Dashboard:**
  - Live searchable circulars feed with branch & category pills.
  - Metrics cards (Total circulars, Today's updates, Fee notices, Exam notices).
  - Manual "Check GTU Portal" on-demand scan trigger.
- 📡 **REST API & RSS Feed:**
  - REST API: `GET /api/circulars`, `GET /api/stats`
  - RSS 2.0 XML: `GET /feed.xml` for RSS readers and news aggregators.
- 👾 **Discord Webhook Support:** Rich Discord Embeds with category-matched color schemes.
- 🧠 **AI / Smart Summary:** Gemini AI + zero-latency heuristic summarizer.
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

### 1. 🌐 Modern Web Dashboard
Start the live dashboard & REST API on `http://127.0.0.1:8080`:
```bash
python main.py --web
```

### 2. 🤖 Interactive Telegram Bot Listener (2-Way Commands)
Start the 2-way bot to reply to student commands (`/latest`, `/search`, `/stats`):
```bash
python main.py --bot
```

### 3. ⏱️ Daemon Monitor Mode (Background Polling)
Background me continuous monitoring ke liye:
```bash
python main.py --daemon
```

### 4. 🔍 Instant Keyword Search from Terminal
```bash
python main.py --search "Diploma Sem 4"
```

### 5. 📋 Daily Bulletin / Morning Digest
```bash
# Terminal par digest print karne ke liye:
python main.py --digest

# Telegram group me broadcast karne ke liye:
python main.py --digest --send-digest
```

### 6. 🧪 Run Test Suite
```bash
python -m unittest test_suite.py
```

---

## 📡 REST API & RSS Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/` | `GET` | Web Dashboard Interface |
| `/api/circulars?q=...&category=...&limit=30` | `GET` | Filtered list of circulars with tags & deadlines |
| `/api/stats` | `GET` | Overall circulars & category statistics |
| `/api/check-now` | `POST` | On-demand live scraper trigger |
| `/feed.xml` / `/rss.xml` | `GET` | RSS 2.0 XML Syndication Feed |

---

## 📁 Project Structure

```
gtu-automation/
├── web/
│   ├── index.html              # Glassmorphic Dark UI Dashboard
│   ├── style.css               # Modern CSS & animations
│   └── app.js                  # Frontend interactive search & real-time fetch
├── .github/workflows/
│   └── gtu_circulars.yml       # 24/7 Free GitHub Actions Cloud Cron
├── config.py                   # Configuration & Policy Loader
├── database.py                 # SQLite DB with auto-migration & search
├── scraper.py                  # GTU Web Scraper & HTML Parser
├── tagger.py                   # Smart Course/Branch/Semester & Hashtag Extractor
├── extractor.py                # Important Deadlines & Fee Penalty Extractor
├── ai_summarizer.py            # AI & Heuristic TL;DR Takeaways
├── notifier.py                 # Rich HTML Telegram Notifier
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

## ⚖️ Legal & Safety Compliance Policy

This project strictly adheres to ethical automation, rate-limiting, and web safety rules:
1. **Public Webpages Only:** Scrapes only publicly accessible GTU notice boards (`https://www.gtu.ac.in/Circular.aspx`).
2. **No Access Control Bypass:** Strictly does NOT access private/student portals, passwords, or CAPTCHAs.
3. **Server-Friendly:** Respectful polling intervals (minimum 5-15 mins) and payload size limit guards.
