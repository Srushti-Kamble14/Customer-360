"""
Tilores benchmark on the synthetic FEBRL-style dataset.

Measures:
  - Setup time: from start to first request
  - Ingestion time: bulk-ingest all records via batch-graphql
  - Throughput: records per second
  - Precision / Recall / F1 via per-record entityByRecord lookups
  - Real-time search latency (avg / p95)
  - Infrastructure: managed SaaS (no cluster, no local database)

Tooling:
  - Bulk ingest: tilotech/batch-graphql CLI (recommended Tilores production tool)
    https://github.com/tilotech/batch-graphql
  - Eval queries: direct GraphQL via the requests library

Usage:
  export TILORES_API_URL=https://YOUR_INSTANCE.svc.tilores.io/YOUR_ID/graphql
  export TILORES_TOKEN=your-token-here
  python benchmark/benchmark_tilores_febrl.py

Prerequisites:
  pip install pandas requests
  go install github.com/tilotech/batch-graphql@latest
  python benchmark/generate_febrl_data.py        # generates records.csv + ground_truth.csv
"""

import csv
import json
import os
import random
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd
import requests

ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = Path(__file__).parent / "data"
RECORDS_CSV = DATA_DIR / "records.csv"
RECORDS_JSONL = DATA_DIR / "records.jsonl"
GROUND_TRUTH_PATH = DATA_DIR / "ground_truth.csv"
RESULTS_PATH = DATA_DIR / "tilores_febrl_results.json"

CONFIG_DIR = Path(__file__).parent / "tilores_configs" / "febrl"
MUTATION_GRAPHQL = CONFIG_DIR / "schema" / "mutation.graphqls"

INGEST_CONCURRENCY = 30
EVAL_SAMPLE_SIZE = 100_000
ASSEMBLY_POLL_INTERVAL_SEC = 10
ASSEMBLY_TIMEOUT_SEC = 3600


def env(name: str, required: bool = True) -> str:
    val = os.environ.get(name, "")
    if required and not val:
        raise EnvironmentError(f"Set {name} environment variable before running.")
    return val


def gql(session: requests.Session, query: str, variables: dict | None = None) -> dict:
    """Execute a GraphQL request and return the parsed response (raises on HTTP/GraphQL error)."""
    payload = {"query": query}
    if variables is not None:
        payload["variables"] = variables
    r = session.post(API_URL, json=payload, timeout=120)
    r.raise_for_status()
    body = r.json()
    if body.get("errors"):
        raise RuntimeError(f"GraphQL errors: {body['errors']}")
    return body["data"]


def convert_csv_to_jsonl(csv_path: Path, jsonl_path: Path) -> int:
    """Convert FEBRL CSV → JSONL with snake_case fields matching the Tilores schema."""
    if jsonl_path.exists() and jsonl_path.stat().st_mtime >= csv_path.stat().st_mtime:
        n = sum(1 for _ in jsonl_path.open())
        print(f"  Reusing existing {jsonl_path.name} ({n:,} records)")
        return n

    print(f"  Converting {csv_path.name} → {jsonl_path.name}...")
    n = 0
    with csv_path.open(newline="", encoding="utf-8") as fin, jsonl_path.open("w", encoding="utf-8") as fout:
        for row in csv.DictReader(fin):
            record = {
                "id":             row["record_id"],
                "first_name":     row["first_name"]     or None,
                "last_name":      row["last_name"]      or None,
                "date_of_birth":  row["date_of_birth"]  or None,
                "street_address": row["street_address"] or None,
                "city":           row["city"]           or None,
                "postcode":       row["postcode"]       or None,
                "phone":          row["phone"]          or None,
                "email":          row["email"]          or None,
            }
            fout.write(json.dumps(record, ensure_ascii=False) + "\n")
            n += 1
    print(f"  Wrote {n:,} records to {jsonl_path}")
    return n


