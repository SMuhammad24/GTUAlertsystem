import re
from typing import Dict, List, Any


class CircularTagger:
    """
    Intelligent tagging engine for GTU circulars.
    Detects courses, branches, semesters, exam types, and generates Telegram/Discord hashtags.
    """

    # Course pattern definitions
    COURSES = {
        'BE': [r'\bb\.?e\.?\b', r'\bdegree\s+eng(?:ineering)?\b', r'\bbachelor\s+of\s+engineering\b'],
        'Diploma': [r'\bdiploma\b', r'\bd\.?e\.?\b', r'\bpolytechnic\b'],
        'ME': [r'\bm\.?e\.?\b', r'\bm\.?tech\b', r'\bmaster\s+of\s+engineering\b'],
        'BPharm': [r'\bb\.?\s*pharm(?:acy)?\b', r'\bbachelor\s+of\s+pharmacy\b'],
        'MPharm': [r'\bm\.?\s*pharm(?:acy)?\b', r'\bmaster\s+of\s+pharmacy\b'],
        'MBA': [r'\bm\.?b\.?a\.?\b', r'\bmanagement\b'],
        'MCA': [r'\bm\.?c\.?a\.?\b', r'\bcomputer\s+applications?\b'],
        'BArch': [r'\bb\.?\s*arch(?:itecture)?\b'],
        'MArch': [r'\bm\.?\s*arch(?:itecture)?\b'],
        'PDDC': [r'\bpddc\b', r'\bpost\s+diploma\b'],
        'BVoc': [r'\bb\.?\s*voc\b'],
        'DVoc': [r'\bd\.?\s*voc\b'],
        'PhD': [r'\bph\.?d\.?\b', r'\bdoctoral\b', r'\bresearch\s+scholar\b'],
        'BHMCT': [r'\bbhmct\b', r'\bhotel\s+management\b'],
        'MSc': [r'\bm\.?\s*sc\b', r'\bintegrated\s+m\.?sc\b']
    }

    # Semester patterns
    SEM_PATTERNS = [
        (r'\bsem(?:ester)?[-:\s]*([1-8])\b', 1),
        (r'\b([1-8])(?:st|nd|rd|th)[-:\s]*sem(?:ester)?\b', 1),
        (r'\bsem(?:ester)?[-:\s]*([1-8])\s*(?:to|&|-)\s*([1-8])\b', 2),
    ]

    # Exam type patterns
    EXAM_TYPES = {
        'Regular': [r'\bregular\b'],
        'Remedial': [r'\bremedial\b', r'\bsupplementary\b', r'\bbacklog\b'],
        'Summer': [r'\bsummer[-:\s]*20\d\d\b', r'\bsummer\b'],
        'Winter': [r'\bwinter[-:\s]*20\d\d\b', r'\bwinter\b'],
        'Special Term': [r'\bspecial\s+term\b', r'\bspecial\s+exam\b'],
        'Internal/VIVA': [r'\bviva\b', r'\bpractical\s+exam\b', r'\binternal\b', r'\bmidd?-?sem\b']
    }

    @classmethod
    def extract_tags(cls, title: str) -> Dict[str, Any]:
        """
        Analyze a circular title and extract structured tag metadata.
        Returns a dict containing courses, semesters, exam_types, and ready-to-use hashtags.
        """
        if not title:
            return {
                'courses': [],
                'semesters': [],
                'exam_types': [],
                'hashtags': ['#GTU', '#Circular']
            }

        title_lower = title.lower()

        # 1. Detect courses
        detected_courses = []
        for course_name, patterns in cls.COURSES.items():
            for pat in patterns:
                if re.search(pat, title_lower):
                    if course_name not in detected_courses:
                        detected_courses.append(course_name)
                    break

        # 2. Detect semesters
        detected_sems = []
        for pat, group_count in cls.SEM_PATTERNS:
            for match in re.finditer(pat, title_lower):
                if group_count == 1:
                    sem_num = int(match.group(1))
                    if sem_num not in detected_sems:
                        detected_sems.append(sem_num)
                elif group_count == 2:
                    s_from, s_to = int(match.group(1)), int(match.group(2))
                    for s in range(min(s_from, s_to), max(s_from, s_to) + 1):
                        if 1 <= s <= 8 and s not in detected_sems:
                            detected_sems.append(s)

        detected_sems.sort()

        # 3. Detect exam / notice types
        detected_types = []
        for type_name, patterns in cls.EXAM_TYPES.items():
            for pat in patterns:
                if re.search(pat, title_lower):
                    if type_name not in detected_types:
                        detected_types.append(type_name)
                    break

        # 4. Generate Hashtags
        hashtags = ['#GTU']
        for c in detected_courses:
            hashtags.append(f"#{c}")
        for s in detected_sems:
            hashtags.append(f"#Sem{s}")
        for t in detected_types:
            clean_tag = re.sub(r'[^a-zA-Z0-9]', '', t)
            if clean_tag:
                hashtags.append(f"#{clean_tag}")

        if len(hashtags) == 1:
            hashtags.append('#CircularUpdate')

        return {
            'courses': detected_courses,
            'semesters': detected_sems,
            'exam_types': detected_types,
            'hashtags': hashtags
        }

    @classmethod
    def format_hashtag_string(cls, tags: Dict[str, Any]) -> str:
        """Return space-separated hashtag string."""
        return " ".join(tags.get('hashtags', ['#GTU', '#Circular']))
