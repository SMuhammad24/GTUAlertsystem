from typing import Dict, Any, Optional


class GujaratiTranslator:
    """
    Generates student-friendly Gujarati (ગુજરાતી) explanations for GTU circulars.
    Runs 100% offline using tailored linguistic rule maps (0% external API load).
    """

    CATEGORY_GUJARATI = {
        'Fee & Penalty': 'ફી અને લેટ ફી દંડ નોટિસ',
        'Exam & Timetable': 'પરીક્ષા ટાઈમટેબલ અને કાર્યક્રમ',
        'Result': 'પરીક્ષા પરિણામ જાહેર',
        'Admission & Enrollment': 'પ્રવેશ અને રજીસ્ટ્રેશન સૂચના',
        'Academics & Syllabus': 'શૈક્ષણિક અભ્યાસક્રમ અપડેટ',
        'Student Support': 'વિદ્યાર્થી સહાય અને સ્કોલરશિપ',
        'General Circular': 'સામાન્ય પરિપત્ર'
    }

    @classmethod
    def get_gujarati_brief(cls, title: str, category: str, tags: Dict[str, Any], deadline_info: Dict[str, Any]) -> str:
        """
        Generate a concise, natural Gujarati brief for students.
        """
        cat_gu = cls.CATEGORY_GUJARATI.get(category, 'GTU પરિપત્ર')
        courses = tags.get('courses', [])
        semesters = tags.get('semesters', [])
        
        target_parts = []
        if courses:
            target_parts.append(", ".join(courses))
        if semesters:
            target_parts.append(f"સેમેસ્ટર {', '.join(str(s) for s in semesters)}")
            
        target_str = f" ({' - '.join(target_parts)})" if target_parts else ""

        if category == 'Fee & Penalty':
            penalties = deadline_info.get('penalties', [])
            pen_text = f" (દંડ: {', '.join(penalties)})" if penalties else ""
            msg = f"📌 <b>ગુજરાતી સારાંશ:</b> {cat_gu}{target_str}{pen_text}. ફી ભરવાની અંતિમ તારીખ ચૂકી ન જવાય તેનું ખાસ ધ્યાન રાખવું."
        elif category == 'Exam & Timetable':
            msg = f"📌 <b>ગુજરાતી સારાંશ:</b> {cat_gu}{target_str}. વિદ્યાર્થીઓએ પરીક્ષાનું ટાઈમટેબલ અને સૂચનાઓ પોર્ટલ પરથી ચકાસી લેવી."
        elif category == 'Result':
            msg = f"📌 <b>ગુજરાતી સારાંશ:</b> GTU દ્વારા પરીક્ષાનું પરિણામ/પુનઃચકાસણી (Rechecking) જાહેર કરવામાં આવ્યું છે{target_str}."
        else:
            msg = f"📌 <b>ગુજરાતી સારાંશ:</b> GTU દ્વારા સત્તાવાર સૂચના જાહેર કરવામાં આવી છે{target_str}."

        return msg
