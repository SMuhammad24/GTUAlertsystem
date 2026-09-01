import smtplib
import time
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Tuple, Optional
from config import Config

class OTPService:
    """
    In-memory OTP generation, email delivery via SMTP, and verification service.
    """
    _store: Dict[str, Dict] = {}  # email -> { 'otp': '1234', 'expires_at': timestamp, 'attempts': 0 }

    @classmethod
    def generate_otp(cls, email: str, expiry_seconds: int = 300) -> str:
        """Generate and store a 4-digit OTP for the given email (valid for 5 mins)."""
        clean_email = email.strip().lower()
        otp = f"{random.randint(1000, 9999)}"
        cls._store[clean_email] = {
            'otp': otp,
            'expires_at': time.time() + expiry_seconds,
            'attempts': 0
        }
        return otp

    @classmethod
    def verify_otp(cls, email: str, user_otp: str) -> Tuple[bool, str]:
        """Verify the submitted OTP against stored code."""
        clean_email = email.strip().lower()
        record = cls._store.get(clean_email)

        # Allow fallback universal demo OTP '1234' for quick testing
        if user_otp.strip() == '1234':
            return True, "Verified with demo code."

        if not record:
            return False, "OTP not requested or expired. Please request a new code."

        if time.time() > record['expires_at']:
            del cls._store[clean_email]
            return False, "OTP has expired. Please request a new code."

        if record['attempts'] >= 5:
            del cls._store[clean_email]
            return False, "Too many failed attempts. Please request a new code."

        if record['otp'] == user_otp.strip():
            del cls._store[clean_email]
            return True, "Verification successful!"

        record['attempts'] += 1
        remaining = 5 - record['attempts']
        return False, f"Incorrect code. {remaining} attempts remaining."

    @classmethod
    def send_otp_email(cls, to_email: str, otp: str, student_name: str = "Student") -> Tuple[bool, str]:
        """
        Send a beautifully styled HTML OTP email via Gmail SMTP.
        """
        smtp_email = (
            os.getenv('EMAIL_SENDER')
            or os.getenv('SMTP_EMAIL')
            or getattr(Config, 'SMTP_EMAIL', '')
            or ''
        ).strip()
        smtp_pass = (
            os.getenv('EMAIL_PASSWORD')
            or os.getenv('SMTP_PASSWORD')
            or getattr(Config, 'SMTP_PASSWORD', '')
            or ''
        ).strip().replace(' ', '')
        smtp_server = (
            os.getenv('SMTP_SERVER')
            or getattr(Config, 'SMTP_SERVER', '')
            or 'smtp.gmail.com'
        ).strip()
        smtp_port = int(
            os.getenv('SMTP_PORT')
            or getattr(Config, 'SMTP_PORT', None)
            or 587
        )

        print(f"[OTP Service] Attempting to send OTP email to '{to_email}' via sender '{smtp_email}' (has_pass={bool(smtp_pass)})")

        if not smtp_email or not smtp_pass:
            print(f"[OTP Service] ERROR: Missing SMTP credentials. Please configure EMAIL_SENDER and EMAIL_PASSWORD.")
            return False, "SMTP email or password is not configured."

        subject = f"GTU Alerts: Your Verification Code is {otp}"
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; }}
    .container {{ max-width: 520px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }}
    .header {{ background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); color: #ffffff; padding: 28px 24px; text-align: center; }}
    .header h1 {{ margin: 0; font-size: 22px; font-weight: 700; letter-spacing: -0.5px; }}
    .header p {{ margin: 6px 0 0 0; opacity: 0.9; font-size: 13px; }}
    .content {{ padding: 32px 28px; text-align: center; }}
    .greeting {{ font-size: 16px; color: #1e293b; margin-bottom: 12px; text-align: left; }}
    .info {{ font-size: 14px; color: #64748b; line-height: 1.5; text-align: left; margin-bottom: 24px; }}
    .otp-card {{ background: #f1f5f9; border: 2px dashed #94a3b8; border-radius: 10px; padding: 18px; margin: 20px 0; }}
    .otp-code {{ font-size: 34px; font-weight: 800; letter-spacing: 10px; color: #1e3a8a; margin: 0; }}
    .expiry {{ font-size: 12px; color: #94a3b8; margin-top: 8px; }}
    .footer {{ background: #f8fafc; padding: 18px 24px; text-align: center; border-top: 1px solid #e2e8f0; font-size: 12px; color: #94a3b8; }}
    .badge {{ display: inline-block; background: #dbeafe; color: #1e40af; font-size: 11px; font-weight: 600; padding: 3px 8px; border-radius: 12px; margin-bottom: 10px; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🎓 Gujarat Technological University</h1>
      <p>Automated Circulars & Alerts Portal</p>
    </div>
    <div class="content">
      <div class="badge">SECURE VERIFICATION</div>
      <div class="greeting">Hello, <strong>{student_name}</strong>!</div>
      <div class="info">
        Use the following 4-digit verification code to activate your personalized GTU alert preferences for circulars, exam dates, and penalty deadlines:
      </div>
      
      <div class="otp-card">
        <div class="otp-code">{otp}</div>
        <div class="expiry">⏱️ Valid for 5 minutes only. Do not share this code with anyone.</div>
      </div>
      
      <p style="font-size: 13px; color: #64748b; text-align: left; margin-top: 20px;">
        If you did not request this verification, you can safely ignore this email.
      </p>
    </div>
    <div class="footer">
      GTU Automated Notification System • Powered by ICT Dev Force
    </div>
  </div>
</body>
</html>
"""

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"GTU Alert System <{smtp_email}>"
        msg['To'] = to_email

        text_fallback = f"Hello {student_name},\n\nYour GTU Alert verification code is: {otp}\n\nThis code is valid for 5 minutes."
        msg.attach(MIMEText(text_fallback, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))

        try:
            with smtplib.SMTP(smtp_server, smtp_port, timeout=12) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(smtp_email, smtp_pass)
                server.sendmail(smtp_email, [to_email], msg.as_string())
            return True, "Email sent successfully!"
        except smtplib.SMTPAuthenticationError as e:
            return False, f"SMTP Authentication failed: {e.smtp_error.decode('utf-8', 'ignore') if hasattr(e, 'smtp_error') else str(e)}"
        except Exception as e:
            return False, f"Failed to send email: {str(e)}"
