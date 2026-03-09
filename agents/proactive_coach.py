"""
proactive_coach.py — Makes the coach lead conversations instead of waiting.
Generates context-aware greetings, quick-reply buttons, and proactive nudges.
"""

from datetime import datetime


class ProactiveCoach:
    """Generates proactive questions, quick replies, and conversation starters."""

    def __init__(self, llm, db):
        self.llm = llm
        self.db = db

    def get_greeting(self) -> dict:
        """Generate a context-aware opening question when user opens the app."""
        profile = self.db.get_user_profile() or {}
        user_name = profile.get("name", "")
        goals = self.db.get_active_goals()
        recent_emotions = self.db.get_recent_emotions(5)
        checkins = self.db.get_recent_checkins(3)
        streak = self.db.get_streak()
        messages = self.db.get_recent_messages(5)

        hour = datetime.now().hour
        if hour < 12:
            time_of_day = "morning"
        elif hour < 17:
            time_of_day = "afternoon"
        else:
            time_of_day = "evening"

        # Build context for LLM
        context_parts = []
        if user_name:
            context_parts.append(f"User's name: {user_name}")
        context_parts.append(f"Time: {time_of_day}")

        if goals:
            goal_list = ", ".join(f"{g['title']} ({g['progress']}%)" for g in goals[:3])
            context_parts.append(f"Active goals: {goal_list}")

        if recent_emotions:
            moods = [e["emotion_label"] for e in recent_emotions[:3]]
            context_parts.append(f"Recent moods: {', '.join(moods)}")

        if streak > 0:
            context_parts.append(f"Current streak: {streak} days")

        if messages:
            last_msg = next((m for m in reversed(messages) if m["role"] == "user"), None)
            if last_msg:
                context_parts.append(f"Last thing they said: \"{last_msg['content'][:100]}\"")

        if checkins:
            last_checkin = checkins[-1]
            context_parts.append(f"Last check-in mood: {last_checkin.get('mood_label', 'unknown')}")

        context = "\n".join(context_parts)

        prompt = f"""Generate a SHORT proactive greeting for the user when they open the app.

CONTEXT:
{context}

RULES:
- Ask ONE specific question based on their context (goals, mood, last conversation)
- Keep it to 1-2 sentences MAX
- Sound like a real friend, not a chatbot
- Reference something specific from their history if possible
- Also generate 3-4 quick-reply buttons the user can tap instead of typing

Return JSON:
{{
    "greeting": "Your 1-2 sentence greeting with a question",
    "quick_replies": ["reply option 1", "reply option 2", "reply option 3"]
}}"""

        result = self.llm.call_json(prompt, temperature=0.8)

        if "error" in result:
            # Fallback
            return self._fallback_greeting(user_name, time_of_day, goals)

        return result

    def get_quick_replies(self, coach_response: str, user_message: str,
                          emotion: str = "") -> list:
        """Generate contextual quick-reply buttons after a coach response."""
        prompt = f"""The AI coach just said this to the user:
"{coach_response}"

The user had said: "{user_message}"
User's current emotion: {emotion or 'unknown'}

Generate 3 SHORT quick-reply button options the user might want to tap.
Each should be 2-5 words max. Make them feel natural, not robotic.
One should be positive, one neutral, one that asks for more.

Return JSON:
{{"replies": ["reply 1", "reply 2", "reply 3"]}}"""

        result = self.llm.call_json(prompt, temperature=0.7)

        if "error" in result or "replies" not in result:
            return self._fallback_replies(emotion)

        return result.get("replies", [])[:4]

    def get_proactive_nudge(self) -> dict:
        """Check if we should proactively bring up a topic."""
        goals = self.db.get_active_goals()
        recent_emotions = self.db.get_recent_emotions(10)
        checkins = self.db.get_recent_checkins(5)

        nudge = None

        # Check for approaching deadlines
        for goal in goals:
            if goal.get("target_date"):
                try:
                    target = datetime.strptime(goal["target_date"], "%Y-%m-%d")
                    days_left = (target - datetime.now()).days
                    if 0 < days_left <= 7:
                        nudge = {
                            "type": "deadline",
                            "message": f"{goal['title']} deadline is in {days_left} days. You're at {goal['progress']}%.",
                            "quick_replies": ["Let's plan", "I'm on it", "Need to adjust"],
                        }
                        break
                except ValueError:
                    pass

        # Check for emotional patterns
        if not nudge and len(recent_emotions) >= 3:
            negative = [e for e in recent_emotions[:5]
                        if e["emotion_label"] in ("sadness", "anxiety", "stress", "frustration", "self_doubt")]
            if len(negative) >= 3:
                nudge = {
                    "type": "emotional",
                    "message": "You've been going through a tough stretch. Want to talk about what's weighing on you?",
                    "quick_replies": ["Yeah let's talk", "I'm managing", "Just tired"],
                }

        # Check for stagnant goals
        if not nudge:
            for goal in goals:
                if goal["progress"] == 0:
                    nudge = {
                        "type": "stagnant_goal",
                        "message": f"'{goal['title']}' is still at 0%. What's the first small step you can take?",
                        "quick_replies": ["Good point", "I started actually", "Remove this goal"],
                    }
                    break

        return nudge or {}

    def _fallback_greeting(self, name: str, time_of_day: str, goals: list) -> dict:
        if goals:
            goal = goals[0]
            return {
                "greeting": f"Hey{' ' + name if name else ''}. How's {goal['title']} going today?",
                "quick_replies": ["Made progress", "Stuck", "Haven't started"],
            }
        return {
            "greeting": f"What's on your mind this {time_of_day}?",
            "quick_replies": ["Feeling good", "Need advice", "Just venting"],
        }

    def _fallback_replies(self, emotion: str = "") -> list:
        if emotion in ("sadness", "anxiety", "stress"):
            return ["That helps", "Tell me more", "I'll try that"]
        return ["Got it", "Tell me more", "What else?"]
