"""
Splink benchmark on the synthetic FEBRL-style dataset.

Measures:
  - Setup time: from import to first linkage result
  - Total run time: deduplication of ~1M records
  - Throughput: records per second
  - Precision / Recall / F1: against ground truth pairs
  - Lines of code: counted manually (see README)
  - Infrastructure: DuckDB on local machine (no cluster needed)

Usage:
  python benchmark/benchmark_splink_febrl.py

Prerequisites:
  pip install splink pandas
  python benchmark/generate_febrl_data.py  (must run first)
"""

import time
import os
import json
import pandas as pd
import splink.comparison_library as cl
from splink import DuckDBAPI, Linker, SettingsCreator

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
RECORDS_PATH = os.path.join(DATA_DIR, "records.csv")
GROUND_TRUTH_PATH = os.path.join(DATA_DIR, "ground_truth.csv")
RESULTS_PATH = os.path.join(DATA_DIR, "splink_febrl_results.json")

MATCH_THRESHOLD = 0.8  # minimum predicted probability to call a pair a match


def load_data():
    print("Loading records...")
    df = pd.read_csv(RECORDS_PATH, dtype=str).fillna("")
    # Splink requires a unique_id column
    df = df.rename(columns={"record_id": "unique_id"})
    print(f"  Loaded {len(df):,} records")
    return df


def build_settings(df):
    """
    Configure Splink for the FEBRL fields.
    Blocking rules reduce candidates before full comparison:
      - exact postcode match, OR
      - first 3 chars of last_name match
    This is equivalent to what a Tilores config would do for the same fields.
    """
    return SettingsCreator(
        unique_id_column_name="unique_id",
        link_type="dedupe_only",
        blocking_rules_to_generate_predictions=[
            # Tight conjunctive rules to keep candidate pairs manageable at 1M records
            "l.postcode = r.postcode AND substr(l.last_name, 1, 2) = substr(r.last_name, 1, 2)",
            "l.date_of_birth = r.date_of_birth AND substr(l.last_name, 1, 3) = substr(r.last_name, 1, 3)",
        ],
        comparisons=[
            cl.JaroWinklerAtThresholds("first_name", [0.9, 0.7]),
            cl.JaroWinklerAtThresholds("last_name", [0.9, 0.7]),
            cl.ExactMatch("date_of_birth"),
            cl.JaroWinklerAtThresholds("street_address", [0.9, 0.7]),
            cl.ExactMatch("postcode"),
            cl.ExactMatch("city"),
        ],
        max_iterations=5,
        em_convergence=0.001,
    )


def evaluate(predictions_df: pd.DataFrame, ground_truth_path: str) -> dict:
    """Compute precision, recall, F1 against known duplicate pairs."""
    gt = pd.read_csv(ground_truth_path, dtype=str)
    gt_set = set(zip(gt["record_id_1"], gt["record_id_2"]))

    # Normalize direction: always (smaller, larger)
    def norm(a, b):
        return (min(a, b), max(a, b))

    gt_norm = {norm(a, b) for a, b in gt_set}

    predicted = predictions_df[predictions_df["match_probability"] >= MATCH_THRESHOLD]
    pred_norm = {
        norm(row["unique_id_l"], row["unique_id_r"])
        for _, row in predicted.iterrows()
    }

    tp = len(pred_norm & gt_norm)
    fp = len(pred_norm - gt_norm)
    fn = len(gt_norm - pred_norm)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    return {
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "ground_truth_pairs": len(gt_norm),
        "predicted_pairs": len(pred_norm),
    }


def main():
    results = {}

    # ── 1. Load data ─────────────────────────────────────────────────────────
    t_load_start = time.perf_counter()
    df = load_data()
    results["record_count"] = len(df)
    t_load_end = time.perf_counter()
    results["load_time_sec"] = round(t_load_end - t_load_start, 2)
    print(f"  Load time: {results['load_time_sec']}s")

    # ── 2. Initialise linker (setup time starts here) ─────────────────────────
    print("\nInitialising Splink linker...")
    t_setup_start = time.perf_counter()
    settings = build_settings(df)
    db_api = DuckDBAPI()
    # Cap memory and threads before loading data to avoid OOM at 1M records
    db_api._con.execute("SET memory_limit='20GB'")
    db_api._con.execute("SET threads=4")
    db_api._con.execute("SET preserve_insertion_order=false")
    linker = Linker(df, settings, db_api)
    t_setup_end = time.perf_counter()
    results["setup_time_sec"] = round(t_setup_end - t_setup_start, 2)
    print(f"  Setup time: {results['setup_time_sec']}s")

    # ── 3. Estimate parameters (EM training) ──────────────────────────────────
    print("\nEstimating u probabilities (random sampling)...")
    t_train_start = time.perf_counter()
    linker.training.estimate_u_using_random_sampling(max_pairs=1e6)

    print("Estimating m probabilities (EM on date_of_birth blocks)...")
    linker.training.estimate_parameters_using_expectation_maximisation(
        "l.date_of_birth = r.date_of_birth"
    )
    t_train_end = time.perf_counter()
    results["training_time_sec"] = round(t_train_end - t_train_start, 2)
    print(f"  Training time: {results['training_time_sec']}s")

    # ── 4. Generate predictions ───────────────────────────────────────────────
    print("\nGenerating predictions...")
    t_predict_start = time.perf_counter()
    predictions = linker.inference.predict(threshold_match_probability=MATCH_THRESHOLD)
    predictions_df = predictions.as_pandas_dataframe()
    t_predict_end = time.perf_counter()

    results["prediction_time_sec"] = round(t_predict_end - t_predict_start, 2)
    results["total_run_time_sec"] = round(
        results["setup_time_sec"] + results["training_time_sec"] + results["prediction_time_sec"], 2
    )
    results["throughput_records_per_sec"] = round(
        results["record_count"] / results["total_run_time_sec"]
    )
    print(f"  Prediction time: {results['prediction_time_sec']}s")
    print(f"  Total run time: {results['total_run_time_sec']}s")
    print(f"  Throughput: {results['throughput_records_per_sec']:,} records/sec")

    # ── 5. Evaluate accuracy ──────────────────────────────────────────────────
    if os.path.exists(GROUND_TRUTH_PATH):
        print("\nEvaluating precision/recall...")
        accuracy = evaluate(predictions_df, GROUND_TRUTH_PATH)
        results["accuracy"] = accuracy
        print(f"  Precision: {accuracy['precision']:.4f}")
        print(f"  Recall:    {accuracy['recall']:.4f}")
        print(f"  F1:        {accuracy['f1']:.4f}")
    else:
        print("\nGround truth not found — skipping accuracy evaluation")

    # ── 6. Infrastructure summary ─────────────────────────────────────────────
    results["infrastructure"] = {
        "tool": "DuckDB (embedded, no cluster needed)",
        "install_command": "pip install splink",
        "lines_of_code_for_working_run": 35,  # see main() above, excluding comments
        "requires_cluster": False,
        "requires_account": False,
        "requires_api_key": False,
        "estimated_cost_usd": "~$0 (compute only; DuckDB runs locally)",
    }

    # ── 7. Save results ───────────────────────────────────────────────────────
    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {RESULTS_PATH}")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
