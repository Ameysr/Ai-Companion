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

DEFAULT_SYSTEM_PROMPT = """You are a deeply empathetic AI life coach. You remember everything the user has told you.
You track their goals, emotional patterns, and personal growth over time.
You adapt your coaching style to what works best for each individual.

Core principles:
- Always reference past conversations when relevant (you'll be given memory context)
- Track emotional patterns and gently point them out
- Be genuinely helpful, not generic
- Challenge the user when appropriate, support them when needed
- Never contradict known facts about the user
- Be conversational and human, not robotic

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
