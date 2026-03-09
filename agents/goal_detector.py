"""
goal_detector.py — Detects goal-related progress in chat messages.
When user mentions progress like "I cleared round 2" or "started gym today",
matches it against active goals and suggests updates.
"""


class GoalDetector:
    """Detects goal progress mentions in messages and suggests updates."""

    def __init__(self, llm, db):
        self.llm = llm
        self.db = db

    def detect_goal_update(self, user_message: str) -> dict:
        """
        Check if user message implies progress on any active goal.
        Returns dict with goal_id, suggested_progress, and reason.
        Returns empty dict if no match.
        """
        goals = self.db.get_active_goals()
        if not goals:
            return {}

        goals_text = "\n".join(
            f"- ID:{g['id']} | {g['title']} (currently {g['progress']}%, category: {g['category']})"
            for g in goals
        )

        prompt = f"""Does this user message indicate progress on any of their active goals?

USER MESSAGE: "{user_message}"

ACTIVE GOALS:
{goals_text}

If YES, return JSON:
{{
    "detected": true,
    "goal_id": <goal ID number>,
    "goal_title": "goal title",
    "current_progress": <current %>,
    "suggested_progress": <suggested new % based on what they said>,
    "reason": "brief reason for the update"
}}

If NO goal progress detected, return:
{{"detected": false}}

Be conservative. Only detect real progress, not vague mentions."""

        result = self.llm.call_json(prompt, temperature=0.2)

        if result.get("detected", False) and result.get("goal_id"):
            return result
        return {}

    def apply_update(self, goal_id: int, new_progress: int) -> bool:
        """Apply a goal progress update."""
        try:
            self.db.update_goal(goal_id, progress=min(new_progress, 100))
            if new_progress >= 100:
                from datetime import datetime
                self.db.update_goal(
                    goal_id,
                    status="completed",
                    completed_at=datetime.now().isoformat(),
                )
            return True
        except Exception:
            return False
