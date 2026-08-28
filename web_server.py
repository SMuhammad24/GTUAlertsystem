import os
import sys
import json
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
