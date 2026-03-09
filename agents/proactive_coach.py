"""
proactive_coach.py — Makes the coach LEAD conversations, not follow.
Generates context-aware insights, action items, and session agendas.
The coach talks like a teacher — gives direction, not questions.
"""

from datetime import datetime


class ProactiveCoach:
    """Generates proactive insights, session agendas, and minimal reply options."""

    def __init__(self, llm, db):
        self.llm = llm
        self.db = db

    def get_greeting(self) -> dict:
        """Generate a coach-led opening — a statement with insight, not a question."""
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

        prompt = f"""You are opening a coaching session. Generate a SHORT, COACH-LED opening.

CONTEXT:
{context}

RULES — FOLLOW THESE EXACTLY:
- DO NOT ask a question. Give a STATEMENT with an observation and action item.
- 2-3 sentences max. Sound like a sharp friend, not a chatbot.
- Example: "Hey Amey. Your coding streak is at 5 days, solid run. Today keep it light — one easy problem, keep the chain alive."
- Reference something specific from their data if possible.
- Generate exactly 2 reply options — one acknowledgment, one pushback. Keep them 2-4 words.
- NO emojis. NO exclamation marks overuse.

Return JSON:
{{
    "greeting": "Your 2-3 sentence coach-led statement with an observation and direction",
    "quick_replies": ["acknowledgment reply", "pushback reply"]
}}"""

        result = self.llm.call_json(prompt, temperature=0.8)

        if "error" in result:
            return self._fallback_greeting(user_name, time_of_day, goals)

        # Ensure max 2 replies
        if "quick_replies" in result:
            result["quick_replies"] = result["quick_replies"][:2]

        return result

    def get_quick_replies(self, coach_response: str, user_message: str,
                          emotion: str = "") -> list:
        """Generate exactly 2 minimal reply options — acknowledge or push back."""
        prompt = f"""The AI coach just said this:
"{coach_response}"

The user had said: "{user_message}"
User's current emotion: {emotion or 'unknown'}

Generate exactly 2 SHORT reply button options:
- One that ACKNOWLEDGES (e.g. "Got it", "Makes sense", "Fair point", "On it")
- One that PUSHES BACK or asks for more (e.g. "Not sure about that", "Why though", "Hard to do")
Each should be 2-4 words max. No emojis.

Return JSON:
{{"replies": ["acknowledgment", "pushback"]}}"""

        result = self.llm.call_json(prompt, temperature=0.7)

        if "error" in result or "replies" not in result:
            return self._fallback_replies(emotion)

        return result.get("replies", [])[:2]

    def get_session_agenda(self) -> list:
        """Generate a 3-4 item session agenda the coach will drive through."""
        goals = self.db.get_active_goals()
        recent_emotions = self.db.get_recent_emotions(10)
        checkins = self.db.get_recent_checkins(5)
        streak = self.db.get_streak()

        context_parts = []
        if goals:
            for g in goals[:3]:
                context_parts.append(f"Goal: {g['title']} at {g['progress']}%")
        if recent_emotions:
            moods = [e["emotion_label"] for e in recent_emotions[:5]]
            context_parts.append(f"Recent emotions: {', '.join(moods)}")
        if streak:
            context_parts.append(f"Streak: {streak} days")
        if checkins:
            last = checkins[-1]
            context_parts.append(f"Last check-in: mood {last.get('mood_label', 'unknown')}")

        context = "\n".join(context_parts) or "New user, no data yet."

        prompt = f"""You are a coach planning a quick session. Based on the user's data, create a 3-item agenda.

USER DATA:
{context}

RULES:
- Each item is a coach-led insight or action item (NOT a question to ask the user)
- Keep each item to 1-2 sentences
- Be specific, reference their actual data
- Order: observation about recent state -> goal check -> specific action item for today
- No emojis, no fluff

Return JSON:
{{
    "agenda": [
        {{"type": "observation", "content": "insight about their recent state"}},
        {{"type": "goal_check", "content": "specific note about a goal"}},
        {{"type": "action", "content": "one concrete thing to do today"}}
    ],
    "closing": "1 sentence wrap-up with today's game plan"
}}"""

        result = self.llm.call_json(prompt, temperature=0.7)

        if "error" in result:
            return self._fallback_agenda(goals, streak)

        return result

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
                            "message": f"{goal['title']} is due in {days_left} days. You're at {goal['progress']}%. Time to lock in.",
                            "quick_replies": ["On it", "Need to adjust"],
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
                    "message": "You've been in a rough patch lately. That's real. But sitting in it won't fix it — let's figure out what's dragging you down.",
                    "quick_replies": ["Yeah let's", "I'm handling it"],
                }

        # Check for stagnant goals
        if not nudge:
            for goal in goals:
                if goal["progress"] == 0:
                    nudge = {
                        "type": "stagnant_goal",
                        "message": f"'{goal['title']}' has been at 0% since you set it. Either start it today or drop it. No point carrying dead weight.",
                        "quick_replies": ["Starting today", "Remove it"],
                    }
                    break

        return nudge or {}

    def _fallback_greeting(self, name: str, time_of_day: str, goals: list) -> dict:
        if goals:
            goal = goals[0]
            return {
                "greeting": f"Hey{' ' + name if name else ''}. {goal['title']} is at {goal['progress']}%. Let's move that number today.",
                "quick_replies": ["On it", "That's tough"],
            }
        return {
            "greeting": f"Good {time_of_day}{' ' + name if name else ''}. New session, let's make it count.",
            "quick_replies": ["Ready", "Not feeling it"],
        }

    def _fallback_replies(self, emotion: str = "") -> list:
        if emotion in ("sadness", "anxiety", "stress"):
            return ["That helps", "Not sure"]
        return ["Got it", "Why though"]

    def _fallback_agenda(self, goals: list, streak: int) -> dict:
        agenda = []
        if streak:
            agenda.append({"type": "observation", "content": f"You're on a {streak}-day streak. Consistency is doing its thing."})
        else:
            agenda.append({"type": "observation", "content": "No streak going yet. Today's the day to start one."})

        if goals:
            g = goals[0]
            agenda.append({"type": "goal_check", "content": f"{g['title']} is at {g['progress']}%. Let's push that forward."})
        else:
            agenda.append({"type": "goal_check", "content": "You haven't set any goals yet. Pick one thing you want to move on."})

        agenda.append({"type": "action", "content": "Pick the smallest possible step and do it in the next 30 minutes."})

        return {
            "agenda": agenda,
            "closing": "One step. That's all. Go.",
        }
