"""
coach_agent.py — Main response generation agent.
Takes full context (memory, emotions, entities, goals) and generates coaching responses.
"""

from config import DEFAULT_SYSTEM_PROMPT, TONE_INSTRUCTIONS


class CoachAgent:
    """Agent responsible for generating contextual coaching responses."""

    def __init__(self, llm, memory_agent, emotion_agent, entity_tracker, db):
        self.llm = llm
        self.memory = memory_agent
        self.emotion = emotion_agent
        self.entities = entity_tracker
        self.db = db

    def generate_response(self, user_message: str, coaching_mode: str = "advise",
                          emotion_data: dict = None, session_id: str = "") -> str:
        """Generate a coaching response with full context."""
        profile = self.db.get_user_profile() or {}
        tone = profile.get("preferred_tone", "warm")

        # Gather all context
        memory_context = self.memory.retrieve_relevant(user_message)
        recent_context = self.memory.get_recent_context()
        emotion_context = self.emotion.get_emotional_context()
        entity_context = self.entities.get_entity_context(user_message)
        goal_context = self._get_goal_context()
        user_context = self.memory.get_user_summary()

        # Build system prompt
        system_prompt = DEFAULT_SYSTEM_PROMPT.format(
            tone_instruction=TONE_INSTRUCTIONS.get(tone, TONE_INSTRUCTIONS["warm"]),
            user_context=user_context,
            memory_context=memory_context,
            entity_context=entity_context,
            goal_context=goal_context,
            emotion_context=emotion_context,
            recent_context=recent_context,
        )

        # Build user prompt with coaching mode instruction
        mode_instructions = {
            "listen": "The user needs to be heard right now. Listen, validate, empathize. Don't give advice unless asked.",
            "advise": "Give thoughtful, actionable advice. Be practical but caring.",
            "challenge": "Push the user to think bigger, call out excuses gently, encourage growth.",
            "celebrate": "The user has good news or progress. Celebrate genuinely, reference their journey.",
        }

        mode_text = mode_instructions.get(coaching_mode, mode_instructions["advise"])

        # Add emotion awareness
        emotion_note = ""
        if emotion_data:
            label = emotion_data.get("label", "neutral")
            intensity = emotion_data.get("intensity", 0.5)
            if intensity > 0.7:
                emotion_note = f"\n[The user seems to be feeling strong {label} right now. Be especially attentive to this.]"
            elif label not in ("neutral", "calm"):
                emotion_note = f"\n[The user seems to be feeling {label}.]"

        user_prompt = f"""COACHING MODE: {mode_text}{emotion_note}

USER MESSAGE: {user_message}

Respond naturally as their coach. Keep it conversational — not too long, not too short.
Reference specific memories or facts when relevant. Don't be generic."""

        response = self.llm.call(user_prompt, system_prompt=system_prompt,
                                 temperature=0.75, max_tokens=600)
        return response.strip()

    def generate_batch_response(self, user_message: str, coaching_mode: str = "advise",
                                session_id: str = "") -> dict:
        """
        Single LLM call that extracts emotion + entities + facts + generates response.
        This is the optimized path — 1 API call instead of 5.
        """
        profile = self.db.get_user_profile() or {}
        tone = profile.get("preferred_tone", "warm")

        # Gather context
        memory_context = self.memory.retrieve_relevant(user_message)
        recent_context = self.memory.get_recent_context()
        emotion_context = self.emotion.get_emotional_context()
        entity_context = self.entities.get_entity_context(user_message)
        goal_context = self._get_goal_context()
        user_context = self.memory.get_user_summary()

        system_prompt = DEFAULT_SYSTEM_PROMPT.format(
            tone_instruction=TONE_INSTRUCTIONS.get(tone, TONE_INSTRUCTIONS["warm"]),
            user_context=user_context,
            memory_context=memory_context,
            entity_context=entity_context,
            goal_context=goal_context,
            emotion_context=emotion_context,
            recent_context=recent_context,
        )

        mode_instructions = {
            "listen": "Listen, validate, empathize. Don't give advice unless asked.",
            "advise": "Give thoughtful, actionable advice. Be practical but caring.",
            "challenge": "Push the user to grow, call out excuses gently.",
            "celebrate": "Celebrate genuinely, reference their journey.",
        }
        mode_text = mode_instructions.get(coaching_mode, mode_instructions["advise"])

        batch_prompt = f"""You are analyzing a user message AND generating a coaching response.
Do BOTH tasks in a single JSON response.

COACHING MODE: {mode_text}

USER MESSAGE: "{user_message}"

Return this exact JSON structure:
{{
    "emotion": {{
        "label": "one of: joy, excitement, gratitude, love, pride, calm, neutral, curious, stress, anxiety, sadness, loneliness, self_doubt, anger, frustration, hurt, fear, determination, hope, relief",
        "secondary": "optional secondary emotion or empty string",
        "intensity": 0.0 to 1.0,
        "trigger": "what specifically triggered this emotion, or empty string"
    }},
    "entities": [
        {{
            "name": "entity name",
            "type": "person/place/event/thing",
            "relationship": "relationship to user if inferable",
            "facts": ["new facts learned about this entity"]
        }}
    ],
    "facts_about_user": ["any new facts learned about the user from this message"],
    "response": "Your full coaching response here. Be conversational, reference memories when relevant, don't be generic."
}}

If no entities found, use empty array []. If no new facts, use empty array [].
The response should feel natural and human."""

        result = self.llm.call_json(batch_prompt, system_prompt=system_prompt)

        # Ensure required fields exist
        if "error" in result:
            # Fallback: generate just the response
            response = self.llm.call(
                f"COACHING MODE: {mode_text}\n\nUSER: {user_message}\n\nRespond as their coach.",
                system_prompt=system_prompt,
                temperature=0.75,
            )
            return {
                "emotion": {"label": "neutral", "secondary": "", "intensity": 0.5, "trigger": ""},
                "entities": [],
                "facts_about_user": [],
                "response": response.strip(),
            }

        return result

    def _get_goal_context(self) -> str:
        goals = self.db.get_active_goals()
        if not goals:
            return "No active goals set."

        lines = []
        for g in goals:
            lines.append(f"- {g['title']} (progress: {g['progress']}%, category: {g['category']})")
            if g.get("description"):
                lines.append(f"  Description: {g['description']}")
        return "\n".join(lines)
