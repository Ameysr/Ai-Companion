"""
coach_agent.py — Main response generation agent.
Takes full context (memory, emotions, entities, goals) and generates coaching responses.
SHORT, PUNCHY responses — 2-3 sentences max.
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

        mode_instructions = {
            "listen": "Just listen. Validate. No advice.",
            "advise": "One sharp piece of advice. No essays.",
            "challenge": "Push them. One tough question.",
            "celebrate": "Hype them up. Keep it real.",
        }

        mode_text = mode_instructions.get(coaching_mode, mode_instructions["advise"])

        emotion_note = ""
        if emotion_data:
            label = emotion_data.get("label", "neutral")
            intensity = emotion_data.get("intensity", 0.5)
            if intensity > 0.7 and label not in ("neutral", "calm"):
                emotion_note = f"\n[User is feeling strong {label}.]"

        user_prompt = f"""MODE: {mode_text}{emotion_note}

USER: {user_message}

Reply in 2-3 sentences max. Sound human, not like a chatbot. One question max."""

        response = self.llm.call(user_prompt, system_prompt=system_prompt,
                                 temperature=0.8, max_tokens=150)
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
            "listen": "Just listen. Validate. No advice.",
            "advise": "One sharp piece of advice. No essays.",
            "challenge": "Push them. One tough question.",
            "celebrate": "Hype them up. Keep it real.",
        }
        mode_text = mode_instructions.get(coaching_mode, mode_instructions["advise"])

        batch_prompt = f"""Analyze this message AND generate a SHORT coaching response (2-3 sentences MAX).

MODE: {mode_text}

USER: "{user_message}"

Return JSON:
{{
    "emotion": {{
        "label": "one of: joy, excitement, gratitude, love, pride, calm, neutral, curious, stress, anxiety, sadness, loneliness, self_doubt, anger, frustration, hurt, fear, determination, hope, relief",
        "secondary": "optional secondary emotion or empty string",
        "intensity": 0.0 to 1.0,
        "trigger": "what triggered this emotion, or empty string"
    }},
    "entities": [
        {{
            "name": "entity name",
            "type": "person/place/event/thing",
            "relationship": "relationship to user if inferable",
            "facts": ["new facts about this entity"]
        }}
    ],
    "facts_about_user": ["new facts about the user"],
    "response": "2-3 sentence reply. Sound like a real friend, not a chatbot. One question max."
}}

Empty arrays if no entities or facts found."""

        result = self.llm.call_json(batch_prompt, system_prompt=system_prompt)

        # Ensure required fields exist
        if "error" in result:
            response = self.llm.call(
                f"MODE: {mode_text}\n\nUSER: {user_message}\n\nReply in 2-3 sentences. Sound human.",
                system_prompt=system_prompt,
                temperature=0.8,
                max_tokens=150,
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
            lines.append(f"- {g['title']} ({g['progress']}%, {g['category']})")
        return "\n".join(lines)
