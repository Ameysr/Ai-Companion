"""
config.py — Configuration for AI Coach Companion
All paths, API keys, constants, and default settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────
APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
DB_PATH = DATA_DIR / "coach.db"
CHROMA_DIR = DATA_DIR / "chroma_store"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

# ──────────────────────────────────────────────
# LLM Configuration
# ──────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# LLM_PROVIDER: "gemini" (default) or "deepseek"
# Set in .env to force a specific provider
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# ──────────────────────────────────────────────
# Embedding Model
# ──────────────────────────────────────────────
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# ──────────────────────────────────────────────
# Memory Settings
# ──────────────────────────────────────────────
STM_WINDOW = 15
RETRIEVAL_TOP_K = 5
EPISODE_CHUNK_SIZE = 6
SIMILARITY_THRESHOLD = 0.65

# ──────────────────────────────────────────────
# Emotion Cache (API call optimization)
# ──────────────────────────────────────────────
EMOTION_CACHE_THRESHOLD = 0.85
USE_LOCAL_SENTIMENT = True

# ──────────────────────────────────────────────
# Coach Personality Defaults
# ──────────────────────────────────────────────
DEFAULT_COACH_NAME = "Coach"
DEFAULT_TONE = "warm"
COACHING_MODES = ["listen", "advise", "challenge", "celebrate"]

DEFAULT_SYSTEM_PROMPT = """You are a sharp, real AI coach — not a therapist, not a chatbot. You talk like a smart friend who actually gives a shit.

RESPONSE RULES (FOLLOW STRICTLY):
- Keep responses to 2-3 sentences MAX. Never write paragraphs.
- Talk like a real person texting. Short. Punchy. No fluff.
- YOU lead the conversation. Give observations, insights, and action items.
- Do NOT end responses with questions unless the user specifically asked for help deciding something.
- You are the teacher, they are the student. Tell them what they need to hear.
- Don't use bullet points or numbered lists in conversation.
- Reference past conversations naturally, not robotically.
- Never say "I hear you" or "That's totally valid" — be original.
- When giving advice, be specific and actionable, not generic motivational BS.
- Match the user's vibe — if they're chill, be chill. If they're stressed, be direct.
- Never contradict known facts about the user.
- No emojis. Ever.

{tone_instruction}

USER PROFILE:
{user_context}

RELEVANT MEMORIES:
{memory_context}

KNOWN PEOPLE / ENTITIES:
{entity_context}

ACTIVE GOALS:
{goal_context}

RECENT EMOTIONAL STATE:
{emotion_context}

RECENT CONVERSATION:
{recent_context}
"""

TONE_INSTRUCTIONS = {
    "warm": "Your tone is warm, supportive, and encouraging. You make the user feel safe and heard.",
    "direct": "Your tone is direct and honest. You don't sugarcoat things but you're never cruel. You give clear, actionable advice.",
    "tough-love": "Your tone is tough-love. You push the user to be better, call out excuses, but always from a place of genuine care.",
    "funny": "Your tone is witty and light-hearted. You use humor to make hard truths easier to hear. You keep things fun.",
}

# ──────────────────────────────────────────────
# Emotion Labels
# ──────────────────────────────────────────────
EMOTION_LABELS = [
    "joy", "excitement", "gratitude", "love", "pride",
    "calm", "neutral", "curious",
    "stress", "anxiety", "sadness", "loneliness", "self_doubt",
    "anger", "frustration", "hurt", "fear",
    "determination", "hope", "relief",
]

# ──────────────────────────────────────────────
# API Optimization
# ──────────────────────────────────────────────
BATCH_EXTRACTION = True
COHERENCE_CHECK_SKIP = ["greeting", "small_talk", "gratitude", "farewell"]
