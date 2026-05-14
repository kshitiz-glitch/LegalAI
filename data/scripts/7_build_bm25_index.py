"""
Builds the BM25 keyword index from all clauses.
Saved to disk and loaded by the backend on startup for hybrid search.

Input:  data/processed/clauses.json           (real scraped clauses)
        data/processed/synthetic_clauses.json  (HuggingFace legal datasets)
Output: data/bm25_index.pkl

Run: python data/scripts/7_build_bm25_index.py
"""
import json
import pickle
from pathlib import Path

from rank_bm25 import BM25Okapi

CLAUSE_FILES = [
    Path("data/processed/clauses.json"),
    Path("data/processed/synthetic_clauses.json"),
]
OUTPUT = Path("data/bm25_index.pkl")


def main():
    all_clauses = []
    for f in CLAUSE_FILES:
        if not f.exists():
            print(f"  Skipping (not found): {f}")
            continue
        data = json.loads(f.read_text())
        all_clauses.extend(data)
        print(f"  Loaded {len(data):,} clauses from {f.name}")

    if not all_clauses:
        print("No clauses found. Run scripts 4 and 5 first.")
        return

    print(f"\nTotal clauses: {len(all_clauses):,}")
    print("Building BM25 index (this takes a few minutes)…")

    corpus = [c["text"] for c in all_clauses]
    tokenized = [doc.lower().split() for doc in corpus]
    index = BM25Okapi(tokenized)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "wb") as f:
        pickle.dump({"index": index, "corpus": corpus, "payloads": all_clauses}, f)

    size_mb = OUTPUT.stat().st_size / (1024 * 1024)
    print(f"\n✅ BM25 index saved: {OUTPUT} ({size_mb:.1f} MB)")
    print(f"   Set BM25_INDEX_PATH=./data/bm25_index.pkl in backend/.env")


if __name__ == "__main__":
    main()
