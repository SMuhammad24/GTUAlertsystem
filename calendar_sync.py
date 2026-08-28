import urllib.parse
from datetime import datetime, timedelta
import re
from typing import Optional, Dict, Any


class CalendarSync:
    """
    Generates 1-Click Google Calendar creation URLs and .ics event content
    for GTU exam schedules, fee submission deadlines, and event timetables.
    """

    @staticmethod
    def parse_best_date(date_str: str) -> Optional[datetime]:
        """Attempt to parse date strings into datetime object."""
        if not date_str:
            return None
            
        clean_date = re.sub(r'(st|nd|rd|th)', '', date_str.strip())
        formats = [
            '%d-%m-%Y', '%d/%m/%Y', '%d.%m.%Y',
            '%d-%b-%Y', '%d-%B-%Y',
            '%d %b %Y', '%d %B %Y',
            '%Y-%m-%d'
        ]
        for fmt in formats:
            try:
                return datetime.strptime(clean_date, fmt)
            except ValueError:
                continue
        return None

    @classmethod
    def generate_google_calendar_url(cls, title: str, date_str: str, link: str, details: str = "") -> Optional[str]:
        """
        Generate a direct 1-click Google Calendar creation link.
        """
        dt = cls.parse_best_date(date_str)
        if not dt:
            # If no specific year/date found, default to today
            dt = datetime.now() + timedelta(days=7)

        # Standard 9:00 AM to 5:00 PM event
        start_time = dt.strftime('%Y%m%dT090000')
        end_time = dt.strftime('%Y%m%dT170000')

        event_title = f"GTU Deadline: {title[:70]}"
        event_details = f"{title}\n\nPDF Link: {link}\n\nOfficial Portal: https://www.gtu.ac.in/Circular.aspx"
        if details:
            event_details = f"{details}\n\n{event_details}"

        params = {
            'action': 'TEMPLATE',
            'text': event_title,
            'dates': f"{start_time}/{end_time}",
            'details': event_details,
            'location': 'Gujarat Technological University (GTU)',
            'sf': 'true',
            'output': 'xml'
        }

        return f"https://calendar.google.com/calendar/render?{urllib.parse.urlencode(params)}"

    @classmethod
    def generate_ics(cls, title: str, date_str: str, link: str) -> str:
        """Generate valid iCalendar (.ics) format string."""
        dt = cls.parse_best_date(date_str) or (datetime.now() + timedelta(days=7))
        start_time = dt.strftime('%Y%m%dT090000Z')
        end_time = dt.strftime('%Y%m%dT170000Z')
        try:
            from datetime import timezone
            now_time = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        except Exception:
            now_time = datetime.now().strftime('%Y%m%dT%H%M%SZ')

        clean_title = re.sub(r'[\r\n]+', ' ', title).replace(',', '\\,')
        return (
            "BEGIN:VCALENDAR\r\n"
            "VERSION:2.0\r\n"
            "PRODID:-//GTU Alert Bot//EN\r\n"
            "BEGIN:VEVENT\r\n"
            f"UID:gtu-{int(dt.timestamp())}@gtu-alert\r\n"
            f"DTSTAMP:{now_time}\r\n"
            f"DTSTART:{start_time}\r\n"
            f"DTEND:{end_time}\r\n"
            f"SUMMARY:{clean_title}\r\n"
            f"DESCRIPTION:Official Circular: {link}\r\n"
            "LOCATION:Gujarat Technological University\r\n"
            "STATUS:CONFIRMED\r\n"
            "END:VEVENT\r\n"
            "END:VCALENDAR\r\n"
        )
