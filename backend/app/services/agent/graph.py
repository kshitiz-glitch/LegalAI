from langgraph.graph import StateGraph, END
from app.services.agent.state import ContractAgentState
from app.services.agent.nodes import (
    extract_metadata_node,
    extract_clauses_node,
    analyze_clauses_node,
    generate_redlines_node,
    generate_strategy_node,
    calculate_risk_node,
)


def build_contract_graph():
    graph = StateGraph(ContractAgentState)

    graph.add_node("extract_metadata", extract_metadata_node)
    graph.add_node("extract_clauses", extract_clauses_node)
    graph.add_node("analyze_clauses", analyze_clauses_node)
    graph.add_node("generate_redlines", generate_redlines_node)
    graph.add_node("generate_strategy", generate_strategy_node)
    graph.add_node("calculate_risk", calculate_risk_node)

    graph.set_entry_point("extract_metadata")
    graph.add_edge("extract_metadata", "extract_clauses")
    graph.add_edge("extract_clauses", "analyze_clauses")
    graph.add_edge("analyze_clauses", "generate_redlines")
    graph.add_edge("generate_redlines", "generate_strategy")
    graph.add_edge("generate_strategy", "calculate_risk")
    graph.add_edge("calculate_risk", END)

    return graph.compile()


contract_graph = build_contract_graph()


async def run_contract_analysis(contract_text: str) -> dict:
    initial_state: ContractAgentState = {
        "contract_text": contract_text,
        "contract_type": "",
        "metadata": {},
        "clauses": [],
        "analyzed_clauses": [],
        "redlines": [],
        "negotiation_strategy": {},
        "overall_risk_score": 0.0,
        "messages": [],
        "error": None,
    }

    final_state = await contract_graph.ainvoke(initial_state)
    metadata = final_state.get("metadata", {})

    return {
        "contract_type": final_state.get("contract_type", "Unknown"),
        "overall_risk_score": final_state.get("overall_risk_score", 5.0),
        "summary": metadata.get("summary", ""),
        "parties": metadata.get("parties", {}),
        "key_dates": {
            "effective_date": metadata.get("effective_date"),
            "expiry_date": metadata.get("expiry_date"),
        },
        "clauses": final_state.get("analyzed_clauses", []),
        "redlines": final_state.get("redlines", []),
        "negotiation_strategy": final_state.get("negotiation_strategy", {}),
    }
