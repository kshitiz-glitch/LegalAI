"""
Dataset 3 (HuggingFace edition): Download real legal clause datasets.
Uses lex_glue — the standard legal NLP benchmark maintained by HuggingFace.
Includes LEDGAR (100K provisions) + ContractNLI (17K NDA clauses) + UNFAIR-ToS.

Output: data/processed/synthetic_clauses.json
Run: python data/scripts/5_generate_synthetic.py
"""
import json
import uuid
from collections import Counter
from pathlib import Path

from datasets import load_dataset

OUTPUT = Path("data/processed/synthetic_clauses.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)


# ── Clause type mapping ──────────────────────────────────────────────────────

LEDGAR_LABEL_MAP = {
    "agreements": "general",
    "amendments": "amendment",
    "anti-assignment": "assignment",
    "arbitration": "dispute_resolution",
    "assignments": "assignment",
    "audits": "general",
    "authorizations": "general",
    "bankruptcy": "general",
    "cap on liability": "liability",
    "change of control": "assignment",
    "choice of law": "governing_law",
    "confidentiality": "confidentiality",
    "consent": "general",
    "covenant not to sue": "general",
    "data and privacy policies": "confidentiality",
    "definitions": "general",
    "dispute resolution": "dispute_resolution",
    "entire agreements": "general",
    "exclusivity": "general",
    "expiration": "termination",
    "force majeure": "force_majeure",
    "general": "general",
    "governing law": "governing_law",
    "indemnification": "indemnification",
    "insurance": "warranty",
    "intellectual property": "ip_ownership",
    "ip ownership": "ip_ownership",
    "joint ip ownership": "ip_ownership",
    "license grant": "ip_ownership",
    "limitations on liability": "liability",
    "liquidated damages": "liability",
    "minimum commitment": "payment",
    "most favored nation": "payment",
    "no-solicit": "confidentiality",
    "non-compete": "confidentiality",
    "non-disparagement": "confidentiality",
    "notices": "general",
    "payment": "payment",
    "payments": "payment",
    "price restrictions": "payment",
    "remedies": "liability",
    "representations": "warranty",
    "representations and warranties": "warranty",
    "revenue/profit sharing": "payment",
    "severability": "general",
    "survival": "general",
    "taxes": "payment",
    "termination": "termination",
    "terminations": "termination",
    "uncapped liability": "liability",
    "warranties": "warranty",
    "warranties and representations": "warranty",
    "waiver": "general",
}


def map_ledgar_label(label_name: str) -> str:
    return LEDGAR_LABEL_MAP.get(label_name.lower().strip(), "general")


def make_record(text: str, clause_type: str, contract_type: str, source: str) -> dict:
    text = text.strip()
    return {
        "clause_id": f"hf_{uuid.uuid4().hex[:12]}",
        "text": text,
        "clause_type": clause_type,
        "contract_type": contract_type,
        "contract_id": source,
        "word_count": len(text.split()),
        "sentence_count": text.count(".") + text.count(";"),
        "source": source,
        "company": "Unknown",
        "favorability": None,
        "generation_type": "real_hf",
    }


# ── Source 1: LEDGAR via lex_glue ────────────────────────────────────────────

def load_ledgar() -> list[dict]:
    print("\n[1/3] Downloading LEDGAR via lex_glue (~100K SEC provisions)…")
    try:
        splits = ["train", "validation", "test"]
        records = []
        label_names = None

        for split in splits:
            ds = load_dataset("lex_glue", "ledgar", split=split)
            if label_names is None:
                label_names = ds.features["label"].names
            for row in ds:
                text = row.get("text", "").strip()
                if not text or len(text.split()) < 8:
                    continue
                label_name = label_names[row["label"]] if label_names else "general"
                clause_type = map_ledgar_label(label_name)
                records.append(make_record(text, clause_type, "SEC_filing", "ledgar"))

        print(f"  LEDGAR: {len(records):,} clauses loaded")
        return records
    except Exception as e:
        print(f"  LEDGAR failed: {e}")
        return []


# ── Source 2: ContractNLI via lex_glue ──────────────────────────────────────

def load_contract_nli() -> list[dict]:
    print("\n[2/3] Downloading ContractNLI via lex_glue (~17K NDA clauses)…")
    try:
        splits = ["train", "validation", "test"]
        records = []
        seen: set[str] = set()

        for split in splits:
            ds = load_dataset("lex_glue", "contract_nli", split=split)
            for row in ds:
                # premise = the actual NDA clause text
                text = row.get("premise", "").strip()
                if not text or len(text.split()) < 8:
                    continue
                key = text[:80]
                if key in seen:
                    continue
                seen.add(key)
                records.append(make_record(text, "confidentiality", "NDA", "contract_nli"))

        print(f"  ContractNLI: {len(records):,} clauses loaded")
        return records
    except Exception as e:
        print(f"  ContractNLI failed: {e}")
        return []


# ── Source 3: UNFAIR-ToS via lex_glue ───────────────────────────────────────

UNFAIR_LABEL_MAP = {
    0: "general",          # A (arbitration)
    1: "general",          # CH (unilateral change)
    2: "liability",        # CR (content removal)
    3: "termination",      # J (jurisdiction)
    4: "liability",        # LAW (choice of law)
    5: "liability",        # LTD (limitation of liability)
    6: "general",          # TER (unilateral termination)
    7: "general",          # USE (contract by use)
}

def load_unfair_tos() -> list[dict]:
    print("\n[3/3] Downloading UNFAIR-ToS via lex_glue (ToS clauses)…")
    try:
        splits = ["train", "validation", "test"]
        records = []

        for split in splits:
            ds = load_dataset("lex_glue", "unfair_tos", split=split)
            for row in ds:
                text = row.get("text", "").strip()
                labels = row.get("labels", [])
                if not text or len(text.split()) < 8:
                    continue
                clause_type = UNFAIR_LABEL_MAP.get(labels[0], "general") if labels else "general"
                records.append(make_record(text, clause_type, "Terms_of_Service", "unfair_tos"))

        print(f"  UNFAIR-ToS: {len(records):,} clauses loaded")
        return records
    except Exception as e:
        print(f"  UNFAIR-ToS failed: {e}")
        return []


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  LegalAI — HuggingFace Legal Dataset Downloader")
    print("  lex_glue: LEDGAR + ContractNLI + UNFAIR-ToS")
    print("=" * 60)

    all_clauses: list[dict] = []
    all_clauses.extend(load_ledgar())
    all_clauses.extend(load_contract_nli())
    all_clauses.extend(load_unfair_tos())

    if not all_clauses:
        print("\n❌ No clauses downloaded. Check your internet connection.")
        return

    # Deduplicate by text prefix
    seen: set[str] = set()
    deduped = []
    for c in all_clauses:
        key = c["text"][:100]
        if key not in seen:
            seen.add(key)
            deduped.append(c)

    print(f"\nTotal unique clauses: {len(deduped):,}")

    dist = Counter(c["clause_type"] for c in deduped)
    print("\nClause type distribution:")
    for ct, count in sorted(dist.items(), key=lambda x: -x[1]):
        bar = "█" * (count // 1000)
        print(f"  {ct:<25} {count:>6,}  {bar}")

    OUTPUT.write_text(json.dumps(deduped, indent=2))
    print(f"\n✅ Saved {len(deduped):,} clauses → {OUTPUT}")
    print("   Run steps 6 and 7 next to index into Qdrant + BM25.")


if __name__ == "__main__":
    main()
