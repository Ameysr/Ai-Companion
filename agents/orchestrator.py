"""
orchestrator.py — The brain router that ties all agents together.
Processes user messages through the full multi-agent pipeline.
"""

import uuid
from datetime import datetime

from storage.database import Database
from storage.vector_store import VectorStore
from llm.provider import LLMProvider
from agents.memory_agent import MemoryAgent
from agents.emotion_agent import EmotionAgent
from agents.entity_tracker import EntityTracker
from agents.coach_agent import CoachAgent
from agents.coherence_guard import CoherenceGuard
from notifications import NotificationManager
from email_digest import EmailDigest
from config import BATCH_EXTRACTION, USE_LOCAL_SENTIMENT


class Orchestrator:
    """
    Central brain router that processes messages through the multi-agent pipeline:
    1. Memory retrieval
    2. Emotion detection (local first, LLM if needed)
    3. Entity extraction
    4. Response generation
    5. Coherence validation
    6. Post-processing (store everything)
    """

    def __init__(self):
        # Initialize storage
        self.db = Database()
        self.vs = VectorStore()
        self.llm = LLMProvider()

        # Initialize agents
        self.memory = MemoryAgent(self.db, self.vs)
        self.emotion = EmotionAgent(self.db, self.llm)
        self.entities = EntityTracker(self.db, self.llm)
        self.coach = CoachAgent(self.llm, self.memory, self.emotion, self.entities, self.db)
        self.coherence = CoherenceGuard(self.llm, self.db, self.vs)

        # Notifications
        self.notifier = NotificationManager(self.db)
        self.emailer = EmailDigest(self.db)

        # Session management
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        self.db.create_session(self.session_id)
        self._message_count = 0

    def process_message(self, user_message: str,
                        coaching_mode: str = "advise") -> dict:
        """
        Main entry point: process a user message through the full pipeline.

        Returns dict with:
        - response: str (the coach's reply)
        - emotion: dict (detected emotion)
        - entities: list (extracted entities)
        - was_coherence_checked: bool
        """
        self._message_count += 1

        # ─── Step 1: Local emotion detection (Layer 1 — no API) ───
        local_emotion = self.emotion.detect_emotion(user_message, self.session_id)
        needs_llm_emotion = local_emotion["source"] == "needs_llm"

        # ─── Step 2: Decide path ─────────────────────────────────
        if BATCH_EXTRACTION and (needs_llm_emotion or self.llm.is_available):
            # OPTIMIZED PATH: Single LLM call for everything
            result = self.coach.generate_batch_response(
                user_message, coaching_mode, self.session_id
            )

            emotion_data = result.get("emotion", local_emotion)
            if not needs_llm_emotion:
                # Local emotion was good enough, keep it
                emotion_data = local_emotion

            entities = result.get("entities", [])
            facts = result.get("facts_about_user", [])
            response = result.get("response", "I'm here for you. Tell me more.")

        else:
            # FALLBACK PATH: Use local emotion, generate response separately
            emotion_data = local_emotion
            entities = []
            facts = []
            response = self.coach.generate_response(
                user_message, coaching_mode, emotion_data, self.session_id
            )

        # ─── Step 3: Coherence check (only if needed) ────────────
        was_checked = False
        if self.coherence.should_check(user_message, emotion_data.get("label", "")):
            response = self.coherence.validate(response, user_message)
            was_checked = True

        # ─── Step 4: Post-processing — store everything ──────────

        # Store user message in conversations
        entity_names = [e.get("name", "") for e in entities if isinstance(e, dict)]
        self.db.add_message(
            role="user",
            content=user_message,
            session_id=self.session_id,
            emotion=emotion_data.get("label", ""),
            emotion_intensity=emotion_data.get("intensity", 0.0),
            entities_mentioned=entity_names,
        )

        # Store coach response
        self.db.add_message(
            role="coach",
            content=response,
            session_id=self.session_id,
        )

        # Track emotion
        self.emotion.track_mood(emotion_data, user_message, self.session_id)

        # Update entities
        if entities:
            self.entities.update_entities(entities)

        # Store facts
        if facts:
            self.memory.store_facts(facts)

        # Store episode
        self.memory.store_exchange(
            user_message, response,
            emotion=emotion_data.get("label", ""),
            entities=entity_names,
        )

        # Update session
        self.db.update_session(self.session_id, message_count=self._message_count)

        return {
            "response": response,
            "emotion": emotion_data,
            "entities": entities,
            "was_coherence_checked": was_checked,
        }

    def end_session(self):
        """End current session — flush memories and update session record."""
        self.memory.force_flush()
        self.db.update_session(
            self.session_id,
            end_time=datetime.now().isoformat(),
            message_count=self._message_count,
        )

    # ─── Convenience Methods ──────────────────────

    def get_user_profile(self) -> dict:
        return self.db.get_user_profile()

    def is_onboarded(self) -> bool:
        profile = self.db.get_user_profile()
        return profile is not None and profile.get("onboarding_complete", 0) == 1

    def setup_profile(self, name: str, tone: str = "warm",
                      coaching_areas: list = None, coach_name: str = "Coach"):
        self.db.create_user_profile(name, tone, coaching_areas, coach_name)

    def get_active_goals(self) -> list:
        return self.db.get_active_goals()

    def add_goal(self, title: str, description: str = "",
                 category: str = "general", target_date: str = ""):
        self.db.add_goal(title, description, category, target_date)

    def update_goal(self, goal_id: int, **kwargs):
        self.db.update_goal(goal_id, **kwargs)

    def get_mood_trend(self, days: int = 30) -> list:
        return self.emotion.get_mood_trend(days)

    def get_all_entities(self) -> list:
        return self.entities.get_all_entities_display()

    def get_memory_stats(self) -> dict:
        return self.memory.get_memory_stats()

    def get_streak(self) -> int:
        return self.db.get_streak()

    def add_checkin(self, mood_score: int, mood_label: str = "",
                    note: str = "", goals_updated: list = None):
        self.db.add_checkin(mood_score, mood_label, note, goals_updated)

    def get_recent_checkins(self, limit: int = 30) -> list:
        return self.db.get_recent_checkins(limit)

    def get_all_goals(self) -> list:
        return self.db.get_all_goals()

    def get_recent_sessions(self, limit: int = 10) -> list:
        return self.db.get_recent_sessions(limit)

    def get_emotion_summary(self, days: int = 7) -> dict:
        return self.db.get_emotion_summary(days)

    # ─── Notifications ────────────────────────────

    def start_notifications(self, checkin_time: str = "20:00"):
        """Start background notification scheduler."""
        self.notifier.start_scheduler(checkin_time)

    def stop_notifications(self):
        self.notifier.stop_scheduler()

    def set_reminder_time(self, time_str: str):
        self.notifier.set_checkin_time(time_str)

    def get_reminder_time(self) -> str:
        return self.notifier.get_checkin_time()

    def send_test_notification(self):
        self.notifier.send("AI Coach — Test", "Notifications are working!")

    # ─── Email Digest ─────────────────────────────

    def is_email_configured(self) -> bool:
        return self.emailer.is_configured

    def send_test_email(self) -> bool:
        return self.emailer.send_daily_digest()

    def start_email_scheduler(self, digest_time: str = "09:00"):
        if self.emailer.is_configured:
            self.emailer.start_scheduler(digest_time)

    def get_digest_time(self) -> str:
        return self.emailer.get_digest_time()

    def set_digest_time(self, time_str: str):
        self.emailer.set_digest_time(time_str)
