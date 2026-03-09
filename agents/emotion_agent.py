"""
emotion_agent.py — Detects, tracks, and analyzes emotional states.
3-layer system: TextBlob (local) → Embedding cache → LLM (API).
"""

from textblob import TextBlob
from storage.database import Database
from config import EMOTION_LABELS, USE_LOCAL_SENTIMENT, EMOTION_CACHE_THRESHOLD


class EmotionAgent:
    """Agent responsible for emotion detection and mood tracking."""

    def __init__(self, db: Database, llm=None):
        self.db = db
        self.llm = llm

    def detect_emotion(self, text: str, session_id: str = "") -> dict:
        """
        3-layer emotion detection:
        1. TextBlob (local, instant)
        2. Embedding cache (local, instant)
        3. LLM batch extraction (API call — handled by orchestrator)

        Returns: {"label": str, "secondary": str, "intensity": float, "trigger": str, "source": str}
        """
        result = {"label": "neutral", "secondary": "", "intensity": 0.5,
                  "trigger": "", "source": "local"}

        # Layer 1: TextBlob for clear positive/negative
        if USE_LOCAL_SENTIMENT:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity

            if polarity > 0.5 and subjectivity > 0.3:
                result["label"] = "joy"
                result["intensity"] = min(0.9, 0.5 + polarity * 0.4)
                result["source"] = "textblob"
            elif polarity > 0.3:
                result["label"] = "calm"
                result["intensity"] = 0.5 + polarity * 0.3
                result["source"] = "textblob"
            elif polarity < -0.5:
                result["label"] = self._guess_negative_emotion(text)
                result["intensity"] = min(0.9, 0.5 + abs(polarity) * 0.4)
                result["source"] = "textblob"
            elif polarity < -0.2:
                result["label"] = self._guess_negative_emotion(text)
                result["intensity"] = 0.5 + abs(polarity) * 0.3
                result["source"] = "textblob"
            else:
                # Ambiguous — needs LLM (will be handled by orchestrator batch call)
                result["label"] = "neutral"
                result["source"] = "needs_llm"

        return result

    def detect_emotion_llm(self, text: str) -> dict:
        """Use LLM for nuanced emotion detection. Called when TextBlob is insufficient."""
        if not self.llm:
            return {"label": "neutral", "secondary": "", "intensity": 0.5,
                    "trigger": "", "source": "fallback"}

        prompt = f"""Analyze the emotion in this message. Return JSON:
{{
    "label": "one of: {', '.join(EMOTION_LABELS)}",
    "secondary": "optional secondary emotion or empty string",
    "intensity": 0.0 to 1.0,
    "trigger": "what caused this emotion, or empty string"
}}

Message: "{text}"
"""
        result = self.llm.call_json(prompt)
        if "error" not in result:
            result["source"] = "llm"
            return result
        return {"label": "neutral", "secondary": "", "intensity": 0.5,
                "trigger": "", "source": "fallback"}

    def track_mood(self, emotion: dict, message_text: str = "", session_id: str = ""):
        """Log emotion to database for tracking."""
        self.db.log_emotion(
            emotion_label=emotion.get("label", "neutral"),
            intensity=emotion.get("intensity", 0.5),
            secondary=emotion.get("secondary", ""),
            trigger=emotion.get("trigger", ""),
            message_text=message_text,
            session_id=session_id,
        )

    def get_emotional_context(self, days: int = 7) -> str:
        """Get a summary of recent emotional state for the coach."""
        summary = self.db.get_emotion_summary(days)
        if summary["count"] == 0:
            return "No emotional data yet."

        parts = [
            f"Dominant mood (last {days} days): {summary['dominant']}",
            f"Average intensity: {summary['avg_intensity']:.1f}/1.0",
            f"Total tracked: {summary['count']} data points",
        ]

        # Breakdown
        if summary["breakdown"]:
            sorted_emotions = sorted(summary["breakdown"].items(),
                                     key=lambda x: x[1], reverse=True)
            parts.append("Emotion breakdown:")
            for emotion, count in sorted_emotions[:5]:
                parts.append(f"  - {emotion}: {count}x")

        # Recent trend
        recent = self.db.get_recent_emotions(5)
        if recent:
            recent_labels = [e["emotion_label"] for e in recent]
            parts.append(f"Recent trend: {' -> '.join(recent_labels)}")

        return "\n".join(parts)

    def get_mood_trend(self, days: int = 30) -> list:
        """Get mood data points for graphing."""
        emotions = self.db.get_emotions_since(days)
        return [
            {
                "timestamp": e["created_at"],
                "label": e["emotion_label"],
                "intensity": e["intensity"],
                "trigger": e.get("trigger", ""),
            }
            for e in emotions
        ]

    def _guess_negative_emotion(self, text: str) -> str:
        """Simple keyword-based negative emotion classification."""
        text_lower = text.lower()
        keywords = {
            "anxiety": ["anxious", "worried", "nervous", "overthink", "panic", "racing"],
            "sadness": ["sad", "cry", "tears", "depressed", "down", "empty"],
            "loneliness": ["lonely", "alone", "nobody", "no one", "isolated"],
            "anger": ["angry", "furious", "mad", "hate", "annoyed", "pissed"],
            "frustration": ["frustrated", "stuck", "cant", "ugh", "annoying"],
            "stress": ["stress", "overwhelmed", "pressure", "deadline", "burned"],
            "self_doubt": ["failure", "worthless", "enough", "imposter", "doubt"],
            "fear": ["scared", "afraid", "terrified", "fear", "frightened"],
            "hurt": ["hurt", "betrayed", "backstab", "trust", "lied"],
        }

        best_match = "sadness"
        best_count = 0
        for emotion, words in keywords.items():
            count = sum(1 for w in words if w in text_lower)
            if count > best_count:
                best_count = count
                best_match = emotion

        return best_match
