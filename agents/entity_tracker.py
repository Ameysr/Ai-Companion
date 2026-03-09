"""
entity_tracker.py — Tracks people, places, and events the user mentions.
Maintains a relationship map that persists across sessions.
"""

from storage.database import Database


class EntityTracker:
    """Agent responsible for tracking entities mentioned by the user."""

    def __init__(self, db: Database, llm=None):
        self.db = db
        self.llm = llm

    def extract_entities(self, text: str) -> list:
        """Extract entities from user message using LLM."""
        if not self.llm:
            return []

        prompt = f"""Extract ALL people, places, and significant events/things mentioned in this message.
Return a JSON array. If none found, return an empty array [].

Each entity should have:
- "name": the entity name
- "type": "person", "place", "event", or "thing"
- "relationship": how they relate to the user (if inferable), or empty string
- "facts": array of new facts learned about this entity from this message

Message: "{text}"

Return ONLY the JSON array, nothing else."""

        result = self.llm.call_json(f"[wrapper]{prompt}")
        # Handle list response
        raw = self.llm.call(prompt, temperature=0.2, max_tokens=512)
        raw = raw.strip()
        if raw.startswith("```json"):
            raw = raw[7:]
        if raw.startswith("```"):
            raw = raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        try:
            import json
            entities = json.loads(raw)
            if isinstance(entities, list):
                return entities
        except Exception:
            pass
        return []

    def update_entities(self, entities: list):
        """Store or update extracted entities in the database."""
        for entity in entities:
            if not isinstance(entity, dict):
                continue
            name = entity.get("name", "").strip()
            if not name or len(name) < 2:
                continue

            self.db.add_entity(
                name=name,
                entity_type=entity.get("type", "person"),
                relationship=entity.get("relationship", ""),
                facts=entity.get("facts", []),
            )

    def get_entity_context(self, text: str) -> str:
        """Get context about entities mentioned in the message."""
        all_entities = self.db.get_all_entities()
        if not all_entities:
            return "No known entities yet."

        # Check which known entities appear in the text
        text_lower = text.lower()
        relevant = []
        for entity in all_entities:
            if entity["name"].lower() in text_lower:
                relevant.append(entity)

        if not relevant:
            # Return top entities by mention count
            top = sorted(all_entities, key=lambda x: x["mention_count"], reverse=True)[:5]
            if top:
                lines = []
                for e in top:
                    facts_str = "; ".join(e["facts"][:3]) if e["facts"] else "no details yet"
                    lines.append(
                        f"- {e['name']} ({e['entity_type']}): "
                        f"{e['relationship'] or 'relationship unknown'}. "
                        f"Facts: {facts_str}. Mentioned {e['mention_count']}x."
                    )
                return "Known people/entities:\n" + "\n".join(lines)
            return "No known entities yet."

        lines = []
        for e in relevant:
            facts_str = "; ".join(e["facts"]) if e["facts"] else "no details yet"
            lines.append(
                f"- {e['name']} ({e['entity_type']}): "
                f"{e['relationship'] or 'relationship unknown'}. "
                f"Facts: {facts_str}. "
                f"First mentioned: {e['first_mentioned']}. "
                f"Mentioned {e['mention_count']}x total."
            )
        return "Relevant entities in this message:\n" + "\n".join(lines)

    def get_all_entities_display(self) -> list:
        """Get all entities formatted for UI display."""
        entities = self.db.get_all_entities()
        return [
            {
                "name": e["name"],
                "type": e["entity_type"],
                "relationship": e["relationship"],
                "facts": e["facts"],
                "mentions": e["mention_count"],
                "first_seen": e["first_mentioned"],
                "last_seen": e["last_mentioned"],
            }
            for e in entities
        ]
