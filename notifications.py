"""
notifications.py — Desktop notification system using plyer.
Sends check-in reminders, streak alerts, and periodic motivational nudges.
"""

import time
import threading
from datetime import datetime, timedelta

try:
    from plyer import notification as plyer_notif
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False


class NotificationManager:
    """Manages desktop notifications and background scheduling."""

    def __init__(self, db=None):
        self.db = db
        self._scheduler_running = False
        self._scheduler_thread = None
        self._checkin_time = "20:00"  # Default: 8 PM
        self._nudge_interval = 3  # Hours between nudges
        self._streak_warned = False

    def send(self, title: str, message: str):
        """Send a desktop notification."""
        if not PLYER_AVAILABLE:
            return

        try:
            plyer_notif.notify(
                title=title,
                message=message,
                app_name="AI Coach",
                timeout=10,
            )
        except Exception:
            pass

    def send_checkin_reminder(self):
        self.send("Time for your check-in", "How was your day? Your coach is waiting.")

    def send_streak_reminder(self, streak: int):
        self.send(
            f"You're on a {streak}-day streak!",
            "Don't break it — do your check-in today.",
        )

    def send_motivational_nudge(self):
        """Send a contextual motivational nudge based on user data."""
        if not self.db:
            self.send("Quick check", "How's your day going? Open AI Coach when you get a sec.")
            return

        # Pick a nudge based on context
        goals = self.db.get_active_goals()
        streak = self.db.get_streak()

        nudge_messages = []

        if goals:
            top_goal = goals[0]
            if top_goal["progress"] < 30:
                nudge_messages.append(
                    (f"Goal reminder: {top_goal['title']}",
                     f"Currently at {top_goal['progress']}%. What's one small step you can take right now?")
                )
            elif top_goal["progress"] >= 70:
                nudge_messages.append(
                    (f"Almost there: {top_goal['title']}",
                     f"You're at {top_goal['progress']}%! Push through the finish line.")
                )

        if streak >= 3:
            nudge_messages.append(
                (f"{streak}-day streak going strong",
                 "Consistency is the game. Keep it rolling.")
            )

        nudge_messages.append(
            ("Quick thought", "What's one thing you're proud of today? Tell your coach.")
        )

        # Pick one
        import random
        title, message = random.choice(nudge_messages)
        self.send(title, message)

    # ─── Scheduler ────────────────────────────────

    def start_scheduler(self, checkin_time: str = None):
        if checkin_time:
            self._checkin_time = checkin_time
        if self._scheduler_running:
            return
        self._scheduler_running = True
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()

    def stop_scheduler(self):
        self._scheduler_running = False

    def set_checkin_time(self, time_str: str):
        self._checkin_time = time_str

    def get_checkin_time(self) -> str:
        return self._checkin_time

    def set_nudge_interval(self, hours: int):
        self._nudge_interval = max(1, min(hours, 12))

    def get_nudge_interval(self) -> int:
        return self._nudge_interval

    def _scheduler_loop(self):
        """Background loop — check-in reminder + periodic nudges."""
        last_checkin_date = None
        last_streak_date = None
        last_nudge_time = None

        while self._scheduler_running:
            now = datetime.now()
            today = now.date()
            current_time = now.strftime("%H:%M")

            # ── Daily check-in reminder ───────────
            if current_time == self._checkin_time and last_checkin_date != today:
                self.send_checkin_reminder()
                last_checkin_date = today

            # ── Streak reminder (1hr before check-in) ──
            try:
                checkin_hour, checkin_min = map(int, self._checkin_time.split(":"))
                reminder_time = (datetime(now.year, now.month, now.day,
                                          checkin_hour, checkin_min) - timedelta(hours=1))
                reminder_str = reminder_time.strftime("%H:%M")

                if current_time == reminder_str and last_streak_date != today:
                    if self.db:
                        streak = self.db.get_streak()
                        if streak >= 2:
                            checkins = self.db.get_recent_checkins(1)
                            if checkins:
                                last_date = checkins[-1].get("created_at", "")[:10]
                                if last_date != str(today):
                                    self.send_streak_reminder(streak)
                            else:
                                self.send_streak_reminder(streak)
                    last_streak_date = today
            except Exception:
                pass

            # ── Periodic motivational nudges ──────
            if self._nudge_interval > 0:
                should_nudge = False
                if last_nudge_time is None:
                    # First nudge after 1 interval
                    last_nudge_time = now
                elif (now - last_nudge_time).total_seconds() >= self._nudge_interval * 3600:
                    should_nudge = True

                # Only nudge during waking hours (8 AM - 10 PM)
                if should_nudge and 8 <= now.hour <= 22:
                    self.send_motivational_nudge()
                    last_nudge_time = now

            time.sleep(60)  # Check every minute
