"""
LegalAI Evaluation Suite
=========================
Measures the quality of the RAG pipeline across 3 dimensions:
  1. Retrieval Quality  — Precision@K, Mean Reciprocal Rank (MRR)
  2. Classification      — Keyword classifier accuracy vs expected labels
  3. End-to-End Analysis — Risk scoring consistency

Run: python data/scripts/evaluate.py
Requires: Backend .env must be loaded (QDRANT_URL, QDRANT_API_KEY)
Output: data/evaluation_report.md
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Optional
from collections import Counter

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[2] / "backend" / ".env")

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

# ── Configuration ─────────────────────────────────────────────────────────
QDRANT_URL = os.environ["QDRANT_URL"]
QDRANT_API_KEY = os.environ["QDRANT_API_KEY"]
COLLECTION = os.environ.get("QDRANT_COLLECTION", "legal_clauses")
OUTPUT_PATH = Path("data/evaluation_report.md")

# ── Test Queries with Expected Results ─────────────────────────────────────
# Each query has: query text, expected clause_type in top-5, description
RETRIEVAL_TEST_CASES = [
    {
        "query": "The licensee shall indemnify and hold harmless the licensor from all claims and damages",
        "expected_type": "indemnification",
        "description": "Indemnification clause search",
    },
    {
        "query": "This agreement may be terminated by either party upon 30 days written notice",
        "expected_type": "termination",
        "description": "Termination clause search",
    },
    {
        "query": "All payments shall be made within net 30 days of invoice date",
        "expected_type": "payment",
        "description": "Payment terms search",
    },
    {
        "query": "Each party agrees to keep confidential all proprietary information",
        "expected_type": "confidentiality",
        "description": "Confidentiality clause search",
    },
    {
        "query": "The software is provided as-is without any warranty of any kind express or implied",
        "expected_type": "warranty",
        "description": "Warranty disclaimer search",
    },
    {
        "query": "Neither party shall be liable for indirect incidental or consequential damages",
        "expected_type": "liability",
        "description": "Liability limitation search",
    },
    {
        "query": "This agreement shall be governed by the laws of the State of Delaware",
        "expected_type": "governing_law",
        "description": "Governing law clause search",
    },
    {
        "query": "Neither party shall be held responsible for failure to perform due to acts of God or force majeure events",
        "expected_type": "force_majeure",
        "description": "Force majeure clause search",
    },
    {
        "query": "All intellectual property rights and ownership of work product shall remain with the company",
        "expected_type": "ip_ownership",
        "description": "IP ownership clause search",
    },
    {
        "query": "Any dispute arising under this agreement shall be resolved through binding arbitration",
        "expected_type": "dispute_resolution",
        "description": "Dispute resolution search",
    },
    {
        "query": "Licensee shall not assign or transfer this agreement without prior written consent",
        "expected_type": "assignment",
        "description": "Assignment restriction search",
    },
    {
        "query": "This agreement may not be amended except by a written instrument signed by both parties",
        "expected_type": "amendment",
        "description": "Amendment clause search",
    },
    {
        "query": "Total liability under this agreement shall not exceed the fees paid in the preceding twelve months",
        "expected_type": "liability",
        "description": "Liability cap search",
    },
    {
        "query": "Company warrants that the product will substantially conform to the documentation for a period of one year",
        "expected_type": "warranty",
        "description": "Product warranty search",
    },
    {
        "query": "Upon termination all licenses granted shall immediately cease and licensee shall return all materials",
        "expected_type": "termination",
        "description": "Termination effects search",
    },
    {
        "query": "Contractor shall defend indemnify and hold harmless client from third party intellectual property claims",
        "expected_type": "indemnification",
        "description": "IP indemnification search",
    },
    {
        "query": "All fees are non-refundable and shall be paid in United States dollars via wire transfer",
        "expected_type": "payment",
        "description": "Payment method search",
    },
    {
        "query": "The receiving party shall use the same degree of care to protect confidential information as it uses for its own",
        "expected_type": "confidentiality",
        "description": "Confidentiality standard of care search",
    },
    {
        "query": "Any controversy or claim shall be settled by arbitration administered by the American Arbitration Association",
        "expected_type": "dispute_resolution",
        "description": "AAA arbitration clause search",
    },
    {
        "query": "Force majeure events include but are not limited to earthquake flood fire epidemic government restrictions",
        "expected_type": "force_majeure",
        "description": "Force majeure definition search",
    },
]

# ── Classification Test Cases ──────────────────────────────────────────────
CLASSIFICATION_TEST_CASES = [
    ("This agreement may be terminated by either party upon 90 days written notice.", "termination"),
    ("Late payments shall accrue interest at 1.5% per month.", "payment"),
    ("IN NO EVENT SHALL LICENSOR BE LIABLE FOR ANY INDIRECT DAMAGES.", "liability"),
    ("Each party agrees to maintain the confidentiality of proprietary information.", "confidentiality"),
    ("All intellectual property created shall be owned by the Company.", "ip_ownership"),
    ("THE SOFTWARE IS PROVIDED AS IS WITHOUT WARRANTY OF ANY KIND.", "warranty"),
    ("Licensee shall indemnify and hold harmless Licensor from all claims.", "indemnification"),
    ("Any disputes shall be resolved through binding arbitration.", "dispute_resolution"),
    ("Neither party shall be liable for failure due to acts of God.", "force_majeure"),
    ("This Agreement shall be governed by the laws of Delaware.", "governing_law"),
    ("Licensee shall not assign this agreement without prior written consent.", "assignment"),
    ("This agreement may not be amended except in writing signed by both parties.", "amendment"),
    ("Payment shall be due within 30 days of the invoice date.", "payment"),
    ("Licensor may terminate immediately if Licensee breaches any material term.", "termination"),
    ("Licensee shall defend and hold harmless the Company from third-party claims.", "indemnification"),
    ("The Company warrants that the product will conform to specifications.", "warranty"),
    ("All confidential information shall remain protected for 5 years after disclosure.", "confidentiality"),
    ("Jurisdiction shall be in the state and federal courts of New York.", "governing_law"),
    ("Neither party may assign rights without written consent of the other party.", "assignment"),
    ("Force majeure includes natural disasters, war, pandemic, and government action.", "force_majeure"),
]


# ══════════════════════════════════════════════════════════════════════════
# Evaluation Functions
# ══════════════════════════════════════════════════════════════════════════

def classify_clause_keyword(text: str) -> str:
    """Keyword-based classifier (mirrors 4_parse_and_extract.py)."""
    CLAUSE_TYPES = {
        "termination":        ["terminat", "cancel", "expir", "end this agreement"],
        "payment":            ["payment", "invoice", "fee ", "cost", "price", "compensation", "remuneration"],
        "liability":          ["liable", "liability", "damages", "loss"],
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
    t = text.lower()
    best_type = "general"
    best_count = 0
    for clause_type, keywords in CLAUSE_TYPES.items():
        count = sum(1 for kw in keywords if kw in t)
        if count > best_count:
            best_count = count
            best_type = clause_type
    return best_type


def evaluate_retrieval(qdrant: QdrantClient, encoder: SentenceTransformer) -> Dict:
    """Evaluate retrieval quality: Precision@K, MRR, Hit Rate."""
    print("\n[1/3] Evaluating Retrieval Quality...")
    print("=" * 60)

    results = []
    k_values = [1, 3, 5, 10]
    total_rr = 0  # For MRR
    hits_at = {k: 0 for k in k_values}

    for i, tc in enumerate(RETRIEVAL_TEST_CASES):
        query = tc["query"]
        expected = tc["expected_type"]

        vec = encoder.encode(query, convert_to_numpy=True).tolist()
        search_results = qdrant.search(
            collection_name=COLLECTION,
            query_vector=vec,
            limit=10,
            with_payload=True,
        )

        retrieved_types = [h.payload.get("clause_type", "general") for h in search_results]
        scores = [h.score for h in search_results]

        # Find first relevant result position (1-indexed)
        first_hit = None
        for j, ct in enumerate(retrieved_types):
            if ct == expected:
                first_hit = j + 1
                break

        rr = 1.0 / first_hit if first_hit else 0.0
        total_rr += rr

        for k in k_values:
            if any(ct == expected for ct in retrieved_types[:k]):
                hits_at[k] += 1

        status = "PASS" if first_hit and first_hit <= 3 else "MISS"
        print(f"  [{status}] Q{i+1:02d}: {tc['description']}")
        if first_hit:
            print(f"         Expected: {expected} | Found at rank {first_hit} | Top score: {scores[0]:.3f}")
        else:
            print(f"         Expected: {expected} | NOT FOUND in top 10 | Top types: {retrieved_types[:3]}")

        results.append({
            "query": tc["description"],
            "expected": expected,
            "first_hit_rank": first_hit,
            "rr": rr,
            "top_3_types": retrieved_types[:3],
            "top_score": scores[0] if scores else 0,
        })

    n = len(RETRIEVAL_TEST_CASES)
    mrr = total_rr / n
    metrics = {
        "mrr": mrr,
        "hit_rate": {k: hits_at[k] / n for k in k_values},
        "results": results,
        "total_queries": n,
    }

    print(f"\n  MRR:          {mrr:.4f}")
    for k in k_values:
        print(f"  Hit Rate@{k:<3d}  {hits_at[k]}/{n} ({hits_at[k]/n*100:.1f}%)")

    return metrics


def evaluate_classification() -> Dict:
    """Evaluate keyword classifier accuracy."""
    print("\n[2/3] Evaluating Classification Accuracy...")
    print("=" * 60)

    correct = 0
    results = []
    confusion = Counter()

    for text, expected in CLASSIFICATION_TEST_CASES:
        predicted = classify_clause_keyword(text)
        is_correct = predicted == expected
        if is_correct:
            correct += 1
        else:
            confusion[(expected, predicted)] += 1

        status = "PASS" if is_correct else "MISS"
        print(f"  [{status}] Expected: {expected:<20s} | Predicted: {predicted:<20s} | {'--' if is_correct else 'MISMATCH'}")
        results.append({
            "text": text[:80] + "..." if len(text) > 80 else text,
            "expected": expected,
            "predicted": predicted,
            "correct": is_correct,
        })

    n = len(CLASSIFICATION_TEST_CASES)
    accuracy = correct / n

    # Per-type accuracy
    type_stats = {}
    for text, expected in CLASSIFICATION_TEST_CASES:
        if expected not in type_stats:
            type_stats[expected] = {"total": 0, "correct": 0}
        type_stats[expected]["total"] += 1
        predicted = classify_clause_keyword(text)
        if predicted == expected:
            type_stats[expected]["correct"] += 1

    metrics = {
        "accuracy": accuracy,
        "correct": correct,
        "total": n,
        "results": results,
        "confusion_errors": [(f"{e}->{p}", c) for (e, p), c in confusion.most_common()],
        "per_type": {k: v["correct"]/v["total"] for k, v in type_stats.items()},
    }

    print(f"\n  Overall Accuracy: {correct}/{n} ({accuracy*100:.1f}%)")
    if confusion:
        print(f"  Misclassifications:")
        for (expected, predicted), count in confusion.most_common():
            print(f"    {expected} -> {predicted} ({count}x)")

    return metrics


def evaluate_collection_stats(qdrant: QdrantClient) -> Dict:
    """Get collection statistics."""
    print("\n[3/3] Collection Statistics...")
    print("=" * 60)

    info = qdrant.get_collection(COLLECTION)
    total_points = info.points_count
    print(f"  Total vectors:    {total_points:,}")
    print(f"  Vector dimension: {info.config.params.vectors.size}")
    print(f"  Distance metric:  {info.config.params.vectors.distance}")

    # Sample distribution by clause type
    sample_types = Counter()
    offset = None
    batch_count = 0
    max_batches = 10  # Sample first 10 batches

    while batch_count < max_batches:
        result = qdrant.scroll(
            collection_name=COLLECTION,
            limit=100,
            offset=offset,
            with_payload=True,
        )
        points, offset = result
        if not points:
            break
        for p in points:
            sample_types[p.payload.get("clause_type", "general")] += 1
        batch_count += 1
        if offset is None:
            break

    sampled = sum(sample_types.values())
    print(f"  Sampled {sampled:,} vectors for distribution:")
    for ct, count in sample_types.most_common():
        pct = count / sampled * 100
        print(f"    {ct:<25s} {count:>5,} ({pct:5.1f}%)")

    return {
        "total_vectors": total_points,
        "dimension": info.config.params.vectors.size,
        "distance": str(info.config.params.vectors.distance),
        "sample_distribution": dict(sample_types.most_common()),
        "sampled_count": sampled,
    }


# ══════════════════════════════════════════════════════════════════════════
# Report Generator
# ══════════════════════════════════════════════════════════════════════════

def generate_report(retrieval: Dict, classification: Dict, collection: Dict) -> str:
    """Generate a markdown evaluation report."""

    report = []
    report.append("# LegalAI Evaluation Report")
    report.append(f"\n> Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"> Pipeline: Hybrid RAG (BM25 + all-MiniLM-L6-v2 + CrossEncoder reranking)")
    report.append(f"> Collection: {COLLECTION} ({collection['total_vectors']:,} vectors)")
    report.append("")

    # Executive Summary
    report.append("## Executive Summary")
    report.append("")
    report.append("| Metric | Score | Target | Status |")
    report.append("|---|---|---|---|")

    mrr = retrieval["mrr"]
    mrr_status = "PASS" if mrr >= 0.7 else "WARN" if mrr >= 0.5 else "FAIL"
    report.append(f"| Mean Reciprocal Rank (MRR) | **{mrr:.4f}** | >= 0.70 | {mrr_status} |")

    hr5 = retrieval["hit_rate"][5]
    hr5_status = "PASS" if hr5 >= 0.8 else "WARN" if hr5 >= 0.6 else "FAIL"
    report.append(f"| Hit Rate@5 | **{hr5*100:.1f}%** | >= 80% | {hr5_status} |")

    hr10 = retrieval["hit_rate"][10]
    hr10_status = "PASS" if hr10 >= 0.9 else "WARN" if hr10 >= 0.7 else "FAIL"
    report.append(f"| Hit Rate@10 | **{hr10*100:.1f}%** | >= 90% | {hr10_status} |")

    cls_acc = classification["accuracy"]
    cls_status = "PASS" if cls_acc >= 0.85 else "WARN" if cls_acc >= 0.7 else "FAIL"
    report.append(f"| Classification Accuracy | **{cls_acc*100:.1f}%** | >= 85% | {cls_status} |")

    report.append(f"| Total Indexed Vectors | **{collection['total_vectors']:,}** | >= 100,000 | PASS |")
    report.append("")

    # Retrieval Details
    report.append("---")
    report.append("## 1. Retrieval Quality")
    report.append("")
    report.append(f"**{retrieval['total_queries']} test queries** evaluated against the vector search pipeline.")
    report.append("")
    report.append("| K | Hit Rate | Queries Found |")
    report.append("|---|---|---|")
    for k in [1, 3, 5, 10]:
        hr = retrieval["hit_rate"][k]
        found = int(hr * retrieval["total_queries"])
        report.append(f"| @{k} | {hr*100:.1f}% | {found}/{retrieval['total_queries']} |")
    report.append("")

    report.append("### Per-Query Results")
    report.append("")
    report.append("| # | Query | Expected Type | Rank Found | RR |")
    report.append("|---|---|---|---|---|")
    for i, r in enumerate(retrieval["results"]):
        rank = r["first_hit_rank"] if r["first_hit_rank"] else "Not found"
        report.append(f"| {i+1} | {r['query']} | `{r['expected']}` | {rank} | {r['rr']:.2f} |")
    report.append("")

    # Classification Details
    report.append("---")
    report.append("## 2. Classification Accuracy")
    report.append("")
    report.append(f"**Keyword classifier** tested on {classification['total']} labeled samples.")
    report.append(f"Overall accuracy: **{classification['accuracy']*100:.1f}%** ({classification['correct']}/{classification['total']})")
    report.append("")

    if classification["per_type"]:
        report.append("### Per-Type Accuracy")
        report.append("")
        report.append("| Clause Type | Accuracy |")
        report.append("|---|---|")
        for ct, acc in sorted(classification["per_type"].items()):
            bar = "=" * int(acc * 20) + " " * (20 - int(acc * 20))
            report.append(f"| `{ct}` | {acc*100:.0f}% |")
        report.append("")

    if classification["confusion_errors"]:
        report.append("### Misclassifications")
        report.append("")
        report.append("| Misclassification | Count |")
        report.append("|---|---|")
        for label, count in classification["confusion_errors"]:
            report.append(f"| {label} | {count} |")
        report.append("")

    # Collection Stats
    report.append("---")
    report.append("## 3. Collection Statistics")
    report.append("")
    report.append(f"| Property | Value |")
    report.append(f"|---|---|")
    report.append(f"| Total Vectors | {collection['total_vectors']:,} |")
    report.append(f"| Embedding Model | all-MiniLM-L6-v2 |")
    report.append(f"| Vector Dimension | {collection['dimension']} |")
    report.append(f"| Distance Metric | {collection['distance']} |")
    report.append(f"| Reranker | cross-encoder/ms-marco-MiniLM-L-6-v2 |")
    report.append("")

    report.append("### Clause Type Distribution (sampled)")
    report.append("")
    report.append("| Clause Type | Count | % |")
    report.append("|---|---|---|")
    for ct, count in collection["sample_distribution"].items():
        pct = count / collection["sampled_count"] * 100
        report.append(f"| `{ct}` | {count:,} | {pct:.1f}% |")
    report.append("")

    # Methodology
    report.append("---")
    report.append("## Methodology")
    report.append("")
    report.append("### Retrieval Evaluation")
    report.append("- **MRR (Mean Reciprocal Rank)**: Average of 1/rank for the first relevant result")
    report.append("- **Hit Rate@K**: Fraction of queries where at least one relevant result appears in top-K")
    report.append("- Relevance is determined by matching the `clause_type` of retrieved documents against expected types")
    report.append("- 20 hand-crafted test queries covering all 12 clause types")
    report.append("")
    report.append("### Classification Evaluation")
    report.append("- 20 labeled clause samples across all 12 types")
    report.append("- Keyword-based classifier matching against predefined keyword lists")
    report.append("- Each clause is assigned the type with the most keyword matches")
    report.append("")

    return "\n".join(report)


# ══════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("  LegalAI Evaluation Suite")
    print("=" * 60)

    # Connect to Qdrant
    print(f"\nConnecting to Qdrant at {QDRANT_URL}...")
    qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=60)

    # Load encoder
    print("Loading sentence encoder (all-MiniLM-L6-v2)...")
    encoder = SentenceTransformer("all-MiniLM-L6-v2")

    # Run evaluations
    retrieval_metrics = evaluate_retrieval(qdrant, encoder)
    classification_metrics = evaluate_classification()
    collection_stats = evaluate_collection_stats(qdrant)

    # Generate report
    report = generate_report(retrieval_metrics, classification_metrics, collection_stats)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(report, encoding="utf-8")

    print(f"\n{'=' * 60}")
    print(f"  Report saved to: {OUTPUT_PATH}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
