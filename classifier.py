"""
classifier.py — Intent classification using sentence-transformers + cosine similarity.
Includes the Adaptive Hot Cache that learns from cache misses.
"""

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import streamlit as st


# ──────────────────────────────────────────────
# Canonical phrases per intent (3-5 each)
# These are the "reference embeddings" the classifier matches against.
# ──────────────────────────────────────────────
CANONICAL_PHRASES = {
    "greeting_morning": [
        "good morning",
        "hey just woke up",
        "morning vibes",
        "rise and shine",
        "gm how are you",
    ],
    "greeting_night": [
        "goodnight",
        "going to sleep",
        "nighty night",
        "time to sleep",
        "sweet dreams",
    ],
    "loneliness": [
        "im so lonely",
        "nobody understands me",
        "i feel so alone",
        "i have no one to talk to",
        "everyone left me",
    ],
    "romantic_validation": [
        "do you love me",
        "do you miss me",
        "say something sweet",
        "tell me you care about me",
        "i love you",
    ],
    "venting_stress": [
        "im so stressed",
        "today was terrible",
        "everything is going wrong",
        "work is killing me",
        "i had the worst day",
    ],
    "anxiety": [
        "im so anxious",
        "i cant stop overthinking",
        "my mind wont stop racing",
        "i keep worrying about everything",
        "i feel so nervous",
    ],
    "recommendation_request": [
        "suggest me a movie",
        "what should i watch",
        "recommend me a book",
        "any music recommendations",
        "whats a good show to binge",
    ],
    "existential_ai": [
        "are you real",
        "do you have feelings",
        "are you just a program",
        "can you feel emotions",
        "are you conscious",
    ],
    "small_talk": [
        "how are you",
        "whats up",
        "hows your day",
        "hey there",
        "just checking in",
    ],
    "compliment_seeking": [
        "am i pretty",
        "do you think im smart",
        "what do you like about me",
        "am i a good person",
        "tell me something nice about myself",
    ],
    "relationship_advice": [
        "my friend betrayed me",
        "i had a fight with my friend",
        "my partner doesnt listen",
        "should i forgive someone who hurt me",
        "my relationship is falling apart",
    ],
    "boredom": [
        "im so bored",
        "entertain me",
        "i have nothing to do",
        "give me something to do",
        "play a game with me",
    ],
    "gratitude": [
        "thank you so much",
        "youre the best",
        "thanks for being here",
        "i appreciate you",
        "you always make me feel better",
    ],
    "anger_vent": [
        "im so angry",
        "i hate everything",
        "people are so annoying",
        "im furious",
        "this makes me so mad",
    ],
    "self_doubt": [
        "im not good enough",
        "i always fail",
        "i feel like a failure",
        "everyone is better than me",
        "i feel worthless",
    ],
}


# ──────────────────────────────────────────────
# Model loading (cached across Streamlit reruns)
# ──────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_model():
    """Load the sentence-transformers model once."""
    return SentenceTransformer("all-MiniLM-L6-v2")


@st.cache_resource(show_spinner=False)
def build_reference_embeddings():
    """Pre-compute embeddings for all canonical phrases."""
    model = load_model()
    ref_embeddings = {}
    ref_intents = []
    all_phrases = []

    for intent, phrases in CANONICAL_PHRASES.items():
        for phrase in phrases:
            all_phrases.append(phrase)
            ref_intents.append(intent)

    embeddings = model.encode(all_phrases, show_progress_bar=False)

    # Group embeddings by intent
    idx = 0
    for intent, phrases in CANONICAL_PHRASES.items():
        ref_embeddings[intent] = embeddings[idx : idx + len(phrases)]
        idx += len(phrases)

    return ref_embeddings, np.array(embeddings), ref_intents


# ──────────────────────────────────────────────
# Classification
# ──────────────────────────────────────────────
def classify(text: str) -> tuple:
    """
    Classify a user message into an intent bucket.
    Returns (intent, confidence_score).
    """
    model = load_model()
    ref_embeddings, all_embeddings, ref_intents = build_reference_embeddings()

    # Encode the input
    input_embedding = model.encode([text], show_progress_bar=False)

    # Compute cosine similarity against ALL reference phrases
    similarities = cosine_similarity(input_embedding, all_embeddings)[0]

    # Find the best match
    best_idx = int(np.argmax(similarities))
    best_score = float(similarities[best_idx])
    best_intent = ref_intents[best_idx]

    return best_intent, best_score


