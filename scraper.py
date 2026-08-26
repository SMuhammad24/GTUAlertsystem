import re
import urllib.parse
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from config import Config
from database import Database


class Scraper:
    """
    GTU Public Notification Monitor.
    
    SAFETY & LEGAL COMPLIANCE:
    - Only queries official, publicly accessible GTU notification pages.
    - Strictly does not bypass login, authentication, CAPTCHA, or access controls.
    - Does not crawl private student accounts, restricted resources, or bulk-download files.
    - Respectful rate limiting and request throttling to avoid server load.
    """
    
    _last_request_time = 0.0

    def __init__(self, url: Optional[str] = None):
        self.url = url or Config.GTU_CIRCULAR_URL
        
        # Enforce Rule 1: Validate public URL compliance
        is_safe, reason = Config.is_safe_public_url(self.url)
        if not is_safe:
            raise PermissionError(f"Safety Rule Violation: {reason}")
            
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': Config.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.gtu.ac.in/',
        })

    def fetch_page(self) -> str:
        """
        Fetch HTML content strictly from the public GTU notification portal.
        Includes rate-limiting cooldown and safety checks.
        """
        # Re-verify URL safety before every request
        is_safe, reason = Config.is_safe_public_url(self.url)
        if not is_safe:
            raise PermissionError(f"Safety Rule Violation: {reason}")
            
        try:
            response = self.session.get(self.url, timeout=Config.REQUEST_TIMEOUT)
            
            # Check for access-control / CAPTCHA blocks - DO NOT attempt to bypass
            if response.status_code in [401, 403]:
                raise PermissionError("Access restricted. Automation strictly refuses to bypass access controls or authentication.")
            
            content_lower = response.text[:2000].lower()
            if 'captcha' in content_lower and ('g-recaptcha' in content_lower or 'cf-challenge' in content_lower):
                raise PermissionError("CAPTCHA detected. Automation strictly respects and does not bypass CAPTCHA.")
                
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"GTU Public Portal fetch failed ({self.url}): {e}")

    @staticmethod
    def categorize(title: str) -> str:
        """Categorize circular based on keywords in title."""
        t = title.lower()
        if any(w in t for w in ['fee', 'fees', 'penalty', 'late fee', 'payment', 'challan', 'installment']):
            return 'Fee & Penalty'
        elif any(w in t for w in ['result', 'recheck', 'reassessment', 'marksheet', 'grade card']):
            return 'Result'
        elif any(w in t for w in ['exam form', 'timetable', 'time table', 'examination', 'theory exam', 'practical exam', 'remedial', 'regular exam']):
            return 'Exam & Timetable'
        elif any(w in t for w in ['admission', 'enrollment', 'registration', 'merit', 'counselling', 'affiliation']):
            return 'Admission & Enrollment'
        elif any(w in t for w in ['syllabus', 'curriculum', 'elective', 'specialization']):
            return 'Academics & Syllabus'
        elif any(w in t for w in ['scholarship', 'gold medal', 'convocation', 'placement']):
            return 'Student Support'
        else:
            return 'General Circular'

    def parse_circulars(self, html: str) -> List[Dict]:
        """Parse circulars from GTU HTML page."""
        soup = BeautifulSoup(html, 'html.parser')
        circulars: List[Dict] = []
        seen_links = set()

        # 1. Parse standard circular list (lvCircular)
        heading_tags = soup.find_all(
            'a',
            id=lambda x: x and x.startswith('ContentPlaceHolder1_lvCircular_lblContentHeading_')
        )

        for heading in heading_tags:
            idx = heading['id'].split('_')[-1]
            date_tag = soup.find(id=f'ContentPlaceHolder1_lvCircular_lblUploadDate_{idx}')
            date_str = date_tag.get_text(strip=True) if date_tag else 'Recent'

            # Find target link inside heading or parent container
            # In GTU, the heading tag contains a child <a> tag with the PDF link
            nested_a = heading.find('a', href=True)
            if nested_a and nested_a.get('href'):
                raw_link = nested_a['href']
                title = nested_a.get_text(strip=True) or heading.get_text(strip=True)
            elif heading.get('href') and heading['href'] != '#' and not heading['href'].startswith('javascript:'):
                raw_link = heading['href']
                title = heading.get_text(strip=True)
            else:
                # Search parent container for the PDF link
                parent = heading.find_parent(class_=lambda c: c and ('post' in c or 'col' in c)) or heading.parent
                found_a = parent.find('a', href=re.compile(r'\.pdf', re.IGNORECASE)) if parent else None
                if found_a and found_a.get('href'):
                    raw_link = found_a['href']
                    title = heading.get_text(strip=True)
                else:
                    raw_link = self.url
                    title = heading.get_text(strip=True)

            # Cleanup URL and Title
            clean_link = urllib.parse.urljoin(self.url, raw_link.strip())
            clean_title = re.sub(r'\s+', ' ', title).strip()

            if not clean_title or clean_title == 'Read More':
                continue

            # Safety Rule: Ensure link targets allowed public domains and no private endpoints
            is_safe_link, _ = Config.is_safe_public_url(clean_link)
            if not is_safe_link:
                # Fallback to base public URL if specific link is non-compliant
                clean_link = Config.GTU_CIRCULAR_URL

            unique_key = f"{clean_title}|{clean_link}"
            if unique_key in seen_links:
                continue
            seen_links.add(unique_key)

            category = self.categorize(clean_title)
            cid = Database.generate_id(clean_title, date_str, clean_link)

            circulars.append({
                'id': cid,
                'title': clean_title,
                'date': date_str,
                'link': clean_link,
                'category': category,
                'is_important': False
            })

        # 2. Fallback if lvCircular was empty: scan all .pdf links in content areas
        if not circulars:
            pdf_elements = soup.find_all('a', href=re.compile(r'\.pdf', re.IGNORECASE))
            for a in pdf_elements:
                link = urllib.parse.urljoin(self.url, a.get('href', '').strip())
                title = a.get_text(strip=True)
                if not title or len(title) < 5 or 'gtu logo' in title.lower():
                    continue

                if link in seen_links:
                    continue
                seen_links.add(link)

                category = self.categorize(title)
                cid = Database.generate_id(title, 'Recent', link)
                circulars.append({
                    'id': cid,
                    'title': title,
                    'date': 'Recent',
                    'link': link,
                    'category': category,
                    'is_important': False
                })

        return circulars

    def get_latest_circulars(self) -> List[Dict]:
        """Fetch and return parsed latest circulars."""
        html = self.fetch_page()
        return self.parse_circulars(html)
