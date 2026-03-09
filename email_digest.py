"""
email_digest.py — Email notifications for daily/weekly summaries.
Uses SMTP (Gmail compatible) to send mood trends, goal progress, and coaching nudges.
"""

import smtplib
import threading
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()


class EmailDigest:
    """Sends daily/weekly email digests with mood + goal summaries."""

    def __init__(self, db=None):
        self.db = db
        self._smtp_email = os.getenv("SMTP_EMAIL", "")
        self._smtp_password = os.getenv("SMTP_PASSWORD", "")
        self._smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self._smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self._recipient = os.getenv("USER_EMAIL", "")
        self._scheduler_running = False
        self._digest_time = "09:00"  # Default: 9 AM

    @property
    def is_configured(self) -> bool:
        return bool(self._smtp_email and self._smtp_password and self._recipient)

    def send_email(self, subject: str, html_body: str) -> bool:
        """Send an email. Returns True on success."""
        if not self.is_configured:
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = self._smtp_email
            msg["To"] = self._recipient
            msg["Subject"] = subject

            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(self._smtp_host, self._smtp_port) as server:
                server.starttls()
                server.login(self._smtp_email, self._smtp_password)
                server.sendmail(self._smtp_email, self._recipient, msg.as_string())
            return True
        except Exception:
            return False

    def build_daily_digest(self) -> tuple:
        """Build daily digest email. Returns (subject, html_body)."""
        if not self.db:
            return ("", "")

        today = datetime.now().strftime("%B %d, %Y")
        streak = self.db.get_streak()

        # Get recent emotions
        emotion_summary = self.db.get_emotion_summary(1)
        top_emotion = "neutral"
        if emotion_summary["count"] > 0:
            breakdown = emotion_summary["breakdown"]
            if breakdown:
                top_emotion = max(breakdown, key=breakdown.get)

        # Get active goals
        goals = self.db.get_active_goals()
        goals_html = ""
        if goals:
            for g in goals:
                bar_width = max(g["progress"], 2)
                goals_html += f"""
                <tr>
                    <td style="padding:8px 0;color:#ffffff;font-size:14px;">{g['title']}</td>
                    <td style="padding:8px 0;width:120px;">
                        <div style="background:#1a1a1a;border-radius:4px;height:6px;overflow:hidden;">
                            <div style="background:#ffffff;height:100%;width:{bar_width}%;border-radius:4px;"></div>
                        </div>
                    </td>
                    <td style="padding:8px 0;color:#888;font-size:12px;text-align:right;width:50px;">{g['progress']}%</td>
                </tr>"""
        else:
            goals_html = '<tr><td style="color:#555;padding:8px 0;">No goals set yet.</td></tr>'

        # Get recent check-in
        checkins = self.db.get_recent_checkins(1)
        checkin_text = "No check-in yesterday."
        if checkins:
            last = checkins[-1]
            checkin_text = f"Mood: {last.get('mood_label', 'unknown')} ({last.get('mood_score', '?')}/10)"

        subject = f"AI Coach — Your Daily Summary ({today})"

        html_body = f"""
        <div style="background:#0a0a0a;padding:40px 20px;font-family:'Inter',Arial,sans-serif;">
            <div style="max-width:500px;margin:0 auto;">
                <h1 style="color:#ffffff;font-size:24px;font-weight:300;margin:0 0 4px 0;letter-spacing:-0.02em;">
                    AI Coach
                </h1>
                <p style="color:#555;font-size:12px;letter-spacing:0.05em;margin:0 0 30px 0;">
                    DAILY DIGEST — {today.upper()}
                </p>

                <div style="background:#0f0f0f;border:1px solid #1e1e1e;border-radius:8px;padding:20px;margin-bottom:16px;">
                    <table style="width:100%;">
                        <tr>
                            <td style="text-align:center;padding:10px;">
                                <p style="color:#ffffff;font-size:32px;font-weight:300;margin:0;">{streak}</p>
                                <p style="color:#555;font-size:10px;text-transform:uppercase;letter-spacing:0.1em;margin:4px 0 0 0;">Day Streak</p>
                            </td>
                            <td style="text-align:center;padding:10px;">
                                <p style="color:#ffffff;font-size:16px;font-weight:400;margin:0;">{top_emotion}</p>
                                <p style="color:#555;font-size:10px;text-transform:uppercase;letter-spacing:0.1em;margin:4px 0 0 0;">Top Mood</p>
                            </td>
                        </tr>
                    </table>
                </div>

                <div style="background:#0f0f0f;border:1px solid #1e1e1e;border-radius:8px;padding:20px;margin-bottom:16px;">
                    <p style="color:#888;font-size:10px;text-transform:uppercase;letter-spacing:0.1em;margin:0 0 12px 0;">Goals</p>
                    <table style="width:100%;">
                        {goals_html}
                    </table>
                </div>

                <div style="background:#0f0f0f;border:1px solid #1e1e1e;border-radius:8px;padding:20px;margin-bottom:16px;">
                    <p style="color:#888;font-size:10px;text-transform:uppercase;letter-spacing:0.1em;margin:0 0 8px 0;">Last Check-in</p>
                    <p style="color:#d0d0d0;font-size:14px;font-weight:300;margin:0;">{checkin_text}</p>
                </div>

                <p style="color:#333;font-size:11px;text-align:center;margin-top:30px;">
                    AI Coach Companion — Local-first personal coaching
                </p>
            </div>
        </div>
        """

        return subject, html_body

    def send_daily_digest(self) -> bool:
        """Build and send the daily digest email."""
        subject, body = self.build_daily_digest()
        if subject:
            return self.send_email(subject, body)
        return False

    # ── Scheduled Email ───────────────────────────

    def start_scheduler(self, digest_time: str = "09:00"):
        """Start background scheduler for daily email digest."""
        if self._scheduler_running:
            return

        self._digest_time = digest_time
        self._scheduler_running = True
        thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        thread.start()

    def stop_scheduler(self):
        self._scheduler_running = False

    def _scheduler_loop(self):
        last_sent_date = None
        while self._scheduler_running:
            now = datetime.now()
            today = now.date()
            current_time = now.strftime("%H:%M")

            if current_time == self._digest_time and last_sent_date != today:
                self.send_daily_digest()
                last_sent_date = today

            time.sleep(60)

    def set_digest_time(self, time_str: str):
        self._digest_time = time_str

    def get_digest_time(self) -> str:
        return self._digest_time
