# Splink vs. Tilores — Benchmark Results

**Date:** 2026-06-03  
**Status:** Tilores (LAN network)  
**Dataset:** FEBRL synthetic (~1M records)

---

## 1. FEBRL Dataset (~1M Records, Synthetic, Ground Truth Available)

### 1.1 Accuracy (Precision / Recall / F1)

| Metric | Splink | Tilores | Delta |
|---|---|---|---|
| Precision | 0.9999 | **0.9998** | ~tie |
| Recall | 0.7965 | **0.9900** | **+19.4pp** |
| F1 Score | 0.8867 | **0.9949** | **+10.8pp** |
| True positives | 79,655 | 99,000 | +19,345 |
| False positives | 5 | 15 | +10 |
| False negatives | 20,345 | 1,000 | −19,345 |
| Ground truth pairs evaluated | 100,000 | 100,000 | — |

### 1.2 API / Runtime Characteristics

| Dimension | Splink (DuckDB) | Tilores (32GB local LXC) |
|---|---|---|
| Records | 1,000,000 | 1,000,000 |
| **Search latency p95** | n/a (batch only) | **8.6ms** |
| Search latency avg | n/a | 8.4ms |
| **Real-time API** | no | **yes** (GraphQL) |
| **Incremental ingest** | no (re-run batch) | **yes** (single record via API) |
| **Persistent entity index** | no | **yes** |

### 1.3 Infrastructure

| Dimension | Splink | Tilores |
|---|---|---|
| Install | `pip install splink` | `pip install pandas requests` + `go install github.com/tilotech/batch-graphql@latest` |
| Ingest tool | DuckDB (embedded Python library) | batch-graphql CLI (Go) — sends records to a running Tilores instance |
| Requires cluster | No | No |
| Requires Tilores instance | No | **Yes** — cloud SaaS or self-hosted; see [tilores.io](https://tilores.io) |
| Requires account/API key | No | Yes |
| Estimated cost | ~$0 (compute only; DuckDB runs locally) | Per-UCR pricing — contact Tilores for quote |

---

## 2. Raw Results (JSON)

### splink_febrl
```json
{
  "record_count": 1000000,
  "load_time_sec": 1.61,
  "setup_time_sec": 0.49,
  "training_time_sec": 7.96,
  "prediction_time_sec": 0.79,
  "total_run_time_sec": 9.24,
  "throughput_records_per_sec": 108225,
  "accuracy": {
    "true_positives": 79655,
    "false_positives": 5,
    "false_negatives": 20345,
    "precision": 0.9999,
    "recall": 0.7965,
    "f1": 0.8867,
    "ground_truth_pairs": 100000,
    "predicted_pairs": 79660
  },
  "infrastructure": {
    "tool": "DuckDB (embedded, no cluster needed)",
    "install_command": "pip install splink",
    "lines_of_code_for_working_run": 35,
    "requires_cluster": false,
    "requires_account": false,
    "requires_api_key": false,
    "estimated_cost_usd": "~$0 (compute only; DuckDB runs locally)"
  }
}
```

### tilores_febrl
```json
{
  "setup_time_sec": 0.019,
  "record_count": 1000000,
  "ingested": 1000000,
  "errors": 0,
  "ingest_time_sec": 6363.66,
  "accuracy": {
    "sample_size": 100000,
    "true_positives": 99000,
    "false_positives": 15,
    "false_negatives": 1000,
    "precision": 0.9998,
    "recall": 0.99,
    "f1": 0.9949,
    "avg_search_latency_ms": 8.4,
    "p95_search_latency_ms": 8.6
  },
  "infrastructure": {
    "tool": "Tilores managed SaaS (GraphQL API)",
    "ingest_tool": "batch-graphql (Go CLI)",
    "install_commands": [
      "pip install pandas requests",
      "go install github.com/tilotech/batch-graphql@latest"
    ],
    "requires_cluster": false,
    "requires_account": true,
    "requires_api_key": true,
    "estimated_cost_usd": "Per-UCR pricing — contact Tilores for quote"
  }
}
```

