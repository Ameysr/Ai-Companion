"""
database.py — SQLite database manager for structured data.
Handles: user profile, entities, emotions, goals, sessions, conversations.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from config import DB_PATH


class Database:
    """SQLite database manager for the AI Coach Companion."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(DB_PATH)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_tables()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_tables(self):
        conn = self._get_conn()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS user_profile (
                    id INTEGER PRIMARY KEY DEFAULT 1,
                    name TEXT DEFAULT '',
                    bio TEXT DEFAULT '',
                    coaching_areas TEXT DEFAULT '[]',
                    preferred_tone TEXT DEFAULT 'warm',
                    coach_name TEXT DEFAULT 'Coach',
                    onboarding_complete INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    entity_type TEXT DEFAULT 'person',
                    relationship TEXT DEFAULT '',
                    facts TEXT DEFAULT '[]',
                    first_mentioned TEXT DEFAULT (datetime('now')),
                    last_mentioned TEXT DEFAULT (datetime('now')),
                    mention_count INTEGER DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS emotions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    emotion_label TEXT NOT NULL,
                    secondary_emotion TEXT DEFAULT '',
                    intensity REAL DEFAULT 0.5,
                    trigger TEXT DEFAULT '',
                    message_text TEXT DEFAULT '',
                    session_id TEXT DEFAULT '',
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    category TEXT DEFAULT 'general',
                    status TEXT DEFAULT 'active',
                    progress INTEGER DEFAULT 0,
                    progress_notes TEXT DEFAULT '[]',
                    created_at TEXT DEFAULT (datetime('now')),
                    target_date TEXT DEFAULT '',
                    completed_at TEXT DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    start_time TEXT DEFAULT (datetime('now')),
                    end_time TEXT DEFAULT '',
                    summary TEXT DEFAULT '',
                    mood_start TEXT DEFAULT '',
                    mood_end TEXT DEFAULT '',
                    message_count INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT DEFAULT '',
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    emotion TEXT DEFAULT '',
                    emotion_intensity REAL DEFAULT 0.0,
                    entities_mentioned TEXT DEFAULT '[]',
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS daily_checkins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mood_score INTEGER DEFAULT 5,
                    mood_label TEXT DEFAULT 'neutral',
                    note TEXT DEFAULT '',
                    goals_updated TEXT DEFAULT '[]',
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS emotion_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_hash TEXT NOT NULL,
                    emotion_label TEXT NOT NULL,
                    intensity REAL DEFAULT 0.5,
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS squads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    invite_code TEXT NOT NULL UNIQUE,
                    created_by TEXT DEFAULT '',
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS squad_members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    squad_id INTEGER NOT NULL,
                    member_name TEXT NOT NULL,
                    is_self INTEGER DEFAULT 0,
                    joined_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (squad_id) REFERENCES squads(id)
                );

                CREATE TABLE IF NOT EXISTS squad_goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    squad_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    status TEXT DEFAULT 'active',
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (squad_id) REFERENCES squads(id)
                );

                CREATE TABLE IF NOT EXISTS squad_goal_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    squad_goal_id INTEGER NOT NULL,
                    member_id INTEGER NOT NULL,
                    progress INTEGER DEFAULT 0,
                    last_updated TEXT DEFAULT (datetime('now')),
                    UNIQUE(squad_goal_id, member_id),
                    FOREIGN KEY (squad_goal_id) REFERENCES squad_goals(id),
                    FOREIGN KEY (member_id) REFERENCES squad_members(id)
                );
            """)
            conn.commit()
        finally:
            conn.close()

    # ── User Profile ──────────────────────────────

    def get_user_profile(self) -> dict:
        conn = self._get_conn()
        try:
            row = conn.execute("SELECT * FROM user_profile WHERE id = 1").fetchone()
            if row:
                profile = dict(row)
                profile["coaching_areas"] = json.loads(profile.get("coaching_areas", "[]"))
                return profile
            return None
        finally:
            conn.close()

    def create_user_profile(self, name: str, tone: str = "warm",
                            coaching_areas: list = None, coach_name: str = "Coach"):
        conn = self._get_conn()
        try:
            conn.execute("""
                INSERT OR REPLACE INTO user_profile (id, name, preferred_tone, coaching_areas, coach_name, onboarding_complete)
                VALUES (1, ?, ?, ?, ?, 1)
            """, (name, tone, json.dumps(coaching_areas or []), coach_name))
            conn.commit()
        finally:
            conn.close()

    def update_user_profile(self, **kwargs):
        conn = self._get_conn()
        try:
            allowed = ["name", "bio", "preferred_tone", "coaching_areas", "coach_name", "onboarding_complete"]
            updates = []
            values = []
            for key, val in kwargs.items():
                if key in allowed:
                    if key == "coaching_areas" and isinstance(val, list):
                        val = json.dumps(val)
                    updates.append(f"{key} = ?")
                    values.append(val)
            if updates:
                updates.append("updated_at = datetime('now')")
                values.append(1)
                sql = f"UPDATE user_profile SET {', '.join(updates)} WHERE id = ?"
                conn.execute(sql, values)
                conn.commit()
        finally:
            conn.close()

    # ── Entities ──────────────────────────────────

    def add_entity(self, name: str, entity_type: str = "person",
                   relationship: str = "", facts: list = None):
        conn = self._get_conn()
        try:
            existing = conn.execute(
                "SELECT * FROM entities WHERE LOWER(name) = LOWER(?)", (name,)
            ).fetchone()

            if existing:
                old_facts = json.loads(existing["facts"] or "[]")
                new_facts = list(set(old_facts + (facts or [])))
                conn.execute("""
                    UPDATE entities SET facts = ?, last_mentioned = datetime('now'),
                    mention_count = mention_count + 1, relationship = COALESCE(NULLIF(?, ''), relationship)
                    WHERE id = ?
                """, (json.dumps(new_facts), relationship, existing["id"]))
            else:
                conn.execute("""
                    INSERT INTO entities (name, entity_type, relationship, facts)
                    VALUES (?, ?, ?, ?)
                """, (name, entity_type, relationship, json.dumps(facts or [])))
            conn.commit()
        finally:
            conn.close()

    def get_entity(self, name: str) -> dict:
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM entities WHERE LOWER(name) = LOWER(?)", (name,)
            ).fetchone()
            if row:
                entity = dict(row)
                entity["facts"] = json.loads(entity.get("facts", "[]"))
                return entity
            return None
        finally:
            conn.close()

    def get_all_entities(self) -> list:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM entities ORDER BY last_mentioned DESC"
            ).fetchall()
            entities = []
            for row in rows:
                entity = dict(row)
                entity["facts"] = json.loads(entity.get("facts", "[]"))
                entities.append(entity)
            return entities
        finally:
            conn.close()

    # ── Emotions ──────────────────────────────────

    def log_emotion(self, emotion_label: str, intensity: float = 0.5,
                    secondary: str = "", trigger: str = "",
                    message_text: str = "", session_id: str = ""):
        conn = self._get_conn()
        try:
            conn.execute("""
                INSERT INTO emotions (emotion_label, secondary_emotion, intensity, trigger, message_text, session_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (emotion_label, secondary, intensity, trigger, message_text, session_id))
            conn.commit()
        finally:
            conn.close()

    def get_recent_emotions(self, limit: int = 20) -> list:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM emotions ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_emotions_since(self, days: int = 7) -> list:
        conn = self._get_conn()
        try:
            rows = conn.execute("""
                SELECT * FROM emotions
                WHERE created_at >= datetime('now', ?)
                ORDER BY created_at ASC
            """, (f"-{days} days",)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_emotion_summary(self, days: int = 7) -> dict:
        emotions = self.get_emotions_since(days)
        if not emotions:
            return {"dominant": "neutral", "avg_intensity": 0.5, "count": 0, "breakdown": {}}

        breakdown = {}
        total_intensity = 0
        for e in emotions:
            label = e["emotion_label"]
            breakdown[label] = breakdown.get(label, 0) + 1
            total_intensity += e["intensity"]

        dominant = max(breakdown, key=breakdown.get) if breakdown else "neutral"
        return {
            "dominant": dominant,
            "avg_intensity": total_intensity / len(emotions),
            "count": len(emotions),
            "breakdown": breakdown,
        }

    # ── Goals ─────────────────────────────────────

    def add_goal(self, title: str, description: str = "", category: str = "general",
                 target_date: str = ""):
        conn = self._get_conn()
        try:
            conn.execute("""
                INSERT INTO goals (title, description, category, target_date)
                VALUES (?, ?, ?, ?)
            """, (title, description, category, target_date))
            conn.commit()
        finally:
            conn.close()

    def update_goal(self, goal_id: int, **kwargs):
        conn = self._get_conn()
        try:
            allowed = ["title", "description", "status", "progress", "progress_notes", "completed_at"]
            updates = []
            values = []
            for key, val in kwargs.items():
                if key in allowed:
                    if key == "progress_notes" and isinstance(val, list):
                        val = json.dumps(val)
                    updates.append(f"{key} = ?")
                    values.append(val)
            if updates:
                values.append(goal_id)
                sql = f"UPDATE goals SET {', '.join(updates)} WHERE id = ?"
                conn.execute(sql, values)
                conn.commit()
        finally:
            conn.close()

    def get_active_goals(self) -> list:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM goals WHERE status = 'active' ORDER BY created_at DESC"
            ).fetchall()
            goals = []
            for row in rows:
                goal = dict(row)
                goal["progress_notes"] = json.loads(goal.get("progress_notes", "[]"))
                goals.append(goal)
            return goals
        finally:
            conn.close()

    def get_all_goals(self) -> list:
        conn = self._get_conn()
        try:
            rows = conn.execute("SELECT * FROM goals ORDER BY created_at DESC").fetchall()
            goals = []
            for row in rows:
                goal = dict(row)
                goal["progress_notes"] = json.loads(goal.get("progress_notes", "[]"))
                goals.append(goal)
            return goals
        finally:
            conn.close()

    # ── Conversations ─────────────────────────────

    def add_message(self, role: str, content: str, session_id: str = "",
                    emotion: str = "", emotion_intensity: float = 0.0,
                    entities_mentioned: list = None):
        conn = self._get_conn()
        try:
            conn.execute("""
                INSERT INTO conversations (session_id, role, content, emotion, emotion_intensity, entities_mentioned)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, role, content, emotion, emotion_intensity,
                  json.dumps(entities_mentioned or [])))
            conn.commit()
        finally:
            conn.close()

    def get_recent_messages(self, limit: int = 15) -> list:
        conn = self._get_conn()
        try:
            rows = conn.execute("""
                SELECT * FROM conversations ORDER BY created_at DESC LIMIT ?
            """, (limit,)).fetchall()
            messages = [dict(r) for r in rows]
            messages.reverse()
            return messages
        finally:
            conn.close()

    def get_session_messages(self, session_id: str) -> list:
        conn = self._get_conn()
        try:
            rows = conn.execute("""
                SELECT * FROM conversations WHERE session_id = ? ORDER BY created_at ASC
            """, (session_id,)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_total_message_count(self) -> int:
        conn = self._get_conn()
        try:
            row = conn.execute("SELECT COUNT(*) as cnt FROM conversations").fetchone()
            return row["cnt"] if row else 0
        finally:
            conn.close()

    # ── Sessions ──────────────────────────────────

    def create_session(self, session_id: str):
        conn = self._get_conn()
        try:
            conn.execute("INSERT OR IGNORE INTO sessions (id) VALUES (?)", (session_id,))
            conn.commit()
        finally:
            conn.close()

    def update_session(self, session_id: str, **kwargs):
        conn = self._get_conn()
        try:
            allowed = ["end_time", "summary", "mood_start", "mood_end", "message_count"]
            updates = []
            values = []
            for key, val in kwargs.items():
                if key in allowed:
                    updates.append(f"{key} = ?")
                    values.append(val)
            if updates:
                values.append(session_id)
                sql = f"UPDATE sessions SET {', '.join(updates)} WHERE id = ?"
                conn.execute(sql, values)
                conn.commit()
        finally:
            conn.close()

    def get_recent_sessions(self, limit: int = 10) -> list:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM sessions ORDER BY start_time DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ── Daily Check-ins ───────────────────────────

    def add_checkin(self, mood_score: int, mood_label: str = "", note: str = "",
                    goals_updated: list = None):
        conn = self._get_conn()
        try:
            conn.execute("""
                INSERT INTO daily_checkins (mood_score, mood_label, note, goals_updated)
                VALUES (?, ?, ?, ?)
            """, (mood_score, mood_label, note, json.dumps(goals_updated or [])))
            conn.commit()
        finally:
            conn.close()

    def get_recent_checkins(self, limit: int = 30) -> list:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM daily_checkins ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            checkins = [dict(r) for r in rows]
            checkins.reverse()
            return checkins
        finally:
            conn.close()

    def get_streak(self) -> int:
        conn = self._get_conn()
        try:
            rows = conn.execute("""
                SELECT DISTINCT DATE(created_at) as d FROM daily_checkins
                ORDER BY d DESC
            """).fetchall()
            if not rows:
                return 0

            streak = 0
            today = datetime.now().date()
            for row in rows:
                check_date = datetime.strptime(row["d"], "%Y-%m-%d").date()
                expected = today - __import__("datetime").timedelta(days=streak)
                if check_date == expected:
                    streak += 1
                else:
                    break
            return streak
        finally:
            conn.close()

    # ── Emotion Cache ─────────────────────────────

    def cache_emotion(self, message_hash: str, emotion_label: str, intensity: float):
        conn = self._get_conn()
        try:
            conn.execute("""
                INSERT INTO emotion_cache (message_hash, emotion_label, intensity)
                VALUES (?, ?, ?)
            """, (message_hash, emotion_label, intensity))
            conn.commit()
        finally:
            conn.close()

    def get_cached_emotion(self, message_hash: str) -> dict:
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM emotion_cache WHERE message_hash = ?", (message_hash,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    # ── Squad ─────────────────────────────────────

    def create_squad(self, name: str, invite_code: str, created_by: str) -> int:
        conn = self._get_conn()
        try:
            cursor = conn.execute("""
                INSERT INTO squads (name, invite_code, created_by)
                VALUES (?, ?, ?)
            """, (name, invite_code, created_by))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_squad(self, squad_id: int = None, invite_code: str = None) -> dict:
        conn = self._get_conn()
        try:
            if squad_id:
                row = conn.execute("SELECT * FROM squads WHERE id = ?", (squad_id,)).fetchone()
            elif invite_code:
                row = conn.execute("SELECT * FROM squads WHERE invite_code = ?", (invite_code,)).fetchone()
            else:
                row = conn.execute("SELECT * FROM squads ORDER BY id DESC LIMIT 1").fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_all_squads(self) -> list:
        conn = self._get_conn()
        try:
            rows = conn.execute("SELECT * FROM squads ORDER BY created_at DESC").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def add_squad_member(self, squad_id: int, member_name: str, is_self: bool = False) -> int:
        conn = self._get_conn()
        try:
            existing = conn.execute(
                "SELECT * FROM squad_members WHERE squad_id = ? AND LOWER(member_name) = LOWER(?)",
                (squad_id, member_name)
            ).fetchone()
            if existing:
                return existing["id"]
            cursor = conn.execute("""
                INSERT INTO squad_members (squad_id, member_name, is_self)
                VALUES (?, ?, ?)
            """, (squad_id, member_name, 1 if is_self else 0))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_squad_members(self, squad_id: int) -> list:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM squad_members WHERE squad_id = ? ORDER BY joined_at", (squad_id,)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def add_squad_goal(self, squad_id: int, title: str, category: str = "general") -> int:
        conn = self._get_conn()
        try:
            cursor = conn.execute("""
                INSERT INTO squad_goals (squad_id, title, category)
                VALUES (?, ?, ?)
            """, (squad_id, title, category))
            goal_id = cursor.lastrowid

            # Create progress entries for all members
            members = conn.execute(
                "SELECT id FROM squad_members WHERE squad_id = ?", (squad_id,)
            ).fetchall()
            for m in members:
                conn.execute("""
                    INSERT OR IGNORE INTO squad_goal_progress (squad_goal_id, member_id, progress)
                    VALUES (?, ?, 0)
                """, (goal_id, m["id"]))

            conn.commit()
            return goal_id
        finally:
            conn.close()

    def get_squad_goals(self, squad_id: int) -> list:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM squad_goals WHERE squad_id = ? AND status = 'active' ORDER BY created_at DESC",
                (squad_id,)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def update_squad_goal_progress(self, squad_goal_id: int, member_id: int, progress: int):
        conn = self._get_conn()
        try:
            conn.execute("""
                INSERT INTO squad_goal_progress (squad_goal_id, member_id, progress)
                VALUES (?, ?, ?)
                ON CONFLICT(squad_goal_id, member_id)
                DO UPDATE SET progress = ?, last_updated = datetime('now')
            """, (squad_goal_id, member_id, progress, progress))
            conn.commit()
        finally:
            conn.close()

    def get_squad_leaderboard(self, squad_id: int) -> list:
        """Get all members' progress on all squad goals."""
        conn = self._get_conn()
        try:
            rows = conn.execute("""
                SELECT
                    sm.member_name,
                    sm.id as member_id,
                    sg.title as goal_title,
                    sg.id as goal_id,
                    COALESCE(sgp.progress, 0) as progress,
                    sgp.last_updated
                FROM squad_members sm
                JOIN squad_goals sg ON sg.squad_id = sm.squad_id AND sg.status = 'active'
                LEFT JOIN squad_goal_progress sgp ON sgp.member_id = sm.id AND sgp.squad_goal_id = sg.id
                WHERE sm.squad_id = ?
                ORDER BY sm.member_name, sg.title
            """, (squad_id,)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_squad_summary(self, squad_id: int) -> dict:
        """Get squad summary with per-member average progress."""
        conn = self._get_conn()
        try:
            members = self.get_squad_members(squad_id)
            goals = self.get_squad_goals(squad_id)
            leaderboard = self.get_squad_leaderboard(squad_id)

            member_scores = {}
            for entry in leaderboard:
                name = entry["member_name"]
                if name not in member_scores:
                    member_scores[name] = {"total": 0, "count": 0, "member_id": entry["member_id"]}
                member_scores[name]["total"] += entry["progress"]
                member_scores[name]["count"] += 1

            rankings = []
            for name, data in member_scores.items():
                avg = data["total"] / data["count"] if data["count"] > 0 else 0
                rankings.append({
                    "name": name,
                    "member_id": data["member_id"],
                    "avg_progress": round(avg, 1),
                })
            rankings.sort(key=lambda x: x["avg_progress"], reverse=True)

            return {
                "member_count": len(members),
                "goal_count": len(goals),
                "rankings": rankings,
                "leaderboard": leaderboard,
            }
        finally:
            conn.close()
