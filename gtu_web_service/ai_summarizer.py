import os
import requests
from typing import Dict, List, Optional, Any
from security import sanitize_text


class CircularSummarizer:
    """
    AI & Smart Heuristic Summarizer for GTU Circulars.
    Provides clear, student-friendly 1-2 sentence takeaways with offline fallback and Gemini API support.
    """

    @classmethod
    def get_heuristic_summary(cls, title: str, category: str, tags: Dict[str, Any], deadline_info: Dict[str, Any]) -> str:
        """
        Generate an instant, zero-latency rule-based summary without API keys.
        """
        courses = tags.get('courses', [])
        semesters = tags.get('semesters', [])
        exam_types = tags.get('exam_types', [])
        
        target_audience = []
        if courses:
            target_audience.append("/".join(courses))
        if semesters:
            sem_str = "Sem " + ", ".join(str(s) for s in semesters)
            target_audience.append(sem_str)
        if exam_types:
            target_audience.append("/".join(exam_types))

        audience_desc = " for " + " (".join(target_audience) + (")" if len(target_audience) > 1 else "") if target_audience else ""

        # Categorical takeaway templates
        if category == 'Fee & Penalty':
            penalties = deadline_info.get('penalties', [])
            pen_text = f" with penalty up to {penalties[-1]}" if penalties else ""
            summary = f"Notice regarding fee submission & schedule{audience_desc}{pen_text}. Please check deadlines to avoid late fees."
        elif category == 'Exam & Timetable':
            summary = f"Official examination schedule / timetable release{audience_desc}. Check exam dates and instructions."
        elif category == 'Result':
            summary = f"GTU has declared examination results / rechecking schedule{audience_desc}. Check online result portal."
        elif category == 'Admission & Enrollment':
            summary = f"Notice concerning admission, student enrollment, or registration procedure{audience_desc}."
        elif category == 'Academics & Syllabus':
            summary = f"Academic circular regarding curriculum, syllabus, or term guidelines{audience_desc}."
        else:
            summary = f"Official notification released by Gujarat Technological University{audience_desc}."

        return sanitize_text(summary, max_length=250)

    @classmethod
    def get_ai_summary(cls, title: str, category: str, tags: Dict[str, Any], deadline_info: Dict[str, Any]) -> str:
        """
        Generate AI summary using Gemini API if key is set, otherwise fallback to heuristic summary.
        """
        api_key = os.getenv('GEMINI_API_KEY', '').strip()
        if not api_key:
            return cls.get_heuristic_summary(title, category, tags, deadline_info)

        # Call Gemini REST API directly without heavy dependencies
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        prompt = (
            f"You are a helpful college assistant for Gujarat Technological University (GTU) students. "
            f"Summarize this circular title in 1-2 concise, clear bullet sentences for students. Mention who it applies to and key action needed.\n\n"
            f"Title: {title}\n"
            f"Category: {category}\n"
            f"Tags: {tags.get('hashtags', [])}\n"
            f"Dates: {deadline_info.get('dates', [])}\n"
            f"Summary (max 40 words, clean text, no markdown headers):"
        )

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 100}
        }

        try:
            resp = requests.post(url, json=payload, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                text = data['candidates'][0]['content']['parts'][0]['text'].strip()
                return sanitize_text(text, max_length=300)
        except Exception:
            pass

        # Fallback if API fails or times out
        return cls.get_heuristic_summary(title, category, tags, deadline_info)