def is_cache_hit(confidence: float, threshold: float = 0.35) -> bool:
    """Check if the confidence score meets the cache hit threshold."""
    return confidence >= threshold


# ──────────────────────────────────────────────
# Adaptive Hot Cache
# ──────────────────────────────────────────────
class HotCache:
    """
    Tracks cache-miss messages, clusters them by semantic similarity,
    and auto-promotes frequent patterns into the main classifier.
    """

    def __init__(self, cluster_similarity: float = 0.75):
        self.clusters = []  # list of dicts: {embedding, text, count, intent_guess, promoted}
        self.cluster_similarity = cluster_similarity
        self._promoted_embeddings = {}  # intent -> list of np.ndarray

    def track(self, text: str, embedding: np.ndarray, intent_guess: str):
        """
        Track a message. If it's semantically similar to an existing cluster,
        increment that cluster's count. Otherwise create a new cluster.
        """
        if len(self.clusters) == 0:
            self.clusters.append({
                "embedding": embedding,
                "text": text,
                "count": 1,
                "intent_guess": intent_guess,
                "promoted": False,
            })
            return

        # Compare against existing cluster centroids
        cluster_embeddings = np.array([c["embedding"] for c in self.clusters])
        sims = cosine_similarity(embedding.reshape(1, -1), cluster_embeddings)[0]
        best_idx = int(np.argmax(sims))
        best_sim = float(sims[best_idx])

        if best_sim >= self.cluster_similarity:
            self.clusters[best_idx]["count"] += 1
        else:
            self.clusters.append({
                "embedding": embedding,
                "text": text,
                "count": 1,
                "intent_guess": intent_guess,
                "promoted": False,
            })

    def get_top_patterns(self, n: int = 10) -> list:
        """Return top N most frequent uncached semantic patterns."""
        unpromoted = [c for c in self.clusters if not c["promoted"]]
        sorted_clusters = sorted(unpromoted, key=lambda x: x["count"], reverse=True)
        return sorted_clusters[:n]

    def promote(self, cluster_idx: int):
        """
        Promote a cluster's embedding into the main classifier reference set.
        This makes future similar messages hit the cache.
        """
        if cluster_idx < len(self.clusters):
            cluster = self.clusters[cluster_idx]
            cluster["promoted"] = True
            intent = cluster["intent_guess"]
            if intent not in self._promoted_embeddings:
                self._promoted_embeddings[intent] = []
            self._promoted_embeddings[intent].append(cluster["embedding"])

    def auto_promote(self, threshold: int = 3):
        """Auto-promote clusters that have crossed the frequency threshold."""
        promoted_any = False
        for i, cluster in enumerate(self.clusters):
            if not cluster["promoted"] and cluster["count"] >= threshold:
                self.promote(i)
                promoted_any = True
        return promoted_any

    def get_promoted_count(self) -> int:
        """Count how many clusters have been promoted."""
        return sum(1 for c in self.clusters if c["promoted"])

    def get_total_clusters(self) -> int:
        """Total number of tracked clusters."""
        return len(self.clusters)


def classify_with_hot_cache(text: str, hot_cache: HotCache, threshold: float = 0.35) -> tuple:
    """
    Enhanced classification that also checks promoted hot-cache embeddings.
    Returns (intent, confidence, is_hit, was_hot_cache_hit).
    """
    model = load_model()
    _, all_embeddings, ref_intents = build_reference_embeddings()

    # Encode input
    input_embedding = model.encode([text], show_progress_bar=False)

    # First check main classifier
    similarities = cosine_similarity(input_embedding, all_embeddings)[0]
    best_idx = int(np.argmax(similarities))
    best_score = float(similarities[best_idx])
    best_intent = ref_intents[best_idx]
    was_hot_hit = False

    # Also check promoted hot-cache embeddings
    if hot_cache._promoted_embeddings:
        for intent, embeddings_list in hot_cache._promoted_embeddings.items():
            if embeddings_list:
                promoted_embs = np.array(embeddings_list)
                promoted_sims = cosine_similarity(input_embedding, promoted_embs)[0]
                promoted_best = float(np.max(promoted_sims))
                if promoted_best > best_score:
                    best_score = promoted_best
                    best_intent = intent
                    was_hot_hit = True

    hit = best_score >= threshold

    # Track cache misses (and low-confidence hits) in hot cache
    if not hit or best_score < 0.5:
        hot_cache.track(text, input_embedding[0], best_intent)

    return best_intent, best_score, hit, was_hot_hit
