import json
import asyncio
import logging
from typing import Any, Dict, Optional
import groq as _groq_lib
from groq import AsyncGroq
from app.core.config import settings

logger = logging.getLogger(__name__)

_groq_client: Optional[AsyncGroq] = None


def get_groq() -> AsyncGroq:
    global _groq_client
    if _groq_client is None:
        _groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    return _groq_client


async def llm_call(prompt: str, max_tokens: int = 2000, temperature: float = 0.1) -> str:
    client = get_groq()
    last_exc: Exception = RuntimeError("No attempts made")
    for attempt in range(5):
        try:
            response = await client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except _groq_lib.RateLimitError as e:
            wait = min(30 * (attempt + 1), 120)
            logger.warning(
                "⚠️  Groq rate limit hit (attempt %d/5). Waiting %ds before retry. "
                "Consider switching API key. Error: %s",
                attempt + 1, wait, e,
            )
            last_exc = e
            if attempt < 4:
                await asyncio.sleep(wait)
        except (_groq_lib.APIConnectionError, _groq_lib.APITimeoutError) as e:
            wait = 5 * (2 ** attempt)
            logger.warning("Groq connection error (attempt %d/5). Retrying in %ds. Error: %s", attempt + 1, wait, e)
            last_exc = e
            if attempt < 4:
                await asyncio.sleep(wait)
    raise last_exc


def parse_json(text: str, fallback: Any) -> Any:
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        try:
            start = text.find(start_char)
            end = text.rfind(end_char) + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
        except (json.JSONDecodeError, ValueError):
            continue
    return fallback


async def call_extract_metadata(contract_text: str) -> Dict[str, Any]:
    prompt = f"""Analyze this contract and extract metadata. Return ONLY valid JSON, no other text.

Contract (first 3000 chars):
{contract_text[:3000]}

Return this exact JSON structure:
{{
  "contract_type": "NDA|Employment|Service|SaaS|Consulting|Lease|Partnership|Other",
  "parties": {{"party_a": "name or null", "party_b": "name or null"}},
  "effective_date": "date string or null",
  "expiry_date": "date string or null",
  "contract_value": "amount string or null",
  "governing_law": "jurisdiction or null",
  "summary": "2-3 sentence plain English summary of what this contract is about"
}}"""

    result = await llm_call(prompt, max_tokens=600)
    return parse_json(result, {
        "contract_type": "Unknown",
        "parties": {"party_a": None, "party_b": None},
        "effective_date": None,
        "expiry_date": None,
        "contract_value": None,
        "governing_law": None,
        "summary": "Contract summary unavailable.",
    })


async def call_extract_clauses(contract_text: str) -> list:
    prompt = f"""Extract the 8-15 most legally important clauses from this contract.
Return ONLY a valid JSON array, no other text.

Contract:
{contract_text[:6000]}

Return a JSON array where each object has:
{{
  "text": "exact clause text from the contract",
  "clause_type": "one of: termination|payment|liability|confidentiality|ip_ownership|warranty|indemnification|dispute_resolution|force_majeure|governing_law|assignment|amendment|general"
}}"""

    result = await llm_call(prompt, max_tokens=2500)
    clauses = parse_json(result, [])
    return clauses if isinstance(clauses, list) else []


async def call_assess_risk(clause: Dict[str, Any], contract_type: str, similar_clauses: list) -> Dict[str, Any]:
    context = "\n".join([f"- {s['text'][:200]}" for s in similar_clauses]) if similar_clauses else "No comparable clauses found."

    prompt = f"""You are a contract risk analyst. Assess the risk of this clause.

Clause Type: {clause.get('clause_type', 'general')}
Contract Type: {contract_type}

Clause Text:
"{clause['text']}"

Similar clauses from real contracts (market comparison):
{context}

Return ONLY valid JSON:
{{
  "risk_score": <integer 1-10, where 1=very favorable, 10=very unfavorable>,
  "risk_level": "<Low|Medium|High|Critical>",
  "issues": ["specific legal issue 1", "specific legal issue 2"],
  "explanation": "1-2 sentence plain English explanation of the risk"
}}"""

    result = await llm_call(prompt, max_tokens=400)
    return parse_json(result, {
        "risk_score": 5,
        "risk_level": "Medium",
        "issues": ["Manual review recommended"],
        "explanation": "Risk assessment could not be completed automatically.",
    })


async def call_generate_redline(clause: Dict[str, Any], contract_type: str) -> Optional[Dict[str, Any]]:
    prompt = f"""Rewrite this {clause.get('clause_type', '')} clause to be more balanced and protective.

Contract Type: {contract_type}
Original Clause: "{clause['text']}"
Issues to fix: {', '.join(clause.get('issues', []))}

Return ONLY valid JSON:
{{
  "original": "original clause text",
  "rewritten": "improved clause with proper legal language",
  "changes": ["specific change made 1", "specific change made 2"],
  "rationale": "why these changes protect your interests"
}}"""

    result = await llm_call(prompt, max_tokens=700, temperature=0.3)
    return parse_json(result, None)


async def call_generate_strategy(analyzed_clauses: list, contract_type: str) -> Dict[str, Any]:
    high_risk = [c for c in analyzed_clauses if c.get("risk_score", 0) >= 7]
    medium_risk = [c for c in analyzed_clauses if 4 <= c.get("risk_score", 0) < 7]

    high_summary = "\n".join(
        [f"- [{c['clause_type']}] Score {c['risk_score']}/10: {c['text'][:120]}..." for c in high_risk[:5]]
    )

    prompt = f"""Create a negotiation strategy for this {contract_type} contract.

High Risk Clauses ({len(high_risk)} total):
{high_summary if high_summary else 'None identified'}

Medium Risk Count: {len(medium_risk)}

Return ONLY valid JSON:
{{
  "priority_issues": ["must-negotiate item with specific action"],
  "negotiable_points": ["nice-to-have change"],
  "deal_breakers": ["clause that should prevent signing if unchanged"],
  "compromise_positions": {{"clause_type": "acceptable compromise position"}},
  "talking_points": ["specific talking point for negotiation meeting"],
  "email_opener": "professional paragraph to open negotiation email"
}}"""

    result = await llm_call(prompt, max_tokens=1000, temperature=0.4)
    return parse_json(result, {
        "priority_issues": [],
        "negotiable_points": [],
        "deal_breakers": [],
        "compromise_positions": {},
        "talking_points": [],
        "email_opener": "",
    })
