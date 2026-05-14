"""
Dataset 4: Human labeling app — annotate 1,000 clauses for evaluation benchmark.
Uses Streamlit for a fast, clean UI.

Stratified sampling (from your plan):
  200 termination
  200 payment
  150 liability
  150 ip_ownership
  100 warranty
  200 mixed

Input:  data/processed/clauses.json
Output: data/processed/labeled_clauses.json

Run: streamlit run data/scripts/8_labeling_app.py
"""
import json
import random
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

CLAUSES_FILE = Path("data/processed/clauses.json")
OUTPUT = Path("data/processed/labeled_clauses.json")

SAMPLE_TARGETS = {
    "termination":  200,
    "payment":      200,
    "liability":    150,
    "ip_ownership": 150,
    "warranty":     100,
    "mixed":        200,  # random from other types
}

MIXED_TYPES = [
    "confidentiality", "indemnification", "dispute_resolution",
    "force_majeure", "governing_law", "assignment", "amendment", "general",
]

RISK_OPTIONS = {
    1: "⭐ Very Favorable (strongly protects you)",
    2: "⭐⭐ Favorable (leans in your favor)",
    3: "⭐⭐⭐ Neutral / Balanced",
    4: "⭐⭐⭐⭐ Unfavorable (leans against you)",
    5: "🚨 Very Unfavorable — RED FLAG",
}


@st.cache_data
def load_sample() -> list[dict]:
    if not CLAUSES_FILE.exists():
        return []

    all_clauses = json.loads(CLAUSES_FILE.read_text())
    grouped: dict[str, list[dict]] = {}
    for c in all_clauses:
        grouped.setdefault(c["clause_type"], []).append(c)

    sample = []

    for clause_type, target in SAMPLE_TARGETS.items():
        if clause_type == "mixed":
            pool = []
            for mt in MIXED_TYPES:
                pool.extend(grouped.get(mt, []))
            random.shuffle(pool)
            sample.extend(pool[:target])
        else:
            pool = grouped.get(clause_type, [])
            random.shuffle(pool)
            sample.extend(pool[:target])

    random.shuffle(sample)
    return sample


def load_labels() -> dict[str, dict]:
    if OUTPUT.exists():
        data = json.loads(OUTPUT.read_text())
        return {item["clause_id"]: item for item in data}
    return {}


def save_labels(labels: dict[str, dict]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(list(labels.values()), indent=2))


# ─── Streamlit UI ───────────────────────────────────────────────────────────

st.set_page_config(
    page_title="LegalAI — Clause Labeling",
    page_icon="⚖️",
    layout="centered",
)

st.title("⚖️ LegalAI Clause Labeling")
st.caption("Label 1,000 clauses from a **client's perspective** to build the evaluation benchmark.")

sample = load_sample()
labels = load_labels()

if not sample:
    st.error("No clauses found. Run scripts 1–4 first to generate data.")
    st.stop()

# Progress
labeled_count = len(labels)
total = len(sample)
remaining = [c for c in sample if c["clause_id"] not in labels]

col1, col2, col3 = st.columns(3)
col1.metric("Labeled", labeled_count)
col2.metric("Remaining", len(remaining))
col3.metric("Target", total)
st.progress(labeled_count / total if total else 0)

if not remaining:
    st.success("🎉 All clauses labeled! Evaluation benchmark complete.")
    st.balloons()
    st.stop()

# Current clause
clause = remaining[0]

st.divider()
st.subheader(f"Clause #{labeled_count + 1} of {total}")

# Metadata
col_a, col_b = st.columns(2)
col_a.info(f"**Type:** {clause['clause_type'].replace('_', ' ').title()}")
col_b.info(f"**Contract:** {clause.get('contract_type', 'Unknown').replace('_', ' ').title()}")

# Clause text
st.markdown("### Clause Text")
st.markdown(
    f"""<div style="background:#f8f9fa;border-left:4px solid #4A90D9;padding:16px;border-radius:4px;font-size:15px;line-height:1.6">
    {clause['text']}
    </div>""",
    unsafe_allow_html=True,
)

st.markdown("---")
st.markdown("### Your Assessment *(from the CLIENT's perspective)*")

risk_score = st.radio(
    "Risk Level",
    options=list(RISK_OPTIONS.keys()),
    format_func=lambda x: RISK_OPTIONS[x],
    horizontal=False,
)

reason = st.text_area(
    "Why this score? *(1 sentence)*",
    placeholder="e.g. The vendor can exit any time with no notice, leaving the client stranded.",
    max_chars=300,
)

confirmed_type = st.selectbox(
    "Confirm / correct clause type",
    options=[
        "termination", "payment", "liability", "confidentiality",
        "ip_ownership", "warranty", "indemnification", "dispute_resolution",
        "force_majeure", "governing_law", "assignment", "amendment", "general",
    ],
    index=["termination", "payment", "liability", "confidentiality",
           "ip_ownership", "warranty", "indemnification", "dispute_resolution",
           "force_majeure", "governing_law", "assignment", "amendment", "general"].index(
        clause["clause_type"]
    ) if clause["clause_type"] in ["termination", "payment", "liability", "confidentiality",
                                    "ip_ownership", "warranty", "indemnification", "dispute_resolution",
                                    "force_majeure", "governing_law", "assignment", "amendment", "general"] else 12,
)

col_save, col_skip = st.columns([3, 1])

if col_save.button("✅ Save & Next", type="primary", use_container_width=True):
    if not reason.strip():
        st.warning("Please add a reason before saving.")
    else:
        labels[clause["clause_id"]] = {
            **clause,
            "clause_type": confirmed_type,
            "human_label": {
                "risk_score": risk_score,
                "risk_level": {1: "very_favorable", 2: "favorable", 3: "neutral",
                               4: "unfavorable", 5: "critical"}[risk_score],
                "reason": reason.strip(),
                "labeled_by": "kshitiz",
                "labeled_at": datetime.now(timezone.utc).isoformat(),
            },
        }
        save_labels(labels)
        st.rerun()

if col_skip.button("⏭ Skip", use_container_width=True):
    labels[clause["clause_id"]] = {**clause, "human_label": None, "skipped": True}
    save_labels(labels)
    st.rerun()

# Sidebar stats
with st.sidebar:
    st.header("Session Stats")
    st.metric("Labeled this session", labeled_count)

    if labels:
        st.subheader("Risk Distribution")
        from collections import Counter
        dist = Counter(
            v["human_label"]["risk_score"]
            for v in labels.values()
            if v.get("human_label") and v["human_label"]
        )
        for score in range(1, 6):
            count = dist.get(score, 0)
            st.write(f"{'⭐' * score}: {count}")

    st.divider()
    st.caption(f"Output: {OUTPUT}")
    if OUTPUT.exists():
        size_kb = OUTPUT.stat().st_size / 1024
        st.caption(f"File size: {size_kb:.1f} KB")
