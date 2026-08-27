"""
Generate a professional PDF Presentation Deck for GTU Automation Project
Using ReportLab Platypus engine for clean typography, colors, tables, and borders.
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas
import sys
import os

class NumberedCanvas(canvas.Canvas):
    """Canvas that adds page numbers and running header/footer."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        if self._pageNumber == 1:
            return  # Suppress headers/footers on cover slide
        
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#1e3a8a"))
        
        # Header
        self.drawString(36, 805, "🎓 GTU AUTOMATED CIRCULAR & ALERT SYSTEM")
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawRightString(559, 805, "Project Presentation & Defense Deck")
        
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.75)
        self.line(36, 797, 559, 797)
        
        # Footer
        self.line(36, 42, 559, 42)
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawString(36, 30, "Confidential - Academic & Project Presentation")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(559, 30, page_str)
        self.restoreState()


def build_pdf(filename="GTU_Project_Presentation.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=50,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    primary_color = colors.HexColor("#1e3a8a")
    dark_slate = colors.HexColor("#0f172a")
    text_color = colors.HexColor("#1e293b")
    green_color = colors.HexColor("#15803d")
    red_color = colors.HexColor("#b91c1c")

    title_style = ParagraphStyle(
        'SlideTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=primary_color,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'SlideSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=14
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=text_color
    )

    bullet_style = ParagraphStyle(
        'BulletText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=text_color
    )

    speaker_note_style = ParagraphStyle(
        'SpeakerNote',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#92400e")
    )

    story = []

    # ==================== PAGE 1: COVER SLIDE ====================
    story.append(Spacer(1, 40))
    
    # Badge
    badge_data = [[
        Paragraph("<font color='#1e40af'><b>ACADEMIC PROJECT PRESENTATION • 2026</b></font>", 
                  ParagraphStyle('Badge', alignment=1, fontSize=9, fontName='Helvetica-Bold'))
    ]]
    badge_table = Table(badge_data, colWidths=[280])
    badge_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#dbeafe")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('LINEBELOW', (0, 0), (-1, -1), 1, colors.HexColor("#93c5fd")),
    ]))
    story.append(badge_table)
    story.append(Spacer(1, 20))

    # Main Title
    cover_title_p = Paragraph(
        "<font color='#0f172a'><b>GTU Automated Circular &amp;<br/>Notification Alert System</b></font>",
        ParagraphStyle('CoverTitle', alignment=1, fontSize=24, leading=28, fontName='Helvetica-Bold')
    )
    story.append(cover_title_p)
    story.append(Spacer(1, 10))

    cover_sub_p = Paragraph(
        "<font color='#475569'>Real-Time University Notice Broadcast with Zero-Latency &amp; Direct 1-Click Official PDF Links</font>",
        ParagraphStyle('CoverSub', alignment=1, fontSize=11, leading=15, fontName='Helvetica')
    )
    story.append(cover_sub_p)
    story.append(Spacer(1, 30))

    # Metadata Card
    meta_data = [
        [
            Paragraph("<b>PROJECT DOMAIN:</b>", ParagraphStyle('M1', fontSize=8, fontName='Helvetica-Bold', textColor=primary_color)),
            Paragraph("Web Automation &amp; Cloud Messaging", ParagraphStyle('M2', fontSize=9, fontName='Helvetica', textColor=text_color))
        ],
        [
            Paragraph("<b>CORE TECH STACK:</b>", ParagraphStyle('M1', fontSize=8, fontName='Helvetica-Bold', textColor=primary_color)),
            Paragraph("Python 3, BeautifulSoup4, SQLite3, Telegram API", ParagraphStyle('M2', fontSize=9, fontName='Helvetica', textColor=text_color))
        ],
        [
            Paragraph("<b>TARGET BENEFICIARIES:</b>", ParagraphStyle('M1', fontSize=8, fontName='Helvetica-Bold', textColor=primary_color)),
            Paragraph("GTU Engineering / Diploma / Degree Students &amp; Faculty", ParagraphStyle('M2', fontSize=9, fontName='Helvetica', textColor=text_color))
        ],
        [
            Paragraph("<b>DATA PRIVACY POLICY:</b>", ParagraphStyle('M1', fontSize=8, fontName='Helvetica-Bold', textColor=colors.HexColor("#15803d"))),
            Paragraph("<b>100% Public Notice Board Only • Zero Student Data Access</b>", ParagraphStyle('M2', fontSize=9, fontName='Helvetica-Bold', textColor=colors.HexColor("#15803d")))
        ]
    ]
    meta_table = Table(meta_data, colWidths=[150, 330])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 35))

    # Privacy Banner on Cover
    priv_box_data = [[
        Paragraph(
            "<font color='#065f46'><b>🔒 SECURITY &amp; ETHICAL GUARANTEE:</b><br/>"
            "This project strictly monitors <b>open public notices</b> published at <code>gtu.ac.in</code>. "
            "It does <b>NOT</b> require, extract, store, or transmit any student credentials, enrolment numbers, passwords, or private information.</font>",
            ParagraphStyle('PrivCover', fontSize=9, leading=13, fontName='Helvetica')
        )
    ]]
    priv_box_table = Table(priv_box_data, colWidths=[480])
    priv_box_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#ecfdf5")),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor("#10b981")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
    ]))
    story.append(priv_box_table)

    story.append(PageBreak())

    # ==================== PAGE 2: PROBLEM STATEMENT & OBJECTIVES ====================
    story.append(Paragraph("1. Problem Statement &amp; Solution Vision", title_style))
    story.append(Paragraph("Why students miss critical deadlines and how automated notification bridges the gap.", subtitle_style))

    col1_content = [
        Paragraph("<font color='#b91c1c'><b>❌ Current Challenges &amp; Inefficiencies</b></font>", ParagraphStyle('H', fontSize=10, fontName='Helvetica-Bold', spaceAfter=6)),
        Paragraph("• <b>Late Fee Penalties:</b> Exam registration &amp; penalty deadlines are frequently missed due to lack of timely alerts.", bullet_style),
        Spacer(1, 4),
        Paragraph("• <b>Manual Friction:</b> Visiting <code>gtu.ac.in</code> daily on mobile devices is tedious and easily forgotten.", bullet_style),
        Spacer(1, 4),
        Paragraph("• <b>Information Overload:</b> 10-20 mixed notices are released daily; filtering branch-relevant news is difficult.", bullet_style),
        Spacer(1, 4),
        Paragraph("• <b>Faculty Burden:</b> Class coordinators manually download &amp; forward circular PDFs in multiple WhatsApp groups.", bullet_style)
    ]

    col2_content = [
        Paragraph("<font color='#15803d'><b>✅ The Automated Solution</b></font>", ParagraphStyle('H', fontSize=10, fontName='Helvetica-Bold', spaceAfter=6)),
        Paragraph("• <b>Instant Mobile Delivery:</b> Scans GTU public board every 15 min &amp; broadcasts alerts directly to Telegram.", bullet_style),
        Spacer(1, 4),
        Paragraph("• <b>Direct 1-Click PDF Link:</b> Students can view official circulars instantly with one tap inside the message.", bullet_style),
        Spacer(1, 4),
        Paragraph("• <b>Smart Urgency Tagging:</b> Distinct visual badges for Fee Deadlines (🚨), Timetables (📝), and Results (📊).", bullet_style),
        Spacer(1, 4),
        Paragraph("• <b>24/7 Cloud Autonomy:</b> Continuous monitoring via GitHub Actions with 0 server maintenance cost.", bullet_style)
    ]

    prob_sol_table = Table([[col1_content, col2_content]], colWidths=[240, 240])
    prob_sol_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor("#fef2f2")),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor("#f0fdf4")),
        ('BOX', (0, 0), (0, 0), 1, colors.HexColor("#fca5a5")),
        ('BOX', (1, 0), (1, 0), 1, colors.HexColor("#86efac")),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(prob_sol_table)
    story.append(Spacer(1, 14))

    # Core Objectives 3-box Grid
    obj_box1 = [Paragraph("<b>Zero Delay</b>", ParagraphStyle('OB', fontSize=9, fontName='Helvetica-Bold', textColor=primary_color)),
                Paragraph("Push updates within minutes of public posting.", ParagraphStyle('OT', fontSize=8, textColor=colors.HexColor("#475569")))]
    obj_box2 = [Paragraph("<b>Zero Spam</b>", ParagraphStyle('OB', fontSize=9, fontName='Helvetica-Bold', textColor=primary_color)),
                Paragraph("SQLite deduplication guarantees 1 post per notice.", ParagraphStyle('OT', fontSize=8, textColor=colors.HexColor("#475569")))]
    obj_box3 = [Paragraph("<b>Zero Cost</b>", ParagraphStyle('OB', fontSize=9, fontName='Helvetica-Bold', textColor=primary_color)),
                Paragraph("Free cloud execution &amp; open-source Python stack.", ParagraphStyle('OT', fontSize=8, textColor=colors.HexColor("#475569")))]

    obj_table = Table([[obj_box1, obj_box2, obj_box3]], colWidths=[156, 156, 156])
    obj_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(obj_table)
    story.append(Spacer(1, 14))

    # Speaker Box
    speaker_data = [[
        Paragraph("<b>🗣️ Presentation Script (Talking Point for Faculty):</b><br/>"
                  "<i>'Respected Sir/Ma'am, students often face heavy exam penalties due to missing manual checks on GTU's site. Our system bridges this gap by automatically detecting new notices the moment GTU uploads them and sending rich alerts to student groups.'</i>",
                  speaker_note_style)
    ]]
    spk_table = Table(speaker_data, colWidths=[480])
    spk_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#fffbeb")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#fde68a")),
        ('LINELEFT', (0, 0), (-1, -1), 3, colors.HexColor("#d97706")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(spk_table)

    story.append(PageBreak())

    # ==================== PAGE 3: STRICT DATA PRIVACY & COMPLIANCE ====================
    story.append(Paragraph("2. Strict Data Privacy &amp; Ethical Compliance", title_style))
    story.append(Paragraph("Absolute assurance regarding zero private student data access and safe university server usage.", subtitle_style))

    # Guarantee Highlight Card
    big_guarantee = [[
        Paragraph(
            "<font color='#15803d' size='11'><b>🛡️ 100% ZERO STUDENT DATA ACCESS POLICY</b></font><br/>"
            "<font color='#166534' size='9'>This application acts strictly as an <b>Automated Public Reader</b>. It does <b>NOT</b> require, extract, or store any student enrolment number, password, name, phone number, or academic record from GTU or any student.</font>",
            ParagraphStyle('BG', leading=13.5)
        )
    ]]
    big_g_table = Table(big_guarantee, colWidths=[480])
    big_g_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#dcfce7")),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor("#22c55e")),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(big_g_table)
    story.append(Spacer(1, 12))

    # Compliance Matrix Table
    matrix_data = [
        [
            Paragraph("<b>Data Domain</b>", ParagraphStyle('TH', fontSize=8.5, fontName='Helvetica-Bold', textColor=colors.white)),
            Paragraph("<b>Access Status</b>", ParagraphStyle('TH', fontSize=8.5, fontName='Helvetica-Bold', textColor=colors.white)),
            Paragraph("<b>Technical Reason &amp; Compliance Details</b>", ParagraphStyle('TH', fontSize=8.5, fontName='Helvetica-Bold', textColor=colors.white))
        ],
        [
            Paragraph("<b>Student Personal Data</b>", ParagraphStyle('TD', fontSize=8.5, fontName='Helvetica-Bold')),
            Paragraph("<font color='#b91c1c'><b>ZERO ACCESS</b></font>", ParagraphStyle('TD', fontSize=8.5)),
            Paragraph("No enrolment numbers, names, emails, mobile numbers, or passwords are ever requested or saved.", ParagraphStyle('TD', fontSize=8))
        ],
        [
            Paragraph("<b>Login &amp; Auth Portals</b>", ParagraphStyle('TD', fontSize=8.5, fontName='Helvetica-Bold')),
            Paragraph("<font color='#b91c1c'><b>NEVER ACCESSED</b></font>", ParagraphStyle('TD', fontSize=8.5)),
            Paragraph("No access to <code>student.gtu.ac.in</code> or ERP logins; no CAPTCHA bypass attempted.", ParagraphStyle('TD', fontSize=8))
        ],
        [
            Paragraph("<b>Information Source</b>", ParagraphStyle('TD', fontSize=8.5, fontName='Helvetica-Bold')),
            Paragraph("<font color='#15803d'><b>PUBLIC ONLY</b></font>", ParagraphStyle('TD', fontSize=8.5)),
            Paragraph("Only reads public circulars table at <code>gtu.ac.in/Circular.aspx</code> visible openly to everyone.", ParagraphStyle('TD', fontSize=8))
        ],
        [
            Paragraph("<b>Data Extracted</b>", ParagraphStyle('TD', fontSize=8.5, fontName='Helvetica-Bold')),
            Paragraph("<font color='#15803d'><b>PUBLIC METADATA</b></font>", ParagraphStyle('TD', fontSize=8.5)),
            Paragraph("Only extracts 3 public fields: Circular Title, Publication Date, and Official Public PDF Download URL.", ParagraphStyle('TD', fontSize=8))
        ],
        [
            Paragraph("<b>GTU Server Load</b>", ParagraphStyle('TD', fontSize=8.5, fontName='Helvetica-Bold')),
            Paragraph("<font color='#15803d'><b>RATE-LIMITED</b></font>", ParagraphStyle('TD', fontSize=8.5)),
            Paragraph("Safe 15-minute polling interval with standard User-Agent headers creates less load than 1 human user.", ParagraphStyle('TD', fontSize=8))
        ]
    ]

    matrix_table = Table(matrix_data, colWidths=[120, 100, 260])
    matrix_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor("#f8fafc")),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor("#ffffff")),
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor("#f8fafc")),
        ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor("#ffffff")),
        ('BACKGROUND', (0, 5), (-1, 5), colors.HexColor("#f8fafc")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(matrix_table)
    story.append(Spacer(1, 12))

    # Speaker Box
    speaker_data2 = [[
        Paragraph("<b>🗣️ Presentation Script (Talking Point for Privacy Defense):</b><br/>"
                  "<i>'Sir/Ma'am, we specifically ensured that our bot strictly acts as a public broadcaster. It operates without any logins or student personal records. It only retrieves what GTU has already made publicly accessible for all students on its website.'</i>",
                  speaker_note_style)
    ]]
    spk_table2 = Table(speaker_data2, colWidths=[480])
    spk_table2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#fffbeb")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#fde68a")),
        ('LINELEFT', (0, 0), (-1, -1), 3, colors.HexColor("#d97706")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(spk_table2)

    story.append(PageBreak())

    # ==================== PAGE 4: ARCHITECTURE & SMART FEATURES ====================
    story.append(Paragraph("3. System Architecture &amp; Smart Features", title_style))
    story.append(Paragraph("High-level execution workflow and intelligent category tagging engine.", subtitle_style))

    # Workflow Steps
    w1 = [Paragraph("<b>Step 1: Public Web Scraper</b>", ParagraphStyle('W1', fontSize=8.5, fontName='Helvetica-Bold', textColor=primary_color)),
          Paragraph("Fetches <code>gtu.ac.in/Circular.aspx</code> using BeautifulSoup parser.", ParagraphStyle('W2', fontSize=8, textColor=text_color))]
    w2 = [Paragraph("<b>Step 2: Category Classifier</b>", ParagraphStyle('W1', fontSize=8.5, fontName='Helvetica-Bold', textColor=primary_color)),
          Paragraph("Identifies Fee deadlines, Exam notices, Results, &amp; Timetables.", ParagraphStyle('W2', fontSize=8, textColor=text_color))]
    w3 = [Paragraph("<b>Step 3: SQLite Deduplication</b>", ParagraphStyle('W1', fontSize=8.5, fontName='Helvetica-Bold', textColor=primary_color)),
          Paragraph("Checks <code>circulars.db</code> to discard previously notified records.", ParagraphStyle('W2', fontSize=8, textColor=text_color))]
    w4 = [Paragraph("<b>Step 4: Push Broadcast</b>", ParagraphStyle('W1', fontSize=8.5, fontName='Helvetica-Bold', textColor=primary_color)),
          Paragraph("Sends rich HTML message with 1-click PDF link to Telegram group.", ParagraphStyle('W2', fontSize=8, textColor=text_color))]

    workflow_table = Table([[w1, w2], [w3, w4]], colWidths=[240, 240])
    workflow_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(workflow_table)
    story.append(Spacer(1, 14))

    # Smart Categorization Badges Grid
    cat_header = Paragraph("<b>Intelligent Urgency Categorization Badges</b>", ParagraphStyle('CH', fontSize=10, fontName='Helvetica-Bold', textColor=dark_slate))
    story.append(cat_header)
    story.append(Spacer(1, 6))

    c1 = [Paragraph("🚨 <b>Fee &amp; Penalty Alerts</b>", ParagraphStyle('CB', fontSize=8.5, fontName='Helvetica-Bold', textColor=red_color)),
          Paragraph("Highlights regular/remedial exam fees &amp; penalty dates.", ParagraphStyle('CT', fontSize=8, textColor=colors.HexColor("#475569")))]
    c2 = [Paragraph("📝 <b>Exams &amp; Timetables</b>", ParagraphStyle('CB', fontSize=8.5, fontName='Helvetica-Bold', textColor=primary_color)),
          Paragraph("Mid-sem &amp; End-sem timetables, hall tickets, and centres.", ParagraphStyle('CT', fontSize=8, textColor=colors.HexColor("#475569")))]
    c3 = [Paragraph("📊 <b>Result Announcements</b>", ParagraphStyle('CB', fontSize=8.5, fontName='Helvetica-Bold', textColor=green_color)),
          Paragraph("Instant alerts for declared semester &amp; recheck results.", ParagraphStyle('CT', fontSize=8, textColor=colors.HexColor("#475569")))]
    c4 = [Paragraph("🎓 <b>Academic &amp; Admission</b>", ParagraphStyle('CB', fontSize=8.5, fontName='Helvetica-Bold', textColor=colors.HexColor("#d97706"))),
          Paragraph("Syllabus changes, academic calendar, and enrollment.", ParagraphStyle('CT', fontSize=8, textColor=colors.HexColor("#475569")))]

    cat_table = Table([[c1, c2], [c3, c4]], colWidths=[240, 240])
    cat_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor("#fef2f2")),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor("#eff6ff")),
        ('BACKGROUND', (0, 1), (0, 1), colors.HexColor("#f0fdf4")),
        ('BACKGROUND', (1, 1), (1, 1), colors.HexColor("#fffbeb")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(cat_table)
    story.append(Spacer(1, 14))

    # Tech Stack Table
    tech_data = [
        [
            Paragraph("<b>Core Language</b>", ParagraphStyle('TK', fontSize=8, fontName='Helvetica-Bold')),
            Paragraph("Python 3.10+ (Standard Web Scraping &amp; Async Libraries)", ParagraphStyle('TV', fontSize=8))
        ],
        [
            Paragraph("<b>Web Parsing</b>", ParagraphStyle('TK', fontSize=8, fontName='Helvetica-Bold')),
            Paragraph("BeautifulSoup4 + Requests with custom HTTP Header handlers", ParagraphStyle('TV', fontSize=8))
        ],
        [
            Paragraph("<b>Database Engine</b>", ParagraphStyle('TK', fontSize=8, fontName='Helvetica-Bold')),
            Paragraph("SQLite3 (Zero-latency local deduplication storage)", ParagraphStyle('TV', fontSize=8))
        ],
        [
            Paragraph("<b>Cloud Infrastructure</b>", ParagraphStyle('TK', fontSize=8, fontName='Helvetica-Bold')),
            Paragraph("GitHub Actions Cloud Cron (24/7 Free Scheduled Autonomous Runner)", ParagraphStyle('TV', fontSize=8))
        ]
    ]
    tech_table = Table(tech_data, colWidths=[130, 350])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(tech_table)

    story.append(PageBreak())

    # ==================== PAGE 5: IMPACT & VIVA DEFENSE FAQ ====================
    story.append(Paragraph("4. Real-World Impact &amp; Viva Defense FAQ", title_style))
    story.append(Paragraph("Quantifiable benefits and prepared defenses for faculty viva questions.", subtitle_style))

    # Benefits
    b1 = [Paragraph("<b>Student Benefits</b>", ParagraphStyle('BH', fontSize=9, fontName='Helvetica-Bold', textColor=green_color)),
          Paragraph("• Zero late fee penalties.<br/>• Instant PDF access without slow web navigation.<br/>• Mobile-friendly push notifications.", ParagraphStyle('BT', fontSize=8, leading=11))]
    b2 = [Paragraph("<b>College &amp; Faculty Benefits</b>", ParagraphStyle('BH', fontSize=9, fontName='Helvetica-Bold', textColor=primary_color)),
          Paragraph("• Eliminates manual PDF forwarding by CRs/Staff.<br/>• Higher on-time exam form submission rates.<br/>• Demonstrates campus workflow automation.", ParagraphStyle('BT', fontSize=8, leading=11))]

    benefits_table = Table([[b1, b2]], colWidths=[240, 240])
    benefits_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor("#f0fdf4")),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor("#eff6ff")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(benefits_table)
    story.append(Spacer(1, 12))

    # FAQ Defense Section
    faq_header = Paragraph("<b>Frequently Asked Questions (Viva Defenses)</b>", ParagraphStyle('FH', fontSize=10, fontName='Helvetica-Bold', textColor=dark_slate))
    story.append(faq_header)
    story.append(Spacer(1, 6))

    faq_data = [
        [
            Paragraph("<b>Q1: Does this scraper risk crashing GTU's web servers?</b><br/>"
                      "<font color='#334155'><b>Answer:</b> No. The bot makes only 1 lightweight HTTP GET request every 15 minutes, consuming fewer server resources than a single student refreshing the page.</font>",
                      ParagraphStyle('FQ', fontSize=8, leading=11))
        ],
        [
            Paragraph("<b>Q2: Is there any risk of student confidential data breach?</b><br/>"
                      "<font color='#334155'><b>Answer:</b> Zero risk. The bot never requests or stores enrolment numbers, passwords, or personal credentials. It only extracts public circular URLs.</font>",
                      ParagraphStyle('FQ', fontSize=8, leading=11))
        ],
        [
            Paragraph("<b>Q3: What if the hosting machine loses internet connection?</b><br/>"
                      "<font color='#334155'><b>Answer:</b> The project includes an automated GitHub Actions cloud workflow that runs 24/7 on GitHub's cloud servers independently.</font>",
                      ParagraphStyle('FQ', fontSize=8, leading=11))
        ]
    ]

    faq_table = Table(faq_data, colWidths=[480])
    faq_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(faq_table)
    story.append(Spacer(1, 12))

    # Future Roadmap
    future_p = Paragraph(
        "<b>🌟 Future Scope &amp; Roadmap:</b> "
        "(1) <b>WhatsApp Cloud API</b> multi-channel broadcast. "
        "(2) <b>Branch &amp; Semester filtering</b> (Computer/IT/Mech specific channels). "
        "(3) <b>AI Summary Engine (TL;DR)</b> for 1-sentence key takeaway summaries of lengthy PDFs.",
        ParagraphStyle('Fut', fontSize=8, leading=11, textColor=colors.HexColor("#475569"))
    )
    story.append(future_p)

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF: {filename}")

if __name__ == "__main__":
    build_pdf()
