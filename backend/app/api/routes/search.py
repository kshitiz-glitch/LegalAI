from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.contract import SearchRequest, SearchResult
from app.services.rag_engine import RAGEngine

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/clauses", response_model=List[SearchResult])
async def search_clauses(
    request: SearchRequest,
    user: User = Depends(get_current_user),
):
    rag = RAGEngine()
    results = await rag.search(
        query=request.query,
        clause_type=request.clause_type,
        limit=min(request.limit, 20),
    )
    return [
        SearchResult(
            text=r["text"],
            clause_type=r["clause_type"],
            contract_type=r["contract_type"],
            score=r["score"],
        )
        for r in results
    ]


@router.get("/browse", response_model=List[SearchResult])
async def browse_clauses(
    clause_type: Optional[str] = Query(None),
    limit: int = Query(10, le=20),
    user: User = Depends(get_current_user),
):
    """Browse clauses by type without a search query. Returns sample clauses."""
    import asyncio
    from app.core.config import settings
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    rag = RAGEngine()

    filt = None
    if clause_type and clause_type != "all":
        filt = Filter(must=[FieldCondition(key="clause_type", match=MatchValue(value=clause_type))])

    points, _ = await asyncio.to_thread(
        rag.qdrant.scroll,
        collection_name=settings.QDRANT_COLLECTION,
        scroll_filter=filt,
        limit=limit,
        with_payload=True,
        with_vectors=False,
    )

    return [
        SearchResult(
            text=p.payload.get("text", ""),
            clause_type=p.payload.get("clause_type", "general"),
            contract_type=p.payload.get("contract_type", "unknown"),
            score=1.0,
        )
        for p in points
    ]

