from typing import TypedDict, List, Dict, Any, Optional, Annotated
import operator


class ContractAgentState(TypedDict):
    contract_text: str
    contract_type: str
    metadata: Dict[str, Any]
    clauses: List[Dict[str, Any]]
    analyzed_clauses: Annotated[List[Dict[str, Any]], operator.add]
    redlines: List[Dict[str, Any]]
    negotiation_strategy: Dict[str, Any]
    overall_risk_score: float
    messages: Annotated[List[str], operator.add]
    error: Optional[str]
