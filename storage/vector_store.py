"""
vector_store.py — ChromaDB vector store for semantic memory.
Collections: episodic_memory, semantic_memory, narrative_threads.
"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from datetime import datetime
from config import CHROMA_DIR, EMBEDDING_MODEL, RETRIEVAL_TOP_K, SIMILARITY_THRESHOLD


class VectorStore:
    """ChromaDB-backed semantic memory store."""

    def __init__(self, persist_dir: str = None):
        self.persist_dir = persist_dir or str(CHROMA_DIR)
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self._model = None

        # Initialize collections
        self.episodic = self.client.get_or_create_collection(
            name="episodic_memory",
            metadata={"description": "Timestamped conversation episodes"}
        )
        self.semantic = self.client.get_or_create_collection(
            name="semantic_memory",
            metadata={"description": "Facts and knowledge about the user"}
        )
        self.narratives = self.client.get_or_create_collection(
            name="narrative_threads",
            metadata={"description": "Ongoing story arcs and themes"}
        )

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(EMBEDDING_MODEL)
        return self._model

    def _embed(self, texts: list) -> list:
        if isinstance(texts, str):
            texts = [texts]
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    # ── Episodic Memory ───────────────────────────

    def store_episode(self, text: str, metadata: dict = None):
        """Store a conversation chunk as an episodic memory."""
        embedding = self._embed(text)
        doc_id = f"ep_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        meta = {
            "timestamp": datetime.now().isoformat(),
            "type": "episode",
        }
        if metadata:
            meta.update({k: str(v) for k, v in metadata.items()})

        self.episodic.add(
            ids=[doc_id],
            embeddings=embedding,
            documents=[text],
            metadatas=[meta],
        )

    def retrieve_episodes(self, query: str, top_k: int = None) -> list:
        """Retrieve relevant episodic memories."""
        top_k = top_k or RETRIEVAL_TOP_K
        if self.episodic.count() == 0:
            return []

        embedding = self._embed(query)
        results = self.episodic.query(
            query_embeddings=embedding,
            n_results=min(top_k, self.episodic.count()),
        )
        return self._format_results(results)

    # ── Semantic Memory ───────────────────────────

    def store_fact(self, fact: str, category: str = "general", metadata: dict = None):
        """Store a fact about the user."""
        # Check for duplicate facts
        if self.semantic.count() > 0:
            existing = self.semantic.query(
                query_embeddings=self._embed(fact),
                n_results=1,
            )
            if existing["distances"] and existing["distances"][0]:
                if existing["distances"][0][0] < 0.15:
                    return  # Too similar to existing fact, skip

        embedding = self._embed(fact)
        doc_id = f"fact_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        meta = {
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "type": "fact",
        }
        if metadata:
            meta.update({k: str(v) for k, v in metadata.items()})

        self.semantic.add(
            ids=[doc_id],
            embeddings=embedding,
            documents=[fact],
            metadatas=[meta],
        )

    def retrieve_facts(self, query: str, top_k: int = None) -> list:
        """Retrieve relevant facts about the user."""
        top_k = top_k or RETRIEVAL_TOP_K
        if self.semantic.count() == 0:
            return []

        embedding = self._embed(query)
        results = self.semantic.query(
            query_embeddings=embedding,
            n_results=min(top_k, self.semantic.count()),
        )
        return self._format_results(results)

    def get_all_facts(self) -> list:
        """Get all stored facts."""
        if self.semantic.count() == 0:
            return []
        results = self.semantic.get()
        facts = []
        for i, doc in enumerate(results["documents"]):
            meta = results["metadatas"][i] if results["metadatas"] else {}
            facts.append({"text": doc, "metadata": meta})
        return facts

    # ── Narrative Threads ─────────────────────────

    def store_narrative(self, narrative: str, thread_name: str = "",
                        metadata: dict = None):
        """Store or update a narrative thread."""
        embedding = self._embed(narrative)
        doc_id = f"narr_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        meta = {
            "timestamp": datetime.now().isoformat(),
            "thread_name": thread_name,
            "type": "narrative",
        }
        if metadata:
            meta.update({k: str(v) for k, v in metadata.items()})

        self.narratives.add(
            ids=[doc_id],
            embeddings=embedding,
            documents=[narrative],
            metadatas=[meta],
        )

    def retrieve_narratives(self, query: str, top_k: int = 3) -> list:
        """Retrieve relevant narrative threads."""
        if self.narratives.count() == 0:
            return []

        embedding = self._embed(query)
        results = self.narratives.query(
            query_embeddings=embedding,
            n_results=min(top_k, self.narratives.count()),
        )
        return self._format_results(results)

    # ── Unified Search ────────────────────────────

    def search_all(self, query: str, top_k: int = None) -> dict:
        """Search across all memory types."""
        top_k = top_k or RETRIEVAL_TOP_K
        return {
            "episodes": self.retrieve_episodes(query, top_k),
            "facts": self.retrieve_facts(query, top_k),
            "narratives": self.retrieve_narratives(query, min(3, top_k)),
        }

    # ── Similarity Check ──────────────────────────

    def find_similar_message(self, text: str, threshold: float = None) -> dict:
        """Check if a similar message exists in episodic memory."""
        threshold = threshold or SIMILARITY_THRESHOLD
        if self.episodic.count() == 0:
            return None

        embedding = self._embed(text)
        results = self.episodic.query(
            query_embeddings=embedding,
            n_results=1,
        )

        if results["distances"] and results["distances"][0]:
            distance = results["distances"][0][0]
            # ChromaDB returns L2 distance by default; lower = more similar
            if distance < (1 - threshold):
                return {
                    "text": results["documents"][0][0],
                    "distance": distance,
                    "metadata": results["metadatas"][0][0] if results["metadatas"] else {},
                }
        return None

    # ── Stats ─────────────────────────────────────

    def get_stats(self) -> dict:
        return {
            "episodes": self.episodic.count(),
            "facts": self.semantic.count(),
            "narratives": self.narratives.count(),
            "total": self.episodic.count() + self.semantic.count() + self.narratives.count(),
        }

    # ── Helpers ───────────────────────────────────

    def _format_results(self, results: dict) -> list:
        formatted = []
        if not results["documents"]:
            return formatted

        for i, doc in enumerate(results["documents"][0]):
            entry = {
                "text": doc,
                "distance": results["distances"][0][i] if results["distances"] else 0,
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
            }
            formatted.append(entry)
        return formatted
