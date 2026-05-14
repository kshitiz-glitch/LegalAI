import asyncio
import logging
import pickle
import os
from typing import List, Dict, Optional
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue,
)
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

from app.core.config import settings

logger = logging.getLogger(__name__)


class RAGEngine:
    """Singleton. Hybrid BM25 + vector search with optional cross-encoder reranking."""

    _instance: Optional["RAGEngine"] = None

    def __new__(cls) -> "RAGEngine":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._ready = False
        return cls._instance

    def __init__(self) -> None:
        if self._ready:
            return

        self.qdrant = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY, timeout=30)
        self.bi_encoder = SentenceTransformer("all-MiniLM-L6-v2")

        try:
            from sentence_transformers import CrossEncoder
            self.cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
            logger.info("CrossEncoder loaded successfully.")
        except Exception as e:
            logger.warning("CrossEncoder failed to load (%s). Reranking disabled.", e)
            self.cross_encoder = None

        self._ensure_collection()
        self._load_bm25()
        self._ready = True

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _ensure_collection(self) -> None:
        existing = [c.name for c in self.qdrant.get_collections().collections]
        if settings.QDRANT_COLLECTION not in existing:
            self.qdrant.create_collection(
                collection_name=settings.QDRANT_COLLECTION,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
        # Payload index required for filtered vector search
        try:
            self.qdrant.create_payload_index(
                collection_name=settings.QDRANT_COLLECTION,
                field_name="clause_type",
                field_schema="keyword",
            )
            logger.info("Qdrant payload index created for 'clause_type'.")
        except Exception:
            pass  # Already exists

    def _load_bm25(self) -> None:
        path = settings.BM25_INDEX_PATH
        if os.path.exists(path):
            with open(path, "rb") as f:
                data = pickle.load(f)
            self.bm25 = data["index"]
            self.bm25_corpus = data["corpus"]
            self.bm25_payloads = data["payloads"]
        else:
            self.bm25 = None
            self.bm25_corpus = []
            self.bm25_payloads = []

    # ------------------------------------------------------------------
    # Indexing (called by data pipeline scripts)
    # ------------------------------------------------------------------

    def index_clauses(self, clauses: List[Dict]) -> int:
        points = []
        for clause in clauses:
            vec = self.bi_encoder.encode(clause["text"], convert_to_numpy=True).tolist()
            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vec,
                    payload={
                        "text": clause["text"],
                        "clause_type": clause.get("clause_type", "general"),
                        "contract_type": clause.get("contract_type", "unknown"),
                    },
                )
            )

        self.qdrant.upsert(collection_name=settings.QDRANT_COLLECTION, points=points)
        return len(points)

    def build_and_save_bm25(self, clauses: List[Dict]) -> None:
        corpus = [c["text"] for c in clauses]
        tokenized = [doc.lower().split() for doc in corpus]
        index = BM25Okapi(tokenized)

        os.makedirs(os.path.dirname(settings.BM25_INDEX_PATH) or ".", exist_ok=True)
        with open(settings.BM25_INDEX_PATH, "wb") as f:
            pickle.dump({"index": index, "corpus": corpus, "payloads": clauses}, f)

        self.bm25 = index
        self.bm25_corpus = corpus
        self.bm25_payloads = clauses

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def _vector_search(self, query: str, k: int, clause_type: Optional[str]) -> List[Dict]:
        vec = self.bi_encoder.encode(query, convert_to_numpy=True).tolist()
        filt = None
        if clause_type:
            filt = Filter(must=[FieldCondition(key="clause_type", match=MatchValue(value=clause_type))])

        hits = self.qdrant.search(
            collection_name=settings.QDRANT_COLLECTION,
            query_vector=vec,
            query_filter=filt,
            limit=k,
            with_payload=True,
        )
        return [{"text": h.payload["text"], "clause_type": h.payload.get("clause_type", "general"),
                 "contract_type": h.payload.get("contract_type", "unknown"), "score": h.score}
                for h in hits]

    def _bm25_search(self, query: str, k: int) -> List[Dict]:
        if not self.bm25:
            return []
        scores = self.bm25.get_scores(query.lower().split())
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        results = []
        for idx in top_indices:
            p = self.bm25_payloads[idx]
            results.append({
                "text": self.bm25_corpus[idx],
                "clause_type": p.get("clause_type", "general"),
                "contract_type": p.get("contract_type", "unknown"),
                "score": float(scores[idx]),
            })
        return results

    @staticmethod
    def _reciprocal_rank_fusion(*ranked_lists: List[Dict], k: int = 60) -> List[Dict]:
        scores: Dict[str, float] = {}
        docs: Dict[str, Dict] = {}

        for ranked in ranked_lists:
            for rank, doc in enumerate(ranked):
                key = doc["text"][:200]
                scores[key] = scores.get(key, 0.0) + 1.0 / (rank + k)
                docs[key] = doc

        fused = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [docs[key] for key, _ in fused]

    def _rerank(self, query: str, candidates: List[Dict]) -> List[Dict]:
        if not candidates or self.cross_encoder is None:
            return candidates
        pairs = [(query, c["text"]) for c in candidates]
        ce_scores = self.cross_encoder.predict(pairs)
        ranked = sorted(zip(ce_scores, candidates), key=lambda x: x[0], reverse=True)
        return [doc for _, doc in ranked]

    async def search(self, query: str, clause_type: Optional[str] = None, limit: int = 5) -> List[Dict]:
        vec_results = await asyncio.to_thread(self._vector_search, query, 20, clause_type)
        bm25_results = self._bm25_search(query, 20)
        fused = self._reciprocal_rank_fusion(vec_results, bm25_results)
        reranked = await asyncio.to_thread(self._rerank, query, fused[:20])
        return reranked[:limit]
