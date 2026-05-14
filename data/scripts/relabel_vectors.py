"""
Re-label Qdrant vectors using batch set_payload (FAST version).
Uses batch point selectors instead of per-point API calls.
"""

import os, sys, time
from pathlib import Path
from collections import Counter, defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[2] / "backend" / ".env")

from qdrant_client import QdrantClient

QDRANT_URL = os.environ["QDRANT_URL"]
QDRANT_API_KEY = os.environ["QDRANT_API_KEY"]
COLLECTION = os.environ.get("QDRANT_COLLECTION", "legal_clauses")

CLAUSE_TYPES = {
    "indemnification":    ["indemnif", "hold harmless", "defend and hold", "defend against", "third-party claim", "third party claim"],
    "force_majeure":      ["force majeure", "act of god", "unforeseeable", "beyond control", "beyond reasonable control", "natural disaster"],
    "governing_law":      ["governing law", "governed by the laws", "laws of the state", "jurisdiction", "courts of", "venue", "choice of law", "laws of"],
    "termination":        ["terminat", "cancel", "expir", "end this agreement", "cease and desist"],
    "payment":            ["payment", "invoice", "fee ", "fees ", "cost", "price", "compensation", "remuneration", "payable", "paid"],
    "liability":          ["liable", "liability", "limitation of liability", "consequential damages", "indirect damages", "punitive damages"],
    "confidentiality":    ["confidential", "non-disclosure", "proprietary", "trade secret", "nda", "proprietary information"],
    "ip_ownership":       ["intellectual property", "ownership", "copyright", "patent", "trademark", "work product", "work-for-hire"],
    "warranty":           ["warrant", "guarantee", "as-is", "as is", "no warranty", "without warranty", "merchantability", "fitness for"],
    "dispute_resolution": ["arbitration", "dispute", "mediation", "litigation", "adr", "arbitrat", "american arbitration"],
    "assignment":         ["assign", "transfer rights", "delegate", "subcontract", "assignable", "not assign"],
    "amendment":          ["amend", "modify this agreement", "changes to this", "modification", "supplement"],
}

PRIORITY_ORDER = [
    "indemnification", "force_majeure", "governing_law",
    "dispute_resolution", "ip_ownership", "confidentiality",
    "warranty", "termination", "amendment", "assignment",
    "payment", "liability",
]


def classify_v2(text):
    t = text.lower()
    best_type, best_score = "general", 0
    for ct in PRIORITY_ORDER:
        score = sum(1 for kw in CLAUSE_TYPES[ct] if kw in t)
        if score > best_score:
            best_score = score
            best_type = ct
    return best_type


def main():
    print("=" * 60)
    print("  Qdrant Batch Re-labeling (FAST)")
    print("=" * 60)

    qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=120)
    info = qdrant.get_collection(COLLECTION)
    total = info.points_count
    print(f"  Collection: {COLLECTION} ({total:,} vectors)")

    # Phase 1: Scan all vectors, group IDs by new label
    print(f"\n  Phase 1: Scanning...")
    start = time.time()

    before = Counter()
    after = Counter()
    # Map: new_type -> list of point IDs that need that label
    updates = defaultdict(list)
    processed = 0
    offset = None

    while True:
        pts, offset = qdrant.scroll(
            collection_name=COLLECTION, limit=100,
            offset=offset, with_payload=True, with_vectors=False,
        )
        if not pts:
            break
        for p in pts:
            old = p.payload.get("clause_type", "general")
            new = classify_v2(p.payload.get("text", ""))
            before[old] += 1
            after[new] += 1
            if old != new:
                updates[new].append(p.id)
            processed += 1

        if processed % 10000 == 0:
            elapsed = time.time() - start
            print(f"    Scanned {processed:,}/{total:,} "
                  f"({processed/total*100:.0f}%) — {elapsed:.0f}s")

        if offset is None:
            break

    to_update = sum(len(ids) for ids in updates.values())
    print(f"\n  Scan done in {time.time()-start:.0f}s")
    print(f"  Need to relabel: {to_update:,} vectors")
    print(f"\n  BEFORE -> AFTER:")
    all_types = sorted(set(list(before.keys()) + list(after.keys())))
    for ct in all_types:
        b = before.get(ct, 0)
        a = after.get(ct, 0)
        arrow = "UP" if a > b else "DN" if a < b else "=="
        print(f"    {ct:25s} {b:>6,} -> {a:>6,}  {arrow}")

    # Phase 2: Batch update per type
    print(f"\n  Phase 2: Applying batch updates...")
    phase2_start = time.time()
    applied = 0

    for new_type, point_ids in updates.items():
        # Qdrant set_payload accepts a list of point IDs — batch!
        BATCH = 500
        for i in range(0, len(point_ids), BATCH):
            batch_ids = point_ids[i:i + BATCH]
            qdrant.set_payload(
                collection_name=COLLECTION,
                payload={"clause_type": new_type},
                points=batch_ids,
            )
            applied += len(batch_ids)

        print(f"    {new_type:25s} {len(point_ids):>6,} updated")

    print(f"\n  Phase 2 done in {time.time()-phase2_start:.0f}s")
    print(f"\n{'=' * 60}")
    print(f"  DONE — {to_update:,} vectors relabeled in {time.time()-start:.0f}s total")
    general_before = before.get("general", 0) / processed * 100
    general_after = after.get("general", 0) / processed * 100
    print(f"  'general' reduced: {general_before:.1f}% -> {general_after:.1f}%")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