def ingest_via_batch_graphql(jsonl_path: Path, total: int) -> dict:
    """Bulk-ingest via batch-graphql. Returns timing + error counts."""
    if not shutil.which("batch-graphql"):
        raise EnvironmentError(
            "batch-graphql CLI not found. Install via: go install github.com/tilotech/batch-graphql@latest"
        )

    config_path = DATA_DIR / "_batch_graphql_config.json"
    cfg = {"url": API_URL}
    if TOKEN:
        cfg["headers"] = {"Authorization": f"Bearer {TOKEN}"}
    config_path.write_text(json.dumps(cfg))

    result_path = DATA_DIR / "_ingest_result.jsonl"
    error_path = DATA_DIR / "_ingest_errors.jsonl"
    for p in (result_path, error_path):
        p.unlink(missing_ok=True)

    print(f"\nIngesting {total:,} records via batch-graphql (-c {INGEST_CONCURRENCY})...")
    t_start = time.perf_counter()

    # jq wraps each line as {"record": <line>} to match the mutation variable
    jq_proc = subprocess.Popen(
        ["jq", "-cM", "{record:.}", str(jsonl_path)],
        stdout=subprocess.PIPE,
    )
    bg_proc = subprocess.Popen(
        [
            "batch-graphql",
            "-q", str(MUTATION_GRAPHQL),
            "-c", str(INGEST_CONCURRENCY),
            "--config", str(config_path),
            "-o", str(result_path),
            "-e", str(error_path),
        ],
        stdin=jq_proc.stdout,
    )
    jq_proc.stdout.close()
    bg_proc.communicate()
    jq_proc.wait()

    elapsed = time.perf_counter() - t_start
    errors = sum(1 for _ in error_path.open()) if error_path.exists() else 0
    ingested = total - errors
    print(f"  Ingest complete: {ingested:,} OK, {errors:,} errors in {elapsed:.1f}s")
    return {
        "ingested": ingested,
        "errors": errors,
        "ingest_time_sec": round(elapsed, 2),
        "ingest_throughput_records_per_sec": round(ingested / elapsed) if elapsed > 0 else 0,
    }


def wait_for_assembly_ready(session: requests.Session) -> float:
    """Poll metrics.assemblyStatus until READY. Returns wait time in seconds."""
    print("\nWaiting for assembly READY...")
    t_start = time.perf_counter()
    deadline = t_start + ASSEMBLY_TIMEOUT_SEC
    while time.perf_counter() < deadline:
        try:
            data = gql(session, "{ metrics { assemblyStatus { state } } }")
            state = data["metrics"]["assemblyStatus"]["state"]
        except (KeyError, RuntimeError) as e:
            # Some SaaS instances may not expose this field; treat as ready
            print(f"  metrics.assemblyStatus not available ({e}); proceeding")
            return 0.0
        if state == "READY":
            elapsed = time.perf_counter() - t_start
            print(f"  Assembly READY after {elapsed:.0f}s")
            return elapsed
        print(f"  Assembly state: {state} ({time.perf_counter() - t_start:.0f}s elapsed)")
        time.sleep(ASSEMBLY_POLL_INTERVAL_SEC)
    raise TimeoutError(f"Assembly did not reach READY within {ASSEMBLY_TIMEOUT_SEC}s")


ENTITY_BY_RECORD_QUERY = """
query($id: ID!) {
  entityByRecord(input: { id: $id }) {
    entity {
      id
      records { id }
    }
  }
}
"""


