from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class ContractResponse(BaseModel):
    id: int
    filename: str
    contract_type: Optional[str]
    status: str
    overall_risk_score: Optional[float]
    summary: Optional[str]
    parties: Optional[Dict[str, Any]]
    key_dates: Optional[Dict[str, Any]]
    clauses: Optional[List[Dict[str, Any]]]
    redlines: Optional[List[Dict[str, Any]]]
    negotiation_strategy: Optional[Dict[str, Any]]
    created_at: datetime

    model_config = {"from_attributes": True}


class ContractListItem(BaseModel):
    id: int
    filename: str
    contract_type: Optional[str]
    status: str
    overall_risk_score: Optional[float]
    created_at: datetime

    model_config = {"from_attributes": True}


class SearchRequest(BaseModel):
    query: str
    clause_type: Optional[str] = None
    limit: int = 10


class SearchResult(BaseModel):
    text: str
    clause_type: str
    contract_type: str
    score: float
