"""
One-command data pipeline runner.
Runs all scripts in order, skipping steps that are already complete.

Run: python data/scripts/run_pipeline.py
     python data/scripts/run_pipeline.py --skip-scraping  (if data already collected)
     python data/scripts/run_pipeline.py --step 4         (run only step 4)
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path


STEPS = [
    {
        "num": 1,
        "name": "Scrape LawInsider (8K contracts)",
        "script": "data/scripts/1_scrape_lawinsider.py",
        "done_check": lambda: len(list(Path("data/raw/lawinsider").rglob("*.json"))) >= 100,
        "skip_with": "--skip-scraping",
        "est_time": "2–3 hours",
    },
    {
        "num": 2,
        "name": "Scrape SEC EDGAR (5K contracts)",
        "script": "data/scripts/2_scrape_sec_edgar.py",
        "done_check": lambda: len(list(Path("data/raw/sec_edgar").glob("*.json"))) >= 100,
        "skip_with": "--skip-scraping",
        "est_time": "1–2 hours",
    },
    {
        "num": 3,
        "name": "Scrape Creative Commons (2K contracts)",
        "script": "data/scripts/3_scrape_creative_commons.py",
        "done_check": lambda: len(list(Path("data/raw/creative_commons").glob("*.json"))) >= 50,
        "skip_with": "--skip-scraping",
        "est_time": "30 minutes",
    },
    {
        "num": 4,
        "name": "Parse contracts → clauses + hybrid classification (300K+)",
        "script": "data/scripts/4_parse_and_extract.py",
        "done_check": lambda: Path("data/processed/clauses.json").exists(),
        "skip_with": None,
        "est_time": "60–90 minutes (includes bart-large-mnli zero-shot pass)",
    },
    {
        "num": 5,
        "name": "Download HuggingFace legal datasets (LEDGAR + UNFAIR-ToS)",
        "script": "data/scripts/5_generate_synthetic.py",
        "done_check": lambda: Path("data/processed/synthetic_clauses.json").exists()
                              and len(json_len("data/processed/synthetic_clauses.json")) >= 10_000,
        "skip_with": None,
        "est_time": "5 minutes (one-time download)",
    },
    {
        "num": 6,
        "name": "Embed + index into Qdrant (400K clauses)",
        "script": "data/scripts/6_embed_and_index.py",
        "done_check": lambda: Path("data/processed/index_checkpoint.json").exists(),
        "skip_with": None,
        "est_time": "1–2 hours",
    },
    {
        "num": 7,
        "name": "Build BM25 index",
        "script": "data/scripts/7_build_bm25_index.py",
        "done_check": lambda: Path("data/bm25_index.pkl").exists(),
        "skip_with": None,
        "est_time": "5 minutes",
    },
]


def json_len(path: str) -> list:
    import json
    try:
        return json.loads(Path(path).read_text())
    except Exception:
        return []


def run_step(step: dict) -> bool:
    print(f"\n{'='*60}")
    print(f"Step {step['num']}: {step['name']}")
    print(f"Est. time: {step['est_time']}")
    print(f"{'='*60}")

    start = time.time()
    result = subprocess.run([sys.executable, step["script"]], check=False)
    elapsed = time.time() - start

    if result.returncode == 0:
        print(f"\n✅ Step {step['num']} complete ({elapsed:.0f}s)")
        return True
    else:
        print(f"\n❌ Step {step['num']} failed (exit code {result.returncode})")
        return False


def main():
    parser = argparse.ArgumentParser(description="LegalAI data pipeline runner")
    parser.add_argument("--skip-scraping", action="store_true",
                        help="Skip steps 1-3 (web scraping)")
    parser.add_argument("--step", type=int, default=None,
                        help="Run only this step number")
    parser.add_argument("--force", action="store_true",
                        help="Run steps even if already complete")
    args = parser.parse_args()

    print("╔══════════════════════════════════════════╗")
    print("║  LegalAI Data Pipeline                   ║")
    print("║  Target: 100,000+ clauses in Qdrant      ║")
    print("╚══════════════════════════════════════════╝")

    steps_to_run = STEPS
    if args.step:
        steps_to_run = [s for s in STEPS if s["num"] == args.step]
        if not steps_to_run:
            print(f"Step {args.step} not found.")
            sys.exit(1)

    for step in steps_to_run:
        if args.skip_scraping and step.get("skip_with") == "--skip-scraping":
            print(f"\nSkipping Step {step['num']}: {step['name']}")
            continue

        if not args.force and step["done_check"]():
            print(f"\n✓ Step {step['num']} already complete — skipping ({step['name']})")
            continue

        success = run_step(step)
        if not success:
            print(f"\nPipeline halted at step {step['num']}. Fix the error and re-run.")
            sys.exit(1)

    print("\n\n" + "="*60)
    print("✅ PIPELINE COMPLETE")
    print("="*60)
    print("\nNext steps:")
    print("  1. Start the labeling app: streamlit run data/scripts/8_labeling_app.py")
    print("  2. Label 1,000 clauses for evaluation benchmark")
    print("  3. Start the backend: uvicorn app.main:app --reload")
    print("  4. Start the frontend: npm run dev")


if __name__ == "__main__":
    main()
