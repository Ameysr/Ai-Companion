"""
coherence_guard.py — Validates responses against known facts to prevent contradictions.
Skips validation for simple messages (greetings, small talk).
"""

from config import COHERENCE_CHECK_SKIP


class CoherenceGuard:
    """Agent that prevents contradictory or inconsistent responses."""

    def __init__(self, llm, db, vector_store):
        self.llm = llm
        self.db = db
        self.vs = vector_store

    def should_check(self, user_message: str, emotion_label: str = "") -> bool:
        """Determine if coherence check is needed for this message."""
        text_lower = user_message.lower().strip()

        # Skip simple messages
        simple_patterns = [
            "good morning", "goodnight", "hi", "hello", "hey", "thanks",
            "thank you", "bye", "good night", "gm", "gn", "sup", "yo",
        ]
        for pattern in simple_patterns:
            if text_lower == pattern or text_lower.startswith(pattern + " "):
                return False

        # Skip if emotion is clearly simple
        if emotion_label in COHERENCE_CHECK_SKIP:
            return False

        # Check if message involves entities or facts worth verifying
        all_entities = self.db.get_all_entities()
        for entity in all_entities:
            if entity["name"].lower() in text_lower:
                return True  # Mentions a known entity — worth checking

        # Short messages probably don't need checking
        if len(text_lower.split()) < 5:
            return False

        return True

    def validate(self, response: str, user_message: str) -> str:
        """
        Validate a coach response against known facts.
        Returns corrected response if contradictions found, original otherwise.
        """
        if not self.llm:
            return response

        # Get known facts
        all_facts = self.vs.get_all_facts()
        entities = self.db.get_all_entities()

        if not all_facts and not entities:
            return response  # Nothing to check against

        # Build fact context
        fact_lines = []
        for f in all_facts[:20]:
            fact_lines.append(f"- {f['text']}")
        for e in entities[:10]:
            facts_str = "; ".join(e["facts"][:3]) if e["facts"] else ""
            fact_lines.append(
                f"- {e['name']} is a {e['entity_type']}"
                f"{', ' + e['relationship'] if e['relationship'] else ''}"
                f"{'. ' + facts_str if facts_str else ''}"
            )

        facts_context = "\n".join(fact_lines)

        prompt = f"""Check if this AI coach response contradicts any known facts about the user.

KNOWN FACTS:
{facts_context}

USER MESSAGE: "{user_message}"
COACH RESPONSE: "{response}"

If the response contradicts any known fact, provide a corrected version.
If there are no contradictions, respond with exactly: NO_CONTRADICTION

If correcting, return only the corrected response text, nothing else."""

        result = self.llm.call(prompt, temperature=0.2, max_tokens=700)
        result = result.strip()

        if "NO_CONTRADICTION" in result.upper():
            return response
        elif len(result) > 20:  # Got a corrected response
            return result
        return response
