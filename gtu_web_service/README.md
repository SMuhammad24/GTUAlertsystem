# 🌐 GTU Alert System - Web Dashboard & Backend Service

Ye folder **Website + Python Backend Server** ka standalone (alag kiya hua) package hai. Isme frontend UI, REST API, AI Search, aur Real Email OTP system sab kuch shamil hai.

---

## 📁 Folder Structure

```
gtu_web_service/
├── web/                       # Frontend Files (HTML, CSS, JS, PWA)
│   ├── index.html             # Dashboard UI
│   ├── style.css              # Styling & Animations
│   ├── app.js                 # Frontend Logic & API Calling
│   ├── data.json              # Sample Circulars fallback
│   ├── manifest.json          # PWA Config
│   └── sw.js                  # Service Worker
├── web_server.py              # Main Python Web & API Server
├── otp_service.py             # Real Email OTP Generator & Sender (SMTP)
├── config.py                  # Environment & App Settings
├── database.py                # SQLite Circulars Database Manager
├── scraper.py                 # GTU Circular Scraper
├── tagger.py                  # AI Branch & Course Tagger
├── extractor.py               # Deadline & Fee Extractor
├── security.py                # Security & Sanitization
├── ai_summarizer.py           # Circular AI Summary Generator
├── circulars.db               # SQLite Database file
├── requirements.txt           # Minimal Python Dependencies
├── Procfile                   # Cloud Deployment Command
└── .env.example               # Environment Variables Template
```

---

## 🚀 1. Local Pe Test Kaise Karein

1. **Terminal kholein is folder ke andar:**
   ```bash
   cd "c:\Users\muham\gtu aoutomation\gtu_web_service"
   ```

2. **Dependencies install karein:**
   ```bash
   pip install -r requirements.txt
   ```

3. **(Optional) Real Email OTP ke liye `.env` file banayein:**
   Ek nayi file `.env` banayein aur usme apna Gmail App Password likhein:
   ```env
   PORT=8080
   EMAIL_SENDER=your_email@gmail.com
   EMAIL_PASSWORD=your_16_digit_gmail_app_password
   ```

4. **Server start karein:**
   ```bash
   python web_server.py
   ```

5. **Browser me open karein:**
   👉 `http://localhost:8080`

---

## ☁️ 2. Render.com Par Permanent Deploy Kaise Karein (Free)

1. Is `gtu_web_service` folder ko ek naye GitHub Repository me push karein (ya apne existing repo me rakhein).
2. [Render.com](https://render.com/) par login karein.
3. **"New +"** par click karke **"Web Service"** chunein.
4. Apna GitHub repo connect karein.
5. Ye settings select karein:
   - **Root Directory:** `gtu_web_service` *(agar subfolder me hai)*
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python web_server.py`
6. **Environment Variables** section me add karein:
   - `EMAIL_SENDER` = `your_gmail@gmail.com`
   - `EMAIL_PASSWORD` = `your_16_digit_gmail_app_password`
7. **"Create Web Service"** par click karein!

Kuch hi minute me aapko ek live link mil jayegi (jaise `https://gtu-alerts.onrender.com`), jisme:
* Real email par 4-digit OTP aayega.
* Screen par test OTP banner hide ho jayega.
* 24/7 poora dashboard live chalega!
