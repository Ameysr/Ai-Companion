"""
notifier_bg.py — Lightweight background notifier.
Runs silently in system tray. Sends desktop notifications on schedule.
No Streamlit, no ML models — just SQLite + plyer + pystray.
Auto-starts with Windows if installed via install_startup.bat.
"""

import sys
import time
import random
import threading
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

from storage.database import Database

try:
    from plyer import notification as plyer_notif
    PLYER_OK = True
except ImportError:
    PLYER_OK = False

try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_OK = True
except ImportError:
    TRAY_OK = False


# ── Config ────────────────────────────────────

CHECKIN_TIME = "20:00"       # 8 PM default
NUDGE_INTERVAL_HOURS = 3    # Every 3 hours
CHECK_INTERVAL_SECS = 60    # Check every minute

# Try to read from .env
env_file = PROJECT_DIR / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line.startswith("CHECKIN_TIME="):
            CHECKIN_TIME = line.split("=", 1)[1].strip()
        elif line.startswith("NUDGE_INTERVAL="):
            try:
                NUDGE_INTERVAL_HOURS = int(line.split("=", 1)[1].strip())
            except ValueError:
                pass


# ── Notification Sender ───────────────────────

def send_notification(title: str, message: str):
    if not PLYER_OK:
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


def get_contextual_nudge(db: Database) -> tuple:
    """Generate a contextual nudge message from user data."""
    nudges = []

    try:
        goals = db.get_active_goals()
        streak = db.get_streak()

        if goals:
            g = goals[0]
            if g["progress"] < 20:
                nudges.append((
                    f"Goal: {g['title']}",
                    f"Still at {g['progress']}%. What's one tiny step you can do right now?"
                ))
            elif g["progress"] < 50:
                nudges.append((
                    f"Halfway push: {g['title']}",
                    f"You're at {g['progress']}%. Keep the momentum."
                ))
            elif g["progress"] >= 70:
                nudges.append((
                    f"Almost done: {g['title']}",
                    f"{g['progress']}% complete. Finish line's right there."
                ))

        if streak >= 2:
            nudges.append((
                f"{streak}-day streak",
                "Don't break the chain. You're building something real."
            ))

        recent_emotions = db.get_recent_emotions(3)
        if recent_emotions:
            last_mood = recent_emotions[0].get("emotion_label", "")
            if last_mood in ("sadness", "anxiety", "stress"):
                nudges.append((
                    "Checking in",
                    "Yesterday was heavy. How are you holding up today?"
                ))
    except Exception:
        pass

    # Fallback nudges
    nudges.extend([
        ("Quick thought", "What's one win from today, no matter how small?"),
        ("Coach waiting", "Your AI coach is ready when you are. Open the app."),
        ("Reflection", "Take 10 seconds. How are you feeling right now?"),
    ])

    return random.choice(nudges)


# ── Main Loop ─────────────────────────────────

def notification_loop():
    """Main background loop — runs forever, sends notifications on schedule."""
    db = Database()

    last_checkin_date = None
    last_streak_date = None
    last_nudge_time = datetime.now()

    print(f"[AI Coach] Background notifier started")
    print(f"[AI Coach] Check-in reminder: {CHECKIN_TIME}")
    print(f"[AI Coach] Nudge interval: every {NUDGE_INTERVAL_HOURS}h")

    while True:
        now = datetime.now()
        today = now.date()
        current_time = now.strftime("%H:%M")

        # ── Daily check-in reminder ───────────
        if current_time == CHECKIN_TIME and last_checkin_date != today:
            send_notification(
                "Time for your check-in",
                "How was your day? Your coach is waiting."
            )
            last_checkin_date = today

        # ── Streak reminder (1hr before) ──────
        try:
            h, m = map(int, CHECKIN_TIME.split(":"))
            reminder = datetime(now.year, now.month, now.day, h, m) - timedelta(hours=1)
            if current_time == reminder.strftime("%H:%M") and last_streak_date != today:
                streak = db.get_streak()
                if streak >= 2:
                    checkins = db.get_recent_checkins(1)
                    if checkins:
                        last_date = checkins[-1].get("created_at", "")[:10]
                        if last_date != str(today):
                            send_notification(
                                f"{streak}-day streak at risk!",
                                "You haven't checked in today. Don't break it."
                            )
                last_streak_date = today
        except Exception:
            pass

        # ── Periodic nudges ───────────────────
        if NUDGE_INTERVAL_HOURS > 0:
            elapsed = (now - last_nudge_time).total_seconds()
            if elapsed >= NUDGE_INTERVAL_HOURS * 3600 and 8 <= now.hour <= 22:
                title, message = get_contextual_nudge(db)
                send_notification(title, message)
                last_nudge_time = now

        time.sleep(CHECK_INTERVAL_SECS)


# ── System Tray Icon ──────────────────────────

def create_tray_icon():
    """Create a small white dot icon for system tray."""
    img = Image.new("RGB", (64, 64), color=(30, 30, 30))
    draw = ImageDraw.Draw(img)
    draw.ellipse([16, 16, 48, 48], fill=(255, 255, 255))
    return img


def open_app(icon, item):
    """Open the Streamlit app in browser."""
    subprocess.Popen(
        ["streamlit", "run", str(PROJECT_DIR / "app.py")],
        cwd=str(PROJECT_DIR),
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )


def quit_app(icon, item):
    """Stop everything."""
    icon.stop()
    sys.exit(0)


def run_with_tray():
    """Run the notification loop with a system tray icon."""
    if not TRAY_OK:
        # No tray support — just run the loop directly
        notification_loop()
        return

    # Start notification loop in background thread
    notif_thread = threading.Thread(target=notification_loop, daemon=True)
    notif_thread.start()

    # Create system tray icon
    icon = pystray.Icon(
        "ai_coach",
        create_tray_icon(),
        "AI Coach - Background Notifier",
        menu=pystray.Menu(
            pystray.MenuItem("Open AI Coach", open_app),
            pystray.MenuItem("Quit", quit_app),
        ),
    )

    send_notification("AI Coach Active", "Running in background. I'll nudge you throughout the day.")
    icon.run()


# ── Entry ─────────────────────────────────────

if __name__ == "__main__":
    run_with_tray()
