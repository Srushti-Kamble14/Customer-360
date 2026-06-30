"""
Compile benchmark result JSONs into a human-readable Markdown report.

Usage:
  python benchmark/compile_results.py

Input files (must exist):
  benchmark/data/splink_febrl_results.json
  benchmark/data/tilores_febrl_results.json

Output:
  benchmark/benchmark_results.md
"""

import json
import os
from pathlib import Path
from datetime import date

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_PATH = Path(__file__).parent / "benchmark_results.md"

RESULT_FILES = {
    "splink_febrl": DATA_DIR / "splink_febrl_results.json",
    "tilores_febrl": DATA_DIR / "tilores_febrl_results.json",
}


def load(path: Path) -> dict:
    if not path.exists():
        print(f"  WARNING: {path.name} not found — results will be incomplete")
        return {}
    with open(path) as f:
        return json.load(f)


def fmt(val, suffix="", missing="N/A") -> str:
    if val is None or val == {}:
        return missing
    if isinstance(val, float):
        return f"{val}{suffix}"
    if isinstance(val, int):
        return f"{val:,}{suffix}"
    return f"{val}{suffix}"


def main():
    results = {k: load(v) for k, v in RESULT_FILES.items()}

    sf = results["splink_febrl"]
    tf = results["tilores_febrl"]

    lines = []
    a = lines.append

    a(f"# Splink vs. Tilores — Benchmark Results")
    a(f"")
    a(f"**Date:** {date.today().isoformat()}  ")
    a(f"**Status:** auto-generated from result JSONs  ")
    a(f"**Dataset:** FEBRL synthetic (~1M records)")
    a(f"")
    a(f"---")
    a(f"")

    # ── FEBRL Summary ──────────────────────────────────────────────────────────
    a(f"## 1. FEBRL Dataset (~1M Records, Synthetic, Ground Truth Available)")
    a(f"")
    a(f"### 1.1 Setup & Runtime")
    a(f"")
    a(f"| Metric | Splink (DuckDB) | Tilores (SaaS API) |")
    a(f"|---|---|---|")
    a(f"| Records | {fmt(sf.get('record_count'))} | {fmt(tf.get('record_count'))} |")
    a(f"| Setup time | {fmt(sf.get('setup_time_sec'), 's')} | {fmt(tf.get('setup_time_sec'), 's')} |")
    a(f"| Training time | {fmt(sf.get('training_time_sec'), 's')} | N/A (managed) |")
    a(f"| Prediction / Ingest time | {fmt(sf.get('prediction_time_sec'), 's')} | {fmt(tf.get('ingest_time_sec'), 's')} |")
    a(f"| **Total run time** | **{fmt(sf.get('total_run_time_sec'), 's')}** | **{fmt(tf.get('total_run_time_sec'), 's')}** |")
    a(f"| Throughput (records/sec) | {fmt(sf.get('throughput_records_per_sec'))} | {fmt(tf.get('ingest_throughput_records_per_sec'))} |")
    a(f"")

    a(f"### 1.2 Accuracy (Precision / Recall / F1)")
    a(f"")
    sf_acc = sf.get("accuracy", {})
    tf_acc = tf.get("accuracy", {})
    a(f"| Metric | Splink | Tilores |")
    a(f"|---|---|---|")
    a(f"| Precision | {fmt(sf_acc.get('precision'))} | {fmt(tf_acc.get('precision'))} |")
    a(f"| Recall | {fmt(sf_acc.get('recall'))} | {fmt(tf_acc.get('recall'))} |")
    a(f"| F1 Score | {fmt(sf_acc.get('f1'))} | {fmt(tf_acc.get('f1'))} |")
    a(f"| True positives | {fmt(sf_acc.get('true_positives'))} | {fmt(tf_acc.get('true_positives'))} |")
    a(f"| False positives | {fmt(sf_acc.get('false_positives'))} | {fmt(tf_acc.get('false_positives'))} |")
    a(f"| False negatives | {fmt(sf_acc.get('false_negatives'))} | {fmt(tf_acc.get('false_negatives'))} |")
    a(f"| Ground truth pairs | {fmt(sf_acc.get('ground_truth_pairs'))} | {fmt(tf_acc.get('ground_truth_pairs'))} |")
    a(f"")

    a(f"### 1.3 Infrastructure")
    a(f"")
    sf_infra = sf.get("infrastructure", {})
    tf_infra = tf.get("infrastructure", {})
    a(f"| Dimension | Splink | Tilores |")
    a(f"|---|---|---|")
    a(f"| Install | `{sf_infra.get('install_command', 'pip install splink')}` | `{tf_infra.get('install_command', 'pip install tilores-sdk')}` |")
    a(f"| Lines of code (working run) | {fmt(sf_infra.get('lines_of_code_for_working_run'))} | {fmt(tf_infra.get('lines_of_code_for_working_run'))} |")
    a(f"| Requires cluster | {sf_infra.get('requires_cluster', False)} | {tf_infra.get('requires_cluster', False)} |")
    a(f"| Requires account/API key | No | Yes |")
    a(f"| Estimated cost | {sf_infra.get('estimated_cost_usd', '~$0')} | {tf_infra.get('estimated_cost_usd', 'Per-UCR pricing')} |")
    a(f"")

    # ── Interpretation ─────────────────────────────────────────────────────────
    a(f"---")
    a(f"")
    a(f"## 3. Interpretation")
    a(f"")
    a(f"This is an auto-generated raw report. For the full interpretation, fairness")
    a(f"rationale, and the honest trade-off between the two tools, see")
    a(f"[`METHODOLOGY.md`](../METHODOLOGY.md) and the curated [`RESULTS.md`](../RESULTS.md).")
    a(f"")

    # ── Raw JSON ───────────────────────────────────────────────────────────────
    a(f"---")
    a(f"")
    a(f"## 4. Raw Results (JSON)")
    a(f"")
    for name, data in results.items():
        a(f"### {name}")
        a(f"```json")
        a(json.dumps(data, indent=2))
        a(f"```")
        a(f"")

    output = "\n".join(lines)
    OUTPUT_PATH.write_text(output, encoding="utf-8")
    print(f"Results compiled to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
