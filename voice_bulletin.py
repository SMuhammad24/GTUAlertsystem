import os
from pathlib import Path
from typing import List, Dict, Optional
from config import Config
from database import Database
from tagger import CircularTagger
from security import sanitize_text


class VoiceBulletin:
    """
    Synthesizes a 30-second audio news briefing MP3 for GTU circulars.
    Zero load on GTU (runs 100% locally from SQLite database).
    """

    OUTPUT_DIR = Config.BASE_DIR / 'cache' / 'audio'

    @classmethod
    def generate_bulletin_script(cls, circulars: List[Dict]) -> str:
        """Create a clean, natural spoken script from top circulars."""
        if not circulars:
            return "Hello GTU students. There are no new circulars or exam updates published today. Have a great day ahead!"

        lines = [f"Hello GTU students. Here is your quick daily bulletin."]
        
        for idx, c in enumerate(circulars[:3], 1):
            tags = CircularTagger.extract_tags(c['title'])
            course_text = f"for {' and '.join(tags['courses'])}" if tags['courses'] else ""
            sem_text = f"Semester {', '.join(str(s) for s in tags['semesters'])}" if tags['semesters'] else ""
            target = f"{course_text} {sem_text}".strip()
            
            clean_title = sanitize_text(c['title'], max_length=120)
            lines.append(f"Update {idx}: {clean_title}. {target}")

        lines.append("For direct PDF downloads, check your Telegram bot or GTU Alerts Dashboard. Stay updated!")
        return " ".join(lines)

    @classmethod
    def generate_audio(cls, output_filename: str = "gtu_daily_bulletin.mp3") -> Optional[Path]:
        """
        Generate MP3 audio file using gTTS (Google Text to Speech) if installed.
        Returns Path to generated audio file.
        """
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = cls.OUTPUT_DIR / output_filename

        db = Database()
        circulars = db.get_todays_circulars()
        if not circulars:
            circulars = db.get_recent_circulars(limit=3)

        script = cls.generate_bulletin_script(circulars)

        try:
            from gtts import gTTS
            tts = gTTS(text=script, lang='en', tld='co.in', slow=False)
            tts.save(str(out_path))
            return out_path
        except ImportError:
            # If gtts not installed, write spoken text script as companion text
            script_path = cls.OUTPUT_DIR / "bulletin_script.txt"
            script_path.write_text(script, encoding='utf-8')
            return script_path
        except Exception:
            return None
