"""
notifications.py — Desktop notifications and scheduled reminders.
Uses plyer for Windows toast notifications and threading for scheduling.
"""

import threading
import time
from datetime import datetime, timedelta
from plyer import notification as plyer_notify


class NotificationManager:
    """Manages desktop notifications and scheduled reminders."""

    def __init__(self, db=None):
        self.db = db
        self._scheduler_running = False
        self._scheduler_thread = None
        self._checkin_time = "20:00"  # Default: 8 PM
        self._streak_warned = False

    # ── Manual Notifications ──────────────────────

    def send(self, title: str, message: str, timeout: int = 10):
        """Send a desktop notification."""
        try:
            plyer_notify.notify(
                title=title,
                message=message,
                app_name="AI Coach",
                timeout=timeout,
            )
        except Exception:
            pass  # Silently fail if notification system unavailable

    def send_checkin_reminder(self):
        """Send daily check-in reminder."""
        self.send(
            title="AI Coach — Daily Check-in",
            message="How was your day? Take 30 seconds to check in and track your progress.",
        )

    def send_streak_reminder(self, streak: int):
        """Send streak at-risk notification."""
        self.send(
            title="AI Coach — Streak Alert",
            message=f"You're on a {streak}-day streak. Don't break it — check in today!",
        )

    def send_goal_nudge(self, goal_title: str):
        """Send a goal follow-up nudge."""
        self.send(
            title="AI Coach — Goal Update",
            message=f"Any progress on '{goal_title}'? Open your coach to update.",
        )

    def send_motivation(self, message: str):
        """Send a motivational notification."""
        self.send(
            title="AI Coach",
            message=message,
        )

    # ── Scheduled Notifications ───────────────────

    def start_scheduler(self, checkin_time: str = "20:00"):
        """Start background scheduler for daily reminders."""
        if self._scheduler_running:
            return

        self._checkin_time = checkin_time
        self._scheduler_running = True
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop, daemon=True
        )
        self._scheduler_thread.start()

    def stop_scheduler(self):
        """Stop background scheduler."""
        self._scheduler_running = False

    def _scheduler_loop(self):
        """Background loop that checks every 60s if it's time to notify."""
        last_checkin_date = None
        last_streak_date = None

        while self._scheduler_running:
            now = datetime.now()
            today = now.date()
            current_time = now.strftime("%H:%M")

            # Daily check-in reminder
            if current_time == self._checkin_time and last_checkin_date != today:
                self.send_checkin_reminder()
                last_checkin_date = today

            # Streak reminder at 1 hour before check-in time
            try:
                checkin_hour, checkin_min = map(int, self._checkin_time.split(":"))
                reminder_time = (datetime(now.year, now.month, now.day,
                                          checkin_hour, checkin_min) - timedelta(hours=1))
                reminder_str = reminder_time.strftime("%H:%M")

                if current_time == reminder_str and last_streak_date != today:
                    if self.db:
                        streak = self.db.get_streak()
                        if streak >= 2:
                            # Check if already checked in today
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

            time.sleep(60)  # Check every minute

    # ── Settings ──────────────────────────────────

    def set_checkin_time(self, time_str: str):
        """Set daily check-in reminder time (HH:MM format)."""
        self._checkin_time = time_str

    def get_checkin_time(self) -> str:
        return self._checkin_time
