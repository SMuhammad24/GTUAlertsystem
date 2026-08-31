import os
import sys
import json
import re
import urllib.parse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Dict, List, Any

# Ensure UTF-8 output on Windows terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from config import Config
from database import Database
from tagger import CircularTagger
from extractor import DeadlineExtractor
from security import sanitize_text


class GTUWebHandler(SimpleHTTPRequestHandler):
    """
    HTTP Request Handler for GTU Alerts Web Dashboard & REST/RSS API.
    """

    WEB_DIR = Config.BASE_DIR / 'web'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(self.WEB_DIR), **kwargs)

    def _send_json(self, data: Any, status: int = 200):
        body = json.dumps(data, indent=2).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(body)

    def _send_xml(self, xml_str: str, status: int = 200):
        body = xml_str.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/rss+xml; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Content-Length', '0')
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query_params = urllib.parse.parse_qs(parsed.query)

        # 1. API: List Circulars
        if path == '/api/circulars':
            db = Database()
            limit = int(query_params.get('limit', ['100'])[0])
            category = query_params.get('category', [None])[0]
            search_q = query_params.get('q', [None])[0]
            filter_param = query_params.get('filter', [None])[0]

            if search_q:
                results = db.search_circulars(search_q, limit=limit)
            elif filter_param == 'today':
                results = db.get_todays_circulars()
            elif category and category != 'ALL':
                results = db.get_circulars_by_category(category, limit=limit)
            else:
                results = db.get_recent_circulars(limit=limit)

            # Enriched fields
            enriched = []
            for r in results:
                tags = CircularTagger.extract_tags(r['title'])
                deadlines = DeadlineExtractor.extract_info(r['title'])
                item = dict(r)
                item['tags'] = ", ".join(tags['hashtags'])
                item['courses'] = tags['courses']
                item['semesters'] = tags['semesters']
                item['deadlines'] = deadlines['dates']
                item['penalties'] = deadlines['penalties']
                enriched.append(item)

            self._send_json(enriched)
            return

        # 2. API: Summary Statistics
        elif path == '/api/stats':
            db = Database()
            stats = {
                'total': db.get_total_count(),
                'today': len(db.get_todays_circulars()),
                'categories': db.get_category_stats(),
                'status': 'online'
            }
            self._send_json(stats)
            return

        # 3. API: Health Check
        elif path == '/api/health':
            self._send_json({'status': 'healthy', 'uptime': 'active', 'timestamp': str(Path(Config.DB_PATH).exists())})
            return

        # 3.5 API: AI Q&A Assistant Endpoint
        elif path == '/api/ai/ask':
            query = query_params.get('q', [''])[0].strip()
            if not query:
                self._send_json({'answer': 'Please provide a question query parameter ?q=...', 'circular': None})
                return

            db = Database()
            circulars = db.get_recent_circulars(limit=75)
            q_lower = query.lower()
            tokens = [t for t in re.sub(r'[^a-zA-Z0-9\s]', ' ', q_lower).split() if len(t) > 1]

            best_match = None
            best_score = -1

            for c in circulars:
                score = 0
                title_lower = c['title'].lower()
                for tok in tokens:
                    if tok in title_lower:
                        score += 10
                if 'me' in q_lower and ('me ' in title_lower or 'me(' in title_lower):
                    score += 25
                if 'diploma' in q_lower and 'diploma' in title_lower:
                    score += 25
                if 'pharmacy' in q_lower and 'pharm' in title_lower:
                    score += 25
                if 'dissertation' in q_lower and 'dissertation' in title_lower:
                    score += 30
                if 'result' in q_lower and ('result' in title_lower or c.get('category') == 'Result'):
                    score += 15
                if score > best_score:
                    best_score = score
                    best_match = c

            if best_match and best_score >= 8:
                tags = CircularTagger.extract_tags(best_match['title'])
                deadlines = DeadlineExtractor.extract_info(best_match['title'])
                
                from ai_summarizer import CircularSummarizer
                summary = CircularSummarizer.get_ai_summary(
                    best_match['title'],
                    best_match.get('category', 'General'),
                    tags,
                    deadlines
                )
                
                dates = deadlines.get('dates', [])
                if dates:
                    ans = f"Based on official GTU circular <strong>\"{best_match['title']}\"</strong>, key dates/deadlines are: <span class=\"ai-highlight-pill\">📅 {', '.join(dates)}</span>. (Published on {best_match.get('date', 'Recent')}).<br><span style='color: #475569; font-size: 0.88rem; display: inline-block; margin-top: 4px;'>💡 <em>{summary}</em></span>"
                else:
                    ans = f"Found official notification <strong>\"{best_match['title']}\"</strong> released on <span class=\"ai-highlight-pill\">📢 {best_match.get('date', 'Recent')}</span>.<br><span style='color: #475569; font-size: 0.88rem; display: inline-block; margin-top: 4px;'>💡 <em>{summary}</em></span>"
                
                item = dict(best_match)
                item['deadlines'] = dates
                item['tags'] = ", ".join(tags['hashtags'])
                item['ai_summary'] = summary
                self._send_json({'answer': ans, 'circular': item})
            else:
                self._send_json({
                    'answer': f"No direct circular found for '<em>{query}</em>'. Try asking about ME Dissertation, Pharmacy Rechecking, or Diploma Results.",
                    'circular': None
                })
            return

        # 4. RSS Feed: /feed.xml or /rss.xml
        elif path in ['/feed.xml', '/rss.xml']:
            db = Database()
            circulars = db.get_recent_circulars(limit=25)
            rss = self._generate_rss(circulars)
            self._send_xml(rss)
            return

        # 5. Static Files (HTML / CSS / JS)
        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Trigger on-demand scraper
        if path == '/api/check-now':
            try:
                from main import run_check
                new_count = run_check(dry_run=False, limit=10)
                self._send_json({
                    'success': True,
                    'new_found': new_count,
                    'message': f"Scan complete! {new_count} new circulars detected." if new_count > 0 else "GTU Portal scanned. No new circulars found."
                })
            except Exception as e:
                self._send_json({'success': False, 'error': str(e)}, status=500)
            return

        # Student Auth: Send OTP
        elif path == '/api/auth/send-otp':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
                data = json.loads(body)
                email = data.get('email', '').strip()
                name = data.get('name', 'Student').strip()
                channel = data.get('channel', 'email')

                if not email:
                    self._send_json({'success': False, 'error': 'Valid email is required.'}, status=400)
                    return

                from otp_service import OTPService
                otp = OTPService.generate_otp(email)
                
                email_sent = False
                status_msg = ""
                if channel == 'email':
                    email_sent, status_msg = OTPService.send_otp_email(email, otp, student_name=name)

                self._send_json({
                    'success': True,
                    'email_sent': email_sent,
                    'otp_code': otp,  # Included for seamless developer testing/fallback
                    'message': f"Verification code sent to {email}!" if email_sent else f"Generated OTP: {otp} ({status_msg})"
                })
            except Exception as e:
                self._send_json({'success': False, 'error': str(e)}, status=500)
            return

        # Student Auth: Verify OTP
        elif path == '/api/auth/verify-otp':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
                data = json.loads(body)
                email = data.get('email', '').strip()
                otp = data.get('otp', '').strip()

                if not email or not otp:
                    self._send_json({'success': False, 'error': 'Email and OTP are required.'}, status=400)
                    return

                from otp_service import OTPService
                verified, msg = OTPService.verify_otp(email, otp)
                if verified:
                    self._send_json({'success': True, 'message': msg})
                else:
                    self._send_json({'success': False, 'error': msg}, status=400)
            except Exception as e:
                self._send_json({'success': False, 'error': str(e)}, status=500)
            return

        self.send_error(404, "Endpoint not found")

    def _generate_rss(self, circulars: List[Dict]) -> str:
        """Generate a valid RSS 2.0 XML string."""
        items = []
        for c in circulars:
            title = sanitize_text(c['title'], max_length=200).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            link = c['link'].replace('&', '&amp;')
            cat = c.get('category', 'General')
            date_str = c.get('date', '')
            items.append(f"""
    <item>
      <title>{title}</title>
      <link>{link}</link>
      <description>GTU Circular ({cat}) - Published on {date_str}</description>
      <category>{cat}</category>
      <guid>{c['id']}</guid>
    </item>""")

        rss_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>GTU Official Circulars &amp; Alerts</title>
    <link>{Config.GTU_CIRCULAR_URL}</link>
    <description>Instant live feed of Gujarat Technological University circulars, timetables, and fee notices.</description>
    <language>en-us</language>{"".join(items)}
  </channel>
</rss>"""
        return rss_xml


def run_server(port: int = 8080, host: str = "127.0.0.1"):
    """Start standalone threaded web dashboard server."""
    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, GTUWebHandler)
    print("=" * 60)
    print(f"🌐 GTU Alerts Web Dashboard is LIVE!")
    print(f"👉 Open in your browser: http://{host}:{port}")
    print(f"📡 REST API: http://{host}:{port}/api/circulars")
    print(f"📰 RSS Feed: http://{host}:{port}/feed.xml")
    print("=" * 60)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Stopping web server...")
        httpd.server_close()


if __name__ == '__main__':
    port = int(os.getenv('WEB_PORT', '8080'))
    run_server(port=port)
