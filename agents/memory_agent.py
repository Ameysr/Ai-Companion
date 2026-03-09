"""
memory_agent.py — Handles all memory operations.
Store episodes, extract facts, retrieve relevant context, manage STM/LTM.
"""

from datetime import datetime
from storage.database import Database
from storage.vector_store import VectorStore
from config import STM_WINDOW, EPISODE_CHUNK_SIZE


class MemoryAgent:
    """Agent responsible for storing and retrieving memories."""

    def __init__(self, db: Database, vector_store: VectorStore):
        self.db = db
        self.vs = vector_store
        self._episode_buffer = []

    # ── Short-Term Memory (Recent Messages) ───────

    def get_recent_context(self, n: int = None) -> str:
        """Get recent conversation messages as formatted context string."""
        n = n or STM_WINDOW
        messages = self.db.get_recent_messages(n)
        if not messages:
            return "No previous conversations yet."

        lines = []
        for msg in messages:
            role = "User" if msg["role"] == "user" else "Coach"
            lines.append(f"{role}: {msg['content']}")
        return "\n".join(lines)

    # ── Long-Term Memory (Semantic Search) ────────

    def retrieve_relevant(self, query: str, top_k: int = 5) -> str:
        """Retrieve relevant memories from all sources, formatted as context."""
        results = self.vs.search_all(query, top_k)

        context_parts = []

        # Episodic memories
        if results["episodes"]:
            parts = []
            for ep in results["episodes"]:
                ts = ep["metadata"].get("timestamp", "unknown time")
                parts.append(f"[{ts}] {ep['text']}")
            context_parts.append("Past conversations:\n" + "\n".join(parts))

        # Facts
        if results["facts"]:
            facts = [f["text"] for f in results["facts"]]
            context_parts.append("Known facts:\n" + "\n".join(f"- {f}" for f in facts))

        # Narratives
        if results["narratives"]:
            narrs = [n["text"] for n in results["narratives"]]
            context_parts.append("Ongoing storylines:\n" + "\n".join(f"- {n}" for n in narrs))

        return "\n\n".join(context_parts) if context_parts else "No relevant memories found."

    # ── Store Episode ─────────────────────────────

    def store_exchange(self, user_message: str, coach_response: str,
                       emotion: str = "", entities: list = None):
        """Store a user-coach exchange as an episodic memory."""
        self._episode_buffer.append({
            "user": user_message,
            "coach": coach_response,
            "emotion": emotion,
            "entities": entities or [],
            "timestamp": datetime.now().isoformat(),
        })

        # Chunk episodes when buffer is full
        if len(self._episode_buffer) >= EPISODE_CHUNK_SIZE:
            self._flush_episode_buffer()

    def _flush_episode_buffer(self):
        """Compress buffered exchanges into an episodic memory."""
        if not self._episode_buffer:
            return

        # Build a summary of the chunk
        lines = []
        emotions = []
        all_entities = []
        for ex in self._episode_buffer:
            lines.append(f"User: {ex['user']}")
            lines.append(f"Coach: {ex['coach'][:100]}...")
            if ex["emotion"]:
                emotions.append(ex["emotion"])
            all_entities.extend(ex["entities"])

        episode_text = "\n".join(lines)
        metadata = {
            "emotions": ", ".join(set(emotions)) if emotions else "mixed",
            "entities": ", ".join(set(all_entities)) if all_entities else "none",
            "exchange_count": str(len(self._episode_buffer)),
        }

        self.vs.store_episode(episode_text, metadata)
        self._episode_buffer.clear()

    def force_flush(self):
        """Force flush any remaining episodes in the buffer."""
        self._flush_episode_buffer()

    # ── Store Facts ───────────────────────────────

    def store_facts(self, facts: list):
        """Store extracted facts about the user."""
        for fact in facts:
            if isinstance(fact, str) and len(fact.strip()) > 5:
                self.vs.store_fact(fact.strip())

    # ── Store Narrative ───────────────────────────

    def store_narrative(self, narrative: str, thread_name: str = ""):
        """Store or update a narrative thread."""
        self.vs.store_narrative(narrative, thread_name)

    # ── User Summary ──────────────────────────────

    def get_user_summary(self) -> str:
        """Compile a summary from user profile and known facts."""
        profile = self.db.get_user_profile()
        if not profile:
            return "New user, no profile yet."

        parts = [f"Name: {profile.get('name', 'Unknown')}"]
        if profile.get("bio"):
            parts.append(f"Bio: {profile['bio']}")
        areas = profile.get("coaching_areas", [])
        if areas:
            parts.append(f"Coaching focus: {', '.join(areas)}")
        parts.append(f"Preferred tone: {profile.get('preferred_tone', 'warm')}")

        # Add stored facts
        all_facts = self.vs.get_all_facts()
        if all_facts:
            fact_texts = [f["text"] for f in all_facts[:15]]
            parts.append("Known facts:\n" + "\n".join(f"- {f}" for f in fact_texts))

        return "\n".join(parts)

    # ── Stats ─────────────────────────────────────

    def get_memory_stats(self) -> dict:
        vs_stats = self.vs.get_stats()
        return {
            "total_messages": self.db.get_total_message_count(),
            "episodic_memories": vs_stats["episodes"],
            "stored_facts": vs_stats["facts"],
            "narrative_threads": vs_stats["narratives"],
            "buffer_size": len(self._episode_buffer),
        }
