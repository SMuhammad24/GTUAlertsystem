# 🎓 GTU Circular to Telegram Automation Bot

> **GTU (Gujarat Technological University) ki website par aane wale har ek circular, exam timetable, result, aur fee notification ko instant aapke Telegram Group / Channel ya Mobile phone par direct PDF download link ke sath push alert bhejta hai.**

---

## 🌟 Features

- ⚡ **Real-Time Push Alerts:** GTU website par circular aate hi turant mobile par notification.
- 💰 **Zero Penalty (Fee Alerts):** Exam fees, regular/remedial fees ya penalty notifications priority badge ke sath receive honge.
- 📄 **1-Click Direct PDF Link:** Browser open karke GTU portal par search karne ki zaroorat nahi; message me direct PDF download link milti hai.
- 🏷️ **Smart Categorization:**
  - 🚨 Fee & Penalty Alerts
  - 📝 Exam & Timetable Updates
  - 📊 Result Declarations
  - 🎓 Admission & Enrollment
  - 📚 Academics & Syllabus
- 🛡️ **Duplicate Prevention:** SQLite Database (`circulars.db`) duplicate check rakhta hai taaki ek hi circular baar-baar repeat na ho.
- ☁️ **24/7 Free Cloud Hosting:** GitHub Actions workflow included hai — aapka computer band hone par bhi cloud par 24/7 free scan hota rahega!
- ⚖️ **Legal & Safety Compliant:** Strictly monitors only public notice boards, never touches private/student login areas or CAPTCHAs, and respects GTU servers with built-in rate limits.

---

## ⚖️ Legal & Safety Compliance Policy

This project strictly adheres to ethical automation, rate-limiting, and web safety rules:

### ✅ ALLOWED:
1. **Public Webpages Only:** Monitor only publicly accessible GTU notification portals (`https://www.gtu.ac.in/Circular.aspx`).
2. **Public Announcements:** Share only publicly released circular metadata (Title, Date, Public PDF Link) in our Telegram group.
3. **Respectful Intervals:** Automated checks are conducted at reasonable, server-friendly intervals (minimum 5-15 minutes) without creating excessive server load.

### 🚫 DO NOT:
1. **No Access-Control Bypass:** Strictly does NOT bypass GTU login, student portals, authentication, or CAPTCHA.
2. **No Private / Student Data:** Strictly does NOT collect, store, or forward any private, student-specific, or confidential information.
3. **No Server Overload & No Bulk Crawling:** Strictly does NOT perform deep crawling, bulk asset downloads, or high-frequency requests.

## 🚀 Quick Setup Guide (Step-by-Step)

### Step 1: Telegram Bot Setup (2 Minutes)

1. Telegram open karein aur search karein **`@BotFather`**.
2. Chat start karke `/newbot` type karein.
3. Apne bot ka naam (e.g. `My GTU Circular Bot`) aur username (e.g. `my_gtu_circular_bot`) enter karein.
4. BotFather aapko ek **API Token** dega (e.g. `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`). Isse copy kar lein.

### Step 2: Bot ko Apne Group / Chat me Add Karein

- **Agar Group me chahiye:** Apne college/doston ke Telegram group me bot ko Add karein aur use Admin permissions dein. Group me koi bhi ek message type karein (e.g. `test`).
- **Agar Personal Chat me chahiye:** Bot ke chat me jakar `/start` click karein.

---

### Step 3: Run Interactive Setup Wizard

Terminal / Command Prompt me run karein:

```bash
python setup_bot.py
```

Ye wizard aapko token enter karne ko kahega, auto-detect karega aapka Chat ID, aur turant ek **Test Message** bhejkar verify karega!

---

## 💻 Running the Automation

### Mode 1: Local PC Background Monitor (Daemon Mode)

Har 15 minute me background me scan karne ke liye:

```bash
python main.py --daemon
```
*(Windows par aap direct `run_bot.bat` file par double click karke bhi start kar sakte hain)*

### Mode 2: Single Check Cycle (Cron / Task Scheduler)

```bash
python main.py --check
```

### Mode 3: Test Telegram Connection

```bash
python main.py --test-telegram
```

### Mode 4: Dry Run (Test Scraper without sending real messages)

```bash
python main.py --dry-run
```

---

## ☁️ 24/7 Free Cloud Setup (GitHub Actions)

Agar aap chahte hain ki **aapka computer band ho tab bhi 24/7 alerts aate rahein**:

1. Is project folder ko apne **GitHub Repository** me push karein.
2. Apne GitHub Repository ke **Settings** > **Secrets and variables** > **Actions** me jayein.
3. **New repository secret** par click karein aur ye do secrets add karein:
   - Name: `TELEGRAM_BOT_TOKEN` | Value: *(Aapka Bot Token)*
   - Name: `TELEGRAM_CHAT_ID` | Value: *(Aapka Chat ID / Group ID)*
4. Bas! GitHub Actions workflow (`.github/workflows/gtu_circulars.yml`) automatically har **15 minute** me cloud me run hoga aur naye circulars group me bhejega.

---

## ⚙️ Configuration (`.env`)

| Variable | Description | Default |
| :--- | :--- | :--- |
| `TELEGRAM_BOT_TOKEN` | Bot API token from @BotFather | Required |
| `TELEGRAM_CHAT_ID` | Telegram Group ID or User ID | Required |
| `CHECK_INTERVAL_MINUTES` | Polling interval for daemon mode | `15` |
| `KEYWORD_FILTER` | Comma separated filter keywords (e.g. `fee,exam,result`) | *(All circulars)* |
| `GTU_CIRCULAR_URL` | GTU official circulars page | `https://www.gtu.ac.in/Circular.aspx` |

---

## 📁 Project Structure

```
gtu-automation/
├── .github/
│   └── workflows/
│       └── gtu_circulars.yml   # 24/7 Free GitHub Actions Cloud Cron
├── .env.example                # Configuration template
├── config.py                   # Settings loader
├── database.py                 # SQLite duplicate prevention
├── scraper.py                  # GTU web scraper & parser
├── notifier.py                 # Telegram push alerts & HTML formatter
├── main.py                     # Main runner & CLI
├── setup_bot.py                # Interactive setup & test wizard
├── run_bot.bat                 # Windows 1-click launcher
├── requirements.txt            # Python dependencies
└── README.md                   # Documentation
```
