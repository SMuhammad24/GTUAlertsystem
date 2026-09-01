import re
from typing import List, Dict, Optional, Any


class DeadlineExtractor:
    """
    Parser to extract critical dates, deadlines, fee penalty slabs,
    and event schedules from GTU circular titles or descriptions.
    """

    # Date pattern variations (e.g. 15-08-2025, 15/08/2025, 15-Aug-2025, 15 August 2025)
    DATE_REGEX = re.compile(
        r'\b(\d{1,2}(?:st|nd|rd|th)?[\s\-\/\.](?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)|\d{1,2})[\s\-\/\.]20\d\d|\d{1,2}[\-\/\.]\d{1,2}[\-\/\.]\d{2,4})\b',
        re.IGNORECASE
    )

    # Penalty & Fee patterns (Rs. 100, ₹500, Rs. 1000/-, penalty of 500)
    PENALTY_REGEX = re.compile(
        r'(?:penalty|late\s+fee|fine)\s*(?:of|is|:)?\s*(?:rs\.?|inr|₹)?\s*(\d{2,5})(?:\/-)?',
        re.IGNORECASE
    )

    # Form / Event context keywords
    CONTEXT_KEYWORDS = {
        'Fee / Exam Form Deadline': [r'form\s+filling', r'exam\s+form', r'submission\s+of', r'without\s+penalty', r'with\s+penalty', r'fee\s+payment'],
        'Reassessment / Recheck': [r're-?check(?:ing)?', r're-?assessment', r'verification'],
        'Exam Schedule': [r'commencing\s+from', r'exam\s+starts?', r'practical\s+exam', r'theory\s+exam', r'timetable'],
        'Enrollment': [r'enrollment\s+form', r'registration\s+date']
    }

    @classmethod
    def extract_dates(cls, text: str) -> List[str]:
        """Extract unique date strings found in text."""
        if not text:
            return []
        matches = cls.DATE_REGEX.findall(text)
        # Clean and deduplicate while maintaining order
        cleaned = []
        for m in matches:
            norm = re.sub(r'(st|nd|rd|th)', '', m.strip())
            if norm not in cleaned:
                cleaned.append(norm)
        return cleaned

    @classmethod
    def extract_penalties(cls, text: str) -> List[str]:
        """Extract penalty / late fee amounts mentioned in text."""
        if not text:
            return []
        matches = cls.PENALTY_REGEX.findall(text)
        penalties = []
        for m in matches:
            formatted = f"₹{m}"
            if formatted not in penalties:
                penalties.append(formatted)
        return penalties

    @classmethod
    def extract_info(cls, text: str) -> Dict[str, Any]:
        """
        Extract all relevant deadline information, structured for alerts.
        """
        dates = cls.extract_dates(text)
        penalties = cls.extract_penalties(text)
        
        # Context detection
        detected_context = "General Update"
        for ctx_name, patterns in cls.CONTEXT_KEYWORDS.items():
            for pat in patterns:
                if re.search(pat, text, re.IGNORECASE):
                    detected_context = ctx_name
                    break
            if detected_context != "General Update":
                break

        has_deadline = bool(dates or penalties or "deadline" in text.lower() or "last date" in text.lower())

        return {
            'has_deadline': has_deadline,
            'dates': dates,
            'penalties': penalties,
            'context': detected_context
        }

    @classmethod
    def format_deadline_badge(cls, info: Dict[str, Any]) -> Optional[str]:
        """
        Generate a highlight badge string for Telegram/Discord if deadlines or penalties are present.
        """
        items = []
        if info.get('penalties'):
            items.append(f"💰 <b>Late Fee:</b> {', '.join(info['penalties'])}")
        if info.get('dates'):
            items.append(f"📅 <b>Key Date(s):</b> {', '.join(info['dates'])}")

        if items:
            return "📌 <b>Important Deadlines:</b>\n" + "\n".join(f"  • {item}" for item in items)
        return None
