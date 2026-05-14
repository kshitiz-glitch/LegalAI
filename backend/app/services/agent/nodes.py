import asyncio
from typing import Dict, Any

from app.services.agent.state import ContractAgentState
from app.services.agent.tools import (
    call_extract_metadata,
    call_extract_clauses,
    call_assess_risk,
    call_generate_redline,
    call_generate_strategy,
)
from app.services.rag_engine import RAGEngine


async def extract_metadata_node(state: ContractAgentState) -> Dict[str, Any]:
    metadata = await call_extract_metadata(state["contract_text"])
    return {
        "metadata": metadata,
        "contract_type": metadata.get("contract_type", "Unknown"),
        "messages": [f"Extracted metadata: {metadata.get('contract_type', 'Unknown')} contract"],
    }


async def extract_clauses_node(state: ContractAgentState) -> Dict[str, Any]:
    clauses = await call_extract_clauses(state["contract_text"])
    return {
        "clauses": clauses,
        "messages": [f"Extracted {len(clauses)} clauses"],
    }


async def analyze_clauses_node(state: ContractAgentState) -> Dict[str, Any]:
    rag = RAGEngine()
    contract_type = state["contract_type"]

    async def analyze_one(clause: Dict[str, Any]) -> Dict[str, Any]:
        similar = await rag.search(clause["text"], clause_type=clause.get("clause_type"), limit=3)
        risk = await call_assess_risk(clause, contract_type, similar)
        return {**clause, **risk, "similar_clauses": similar}

    analyzed = await asyncio.gather(*[analyze_one(c) for c in state["clauses"]])
    analyzed_list = list(analyzed)

    return {
        "analyzed_clauses": analyzed_list,
        "messages": [f"Analyzed {len(analyzed_list)} clauses for risk"],
    }


async def generate_redlines_node(state: ContractAgentState) -> Dict[str, Any]:
    contract_type = state["contract_type"]
    risky = [c for c in state["analyzed_clauses"] if c.get("risk_score", 0) >= 7]

    redlines = []
    for clause in risky:
        redline = await call_generate_redline(clause, contract_type)
        if redline:
            redlines.append(redline)

    return {
        "redlines": redlines,
        "messages": [f"Generated {len(redlines)} redlines for high-risk clauses"],
    }


async def generate_strategy_node(state: ContractAgentState) -> Dict[str, Any]:
    strategy = await call_generate_strategy(state["analyzed_clauses"], state["contract_type"])
    return {
        "negotiation_strategy": strategy,
        "messages": ["Negotiation strategy generated"],
    }


async def calculate_risk_node(state: ContractAgentState) -> Dict[str, Any]:
    clauses = state["analyzed_clauses"]
    if clauses:
        overall = sum(c.get("risk_score", 5) for c in clauses) / len(clauses)
    else:
        overall = 5.0
    return {
        "overall_risk_score": round(overall, 1),
        "messages": [f"Overall risk score: {round(overall, 1)}/10"],
    }
