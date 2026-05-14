"""
Embeds all clauses and indexes into Qdrant Cloud.
Total: ~105K clauses (32K real SEC/CC + 72K from LEDGAR/UNFAIR-ToS)

Input:  data/processed/clauses.json           (real scraped clauses)
        data/processed/synthetic_clauses.json  (HuggingFace legal datasets)
Output: Qdrant Cloud collection 'legal_clauses'

Run: python data/scripts/6_embed_and_index.py
"""
import json
import os
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

load_dotenv("backend/.env")

QDRANT_URL = os.environ["QDRANT_URL"]
QDRANT_API_KEY = os.environ["QDRANT_API_KEY"]
COLLECTION = os.environ.get("QDRANT_COLLECTION", "legal_clauses")

CLAUSE_FILES = [
    Path("data/processed/clauses.json"),
    Path("data/processed/synthetic_clauses.json"),
]

BATCH_SIZE = 64  # Smaller batches to avoid Qdrant Cloud timeouts
CHECKPOINT_FILE = Path("data/processed/index_checkpoint.json")


def load_all_clauses() -> list[dict]:
    all_clauses = []
    for f in CLAUSE_FILES:
        if not f.exists():
            print(f"  Not found (skipping): {f}")
            continue
        data = json.loads(f.read_text())
        print(f"  Loaded {len(data):,} clauses from {f.name}")
        all_clauses.extend(data)
    return all_clauses


def load_checkpoint() -> set[str]:
    """Returns set of already-indexed clause_ids."""
    if CHECKPOINT_FILE.exists():
        return set(json.loads(CHECKPOINT_FILE.read_text()))
    return set()


def save_checkpoint(indexed_ids: set[str]) -> None:
    CHECKPOINT_FILE.write_text(json.dumps(list(indexed_ids)))


def main():
    clauses = load_all_clauses()
    if not clauses:
        print("No clauses found. Run scripts 4 and 5 first.")
        sys.exit(1)

    print(f"\nTotal clauses to index: {len(clauses):,}")

    already_indexed = load_checkpoint()
    remaining = [c for c in clauses if c.get("clause_id") not in already_indexed]
    print(f"Already indexed: {len(already_indexed):,}")
    print(f"Remaining: {len(remaining):,}")

    if not remaining:
        print("✅ All clauses already indexed!")
        return

    print("\nLoading embedding model (all-MiniLM-L6-v2)…")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    print("Connecting to Qdrant Cloud…")
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=120)

    existing_collections = [c.name for c in client.get_collections().collections]
    if COLLECTION not in existing_collections:
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )
        print(f"Created collection: {COLLECTION}")

    total_indexed = len(already_indexed)
    indexed_ids = set(already_indexed)

    for i in range(0, len(remaining), BATCH_SIZE):
        batch = remaining[i:i + BATCH_SIZE]
        texts = [c["text"] for c in batch]

        vectors = model.encode(
            texts,
            batch_size=64,
            show_progress_bar=False,
            convert_to_numpy=True,
        )

        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vectors[j].tolist(),
                payload={
                    "clause_id": batch[j].get("clause_id", ""),
                    "text": batch[j]["text"],
                    "clause_type": batch[j].get("clause_type", "general"),
                    "contract_type": batch[j].get("contract_type", "unknown"),
                    "source": batch[j].get("source", "unknown"),
                    "favorability": batch[j].get("favorability"),
                    "word_count": batch[j].get("word_count", 0),
                },
            )
            for j in range(len(batch))
        ]

        client.upsert(collection_name=COLLECTION, points=points)
        total_indexed += len(points)
        indexed_ids.update(c.get("clause_id", "") for c in batch)

        if (i // BATCH_SIZE) % 10 == 0:
            save_checkpoint(indexed_ids)
            info = client.get_collection(COLLECTION)
            print(f"  Indexed {total_indexed:,} | Qdrant count: {info.points_count:,}")

    save_checkpoint(indexed_ids)
    info = client.get_collection(COLLECTION)
    print(f"\n✅ Done. '{COLLECTION}' has {info.points_count:,} vectors in Qdrant Cloud.")


if __name__ == "__main__":
    main()
