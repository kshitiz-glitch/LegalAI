"""
Parses all raw contracts into individual clauses with full metadata.
Uses spaCy for NLP sentence boundary detection.
Hybrid classification: keyword matching (fast) + facebook/bart-large-mnli
zero-shot (accurate) for ambiguous clauses.

Input:  data/raw/lawinsider/    (8,000 contracts)
        data/raw/sec_edgar/     (5,000 contracts)
        data/raw/creative_commons/ (2,000 contracts)
Output: data/processed/clauses.json (300,000+ clauses)

Run: python data/scripts/4_parse_and_extract.py
     python data/scripts/4_parse_and_extract.py --fast   (keyword-only, no model)
Install: python -m spacy download en_core_web_sm
         pip install transformers    (for zero-shot classification)
"""
import argparse
import json
import re
import uuid
from collections import Counter
from pathlib import Path

import spacy

RAW_DIRS = [
    Path("data/raw/lawinsider"),
    Path("data/raw/sec_edgar"),
    Path("data/raw/creative_commons"),
]
OUTPUT = Path("data/processed/clauses.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

# Section header patterns
SECTION_RE = re.compile(
    r"(?:^|\n)\s*"
    r"(?:\d{1,2}\.\s+[A-Z]|[A-Z]\.\s+[A-Z]"
    r"|Section\s+\d+|SECTION\s+[A-Z]+"
    r"|Article\s+\d+|ARTICLE\s+[A-Z]+"
    r"|Schedule\s+\d+)"
    r"[.\s]",
    re.MULTILINE,
)

CLAUSE_TYPES = {
    "termination":        ["terminat", "cancel", "expir", "end this agreement"],
    "payment":            ["payment", "invoice", "fee ", "cost", "price", "compensation", "remuneration"],
    "liability":          ["liable", "liability", "damages", "loss", "indemnif", "hold harmless"],
    "confidentiality":    ["confidential", "non-disclosure", "proprietary", "trade secret"],
    "ip_ownership":       ["intellectual property", "ownership", "copyright", "patent", "trademark", "work product"],
    "warranty":           ["warrant", "guarantee", "represent", "as-is", "no warranty"],
    "indemnification":    ["indemnif", "hold harmless", "defend against", "third-party claim"],
    "dispute_resolution": ["arbitration", "dispute", "mediation", "litigation", "adr"],
    "force_majeure":      ["force majeure", "act of god", "unforeseeable", "beyond control"],
    "governing_law":      ["governing law", "jurisdiction", "courts of", "venue"],
    "assignment":         ["assign", "transfer rights", "delegate", "subcontract"],
    "amendment":          ["amend", "modify this agreement", "changes to this"],
}

# Target counts per clause type (from your plan)
CLAUSE_TARGETS = {
    "termination":        40000,
    "payment":            50000,
    "liability":          35000,
    "confidentiality":    30000,
    "ip_ownership":       25000,
    "warranty":           20000,
    "indemnification":    25000,
    "dispute_resolution": 15000,
    "force_majeure":      10000,
    "amendment":           8000,
    "assignment":         12000,
    "governing_law":      10000,
    "general":            20000,
}


def classify_clause(text: str) -> str:
    """Fast keyword-based classification (first pass)."""
    t = text.lower()
    for clause_type, keywords in CLAUSE_TYPES.items():
        if any(kw in t for kw in keywords):
            return clause_type
    return "general"


# ── Zero-shot classification (second pass for ambiguous clauses) ─────────────

ZS_LABELS = [
    "termination or cancellation",
    "payment or compensation",
    "liability or damages",
    "confidentiality or non-disclosure",
    "intellectual property ownership",
    "warranty or guarantee",
    "indemnification",
    "dispute resolution or arbitration",
    "force majeure",
    "governing law or jurisdiction",
    "assignment or transfer of rights",
    "amendment or modification",
]

ZS_TO_TYPE = {
    "termination or cancellation": "termination",
    "payment or compensation": "payment",
    "liability or damages": "liability",
    "confidentiality or non-disclosure": "confidentiality",
    "intellectual property ownership": "ip_ownership",
    "warranty or guarantee": "warranty",
    "indemnification": "indemnification",
    "dispute resolution or arbitration": "dispute_resolution",
    "force majeure": "force_majeure",
    "governing law or jurisdiction": "governing_law",
    "assignment or transfer of rights": "assignment",
    "amendment or modification": "amendment",
}

ZS_CONFIDENCE_THRESHOLD = 0.35


def reclassify_general_clauses(clauses: list[dict], batch_size: int = 16) -> int:
    """
    Reclassify clauses tagged as 'general' using facebook/bart-large-mnli
    zero-shot classification. Only overrides if confidence >= threshold.
    Returns number of clauses reclassified.
    """
    try:
        from transformers import pipeline as hf_pipeline
    except ImportError:
        print("  ⚠ transformers not installed — run: pip install transformers")
        print("  Skipping zero-shot reclassification.")
        return 0

    print("  Loading facebook/bart-large-mnli (first run downloads ~1.6 GB)…")
    classifier = hf_pipeline(
        "zero-shot-classification",
        model="facebook/bart-large-mnli",
        device=-1,  # CPU; set to 0 if you have a CUDA GPU
    )

    reclassified = 0
    total = len(clauses)

    for i in range(0, total, batch_size):
        batch = clauses[i : i + batch_size]
        texts = [c["text"][:512] for c in batch]

        results = classifier(
            texts,
            candidate_labels=ZS_LABELS,
            hypothesis_template="This legal clause is about {}.",
        )

        # Single input returns dict, batch returns list
        if isinstance(results, dict):
            results = [results]

        for clause, result in zip(batch, results):
            top_label = result["labels"][0]
            top_score = result["scores"][0]

            if top_score >= ZS_CONFIDENCE_THRESHOLD:
                new_type = ZS_TO_TYPE.get(top_label, "general")
                if new_type != "general":
                    clause["clause_type"] = new_type
                    clause["zs_confidence"] = round(top_score, 3)
                    reclassified += 1

        done = min(i + batch_size, total)
        if (i // batch_size) % 25 == 0:
            print(f"    {done:,}/{total:,} processed | {reclassified:,} reclassified")

    return reclassified


def split_to_clauses(text: str, nlp) -> list[str]:
    """Split contract text into clause-level chunks using spaCy."""
    clauses = []

    # First split by section headers
    sections = SECTION_RE.split(text)

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Use spaCy for sentence detection within section
        # Limit to 100K chars to avoid memory issues
        doc = nlp(section[:100_000])

        buffer = []
        buffer_words = 0

        for sent in doc.sents:
            sent_text = sent.text.strip()
            sent_words = len(sent_text.split())

            if sent_words < 5:
                continue

            buffer.append(sent_text)
            buffer_words += sent_words

            # Flush buffer at clause boundaries (20-150 words)
            if buffer_words >= 20:
                clause_text = " ".join(buffer)
                if 15 <= len(clause_text.split()) <= 500:
                    clauses.append(clause_text)
                buffer = []
                buffer_words = 0

        # Flush remaining
        if buffer:
            clause_text = " ".join(buffer)
            if 15 <= len(clause_text.split()) <= 500:
                clauses.append(clause_text)

    return clauses


def load_contracts() -> list[dict]:
    contracts = []
    for raw_dir in RAW_DIRS:
        if not raw_dir.exists():
            print(f"  Skipping (not found): {raw_dir}")
            continue
        files = list(raw_dir.glob("*.json"))
        print(f"  Loading {len(files)} contracts from {raw_dir.name}/")
        for f in files:
            try:
                contracts.append(json.loads(f.read_text()))
            except Exception:
                pass
    return contracts


def main():
    parser = argparse.ArgumentParser(
        description="Parse raw contracts into clause-level dataset with hybrid classification"
    )
    parser.add_argument(
        "--fast", action="store_true",
        help="Keyword-only mode — skip zero-shot model (faster, less accurate)",
    )
    args = parser.parse_args()

    print("Loading spaCy model (en_core_web_sm)…")
    try:
        nlp = spacy.load("en_core_web_sm", exclude=["ner", "attribute_ruler", "lemmatizer"])
    except OSError:
        print("Run: python -m spacy download en_core_web_sm")
        return

    # Ensure sentence boundaries are set — add sentencizer if parser/senter absent
    if not nlp.has_pipe("sentencizer") and not nlp.has_pipe("senter") and not nlp.has_pipe("parser"):
        nlp.add_pipe("sentencizer")

    print("\nLoading raw contracts…")
    contracts = load_contracts()
    print(f"Total contracts: {len(contracts)}")

    if not contracts:
        print("No raw contracts found. Run scripts 1, 2, 3 first.")
        return

    # ── Pass 1: Parse + keyword classification (fast) ──
    print("\n[Pass 1] Parsing contracts + keyword classification…")
    all_clauses = []
    type_counter: Counter = Counter()

    for i, contract in enumerate(contracts):
        if i % 500 == 0:
            print(f"  Processing {i}/{len(contracts)} | clauses so far: {len(all_clauses)}")

        text = contract.get("text", "")
        if not text:
            continue

        clause_texts = split_to_clauses(text, nlp)

        for clause_text in clause_texts:
            clause_type = classify_clause(clause_text)
            clause_id = f"clause_{uuid.uuid4().hex[:12]}"

            clause = {
                "clause_id": clause_id,
                "text": clause_text,
                "clause_type": clause_type,
                "contract_type": contract.get("contract_type", "unknown"),
                "contract_id": contract.get("contract_id", "unknown"),
                "word_count": len(clause_text.split()),
                "sentence_count": clause_text.count(".") + clause_text.count(";"),
                "source": contract.get("source", "unknown"),
                "company": contract.get("company", "Unknown"),
                "favorability": None,  # Will be labeled in script 8
            }
            all_clauses.append(clause)
            type_counter[clause_type] += 1

    general_count = type_counter.get("general", 0)
    print(f"\n  Pass 1 done: {len(all_clauses):,} clauses extracted")
    print(f"  Keyword-classified: {len(all_clauses) - general_count:,} | Uncertain ('general'): {general_count:,}")

    # ── Pass 2: Zero-shot reclassification of "general" clauses ──
    if not args.fast:
        general_clauses = [c for c in all_clauses if c["clause_type"] == "general"]
        if general_clauses:
            print(f"\n[Pass 2] Zero-shot reclassifying {len(general_clauses):,} 'general' clauses")
            print(f"         Model: facebook/bart-large-mnli")
            print(f"         Threshold: {ZS_CONFIDENCE_THRESHOLD}")
            reclassified = reclassify_general_clauses(general_clauses)
            print(f"\n  ✅ Reclassified {reclassified:,} / {len(general_clauses):,} clauses → specific types")
            print(f"     Remaining 'general': {len(general_clauses) - reclassified:,}")
            # Rebuild counter after reclassification
            type_counter = Counter(c["clause_type"] for c in all_clauses)
        else:
            print("\n[Pass 2] No 'general' clauses to reclassify — all keywords matched!")
    else:
        print("\n[--fast] Skipping zero-shot reclassification")

    # ── Save output ──
    OUTPUT.write_text(json.dumps(all_clauses, indent=2))

    print(f"\n[OK] Saved {len(all_clauses):,} clauses -> {OUTPUT}")
    print("\nFinal clause type distribution:")
    for ct, count in type_counter.most_common():
        target = CLAUSE_TARGETS.get(ct, 0)
        pct = count / target * 100 if target else 0
        bar = "█" * min(int(pct / 5), 20)
        print(f"  {ct:25s} {count:7,d} / {target:7,d}  {bar} {pct:.0f}%")


if __name__ == "__main__":
    main()