def evaluate_accuracy(session: requests.Session, ground_truth_path: Path) -> dict:
    """Sample ground-truth pairs, fetch each record's entity, compute precision/recall."""
    gt = pd.read_csv(ground_truth_path, dtype=str)
    gt_pairs = set(zip(gt["record_id_1"], gt["record_id_2"]))
    gt_pairs |= {(b, a) for a, b in gt_pairs}  # bidirectional

    sample_size = min(EVAL_SAMPLE_SIZE, len(gt))
    sample_gt = gt.sample(n=sample_size, random_state=42)

    tp = fp = fn = 0
    latencies: list[float] = []
    print(f"\nEvaluating accuracy on {sample_size:,} ground-truth pairs...")

    for _, row in sample_gt.iterrows():
        rid1 = row["record_id_1"]
        expected_dup = row["record_id_2"]
        t_q = time.perf_counter()
        try:
            data = gql(session, ENTITY_BY_RECORD_QUERY, {"id": rid1})
            latencies.append((time.perf_counter() - t_q) * 1000)
        except Exception as e:
            print(f"  Search error for {rid1}: {e}")
            fn += 1
            continue
        entity = (data.get("entityByRecord") or {}).get("entity") or {}
        member_ids = {rec["id"] for rec in entity.get("records", [])} - {rid1}
        for mid in member_ids:
            if (rid1, mid) in gt_pairs:
                tp += 1
            else:
                fp += 1
        if expected_dup not in member_ids:
            fn += 1

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall    = tp / (tp + fn) if (tp + fn) else 0.0
    f1        = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    latencies.sort()
    return {
        "sample_size": sample_size,
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "avg_search_latency_ms": round(sum(latencies) / len(latencies), 1) if latencies else 0,
        "p95_search_latency_ms": round(latencies[int(len(latencies) * 0.95)], 1) if latencies else 0,
    }


def main() -> None:
    global API_URL, TOKEN
    API_URL = env("TILORES_API_URL")
    TOKEN   = env("TILORES_TOKEN", required=False)  # local servers run with auth disabled

    if not RECORDS_CSV.exists():
        sys.exit(f"records.csv not found. Run benchmark/generate_febrl_data.py first.")
    if not MUTATION_GRAPHQL.exists():
        sys.exit(f"mutation.graphqls not found at {MUTATION_GRAPHQL}")

    results: dict = {}

    # Setup
    print("Connecting to Tilores API...")
    t_setup = time.perf_counter()
    session = requests.Session()
    if TOKEN:
        session.headers["Authorization"] = f"Bearer {TOKEN}"
    session.headers["Content-Type"] = "application/json"
    # smoke-test the connection
    gql(session, "{ __typename }")
    results["setup_time_sec"] = round(time.perf_counter() - t_setup, 3)
    print(f"  Setup time: {results['setup_time_sec']}s")

    # Convert CSV → JSONL
    total_records = convert_csv_to_jsonl(RECORDS_CSV, RECORDS_JSONL)
    results["record_count"] = total_records

    # Bulk ingest
    ingest_metrics = ingest_via_batch_graphql(RECORDS_JSONL, total_records)
    results.update(ingest_metrics)
    results["assembly_wait_time_sec"] = round(wait_for_assembly_ready(session), 2)
    results["total_run_time_sec"] = round(
        results["setup_time_sec"] + ingest_metrics["ingest_time_sec"] + results["assembly_wait_time_sec"], 2
    )

    # Accuracy + latency
    if GROUND_TRUTH_PATH.exists():
        accuracy = evaluate_accuracy(session, GROUND_TRUTH_PATH)
        results["accuracy"] = accuracy
        print(f"\n  Precision: {accuracy['precision']:.4f}")
        print(f"  Recall:    {accuracy['recall']:.4f}")
        print(f"  F1:        {accuracy['f1']:.4f}")
        print(f"  Avg search latency: {accuracy['avg_search_latency_ms']}ms")
    else:
        print("\nGround truth not found — skipping accuracy evaluation")

    results["infrastructure"] = {
        "tool": "Tilores managed SaaS (GraphQL API)",
        "ingest_tool": "batch-graphql (Go CLI)",
        "install_commands": [
            "pip install pandas requests",
            "go install github.com/tilotech/batch-graphql@latest",
        ],
        "requires_cluster":  False,
        "requires_account":  True,
        "requires_api_key":  True,
        "estimated_cost_usd": "Per-UCR pricing — contact Tilores for quote",
    }

    RESULTS_PATH.write_text(json.dumps(results, indent=2))
    print(f"\nResults saved to {RESULTS_PATH}")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
