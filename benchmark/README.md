# Splink vs. Tilores — Live Benchmark

This directory contains reproducible benchmark scripts for comparing Splink and Tilores on the FEBRL-style dataset (~1M synthetic records, known ground truth) — measuring accuracy, throughput, and real-time search latency.

---

## Prerequisites

**Python 3.10+** with a virtual environment:

```bash
cd /path/to/tilores-splink-benchmark
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install splink faker pandas requests
```

**For Tilores benchmarks:** You need a running Tilores instance and an API token.

```bash
export TILORES_API_URL=https://YOUR_INSTANCE.svc.tilores.io/YOUR_ID/graphql
export TILORES_TOKEN=your-token-here
```

Contact the Tilo Tech GmbH team to provision a benchmark instance.

---

## Step-by-Step Execution

### Step 1 — Generate FEBRL Dataset

Generates ~1M synthetic personal records with ~100K known duplicate pairs.

```bash
python benchmark/generate_febrl_data.py
```

**Output:**
- `benchmark/data/records.csv` — 1M records (900K unique + 100K duplicates)
- `benchmark/data/ground_truth.csv` — known duplicate pairs for accuracy evaluation

**Runtime:** ~3–5 minutes on a standard laptop.  
**Disk:** ~300MB

---

### Step 2 — Run Splink Benchmark

```bash
python benchmark/benchmark_splink_febrl.py
```

**No API key or account required.**  
**Infrastructure:** DuckDB runs embedded in Python — no cluster, no database to set up.  
**Expected runtime:** ~10 seconds at 1M records.

---

### Step 3 — Run Tilores Benchmark

```bash
export TILORES_API_URL=https://YOUR_INSTANCE.svc.tilores.io/YOUR_ID/graphql
python benchmark/benchmark_tilores_febrl.py
```

**Requires:** Running Tilores instance with the rule config from `tilores_configs/febrl/rule-config.json`.

---

### Step 4 — Compile Results

```bash
python benchmark/compile_results.py
```

This reads the JSON result files and writes a raw report to `benchmark/benchmark_results.md`. The curated, human-edited summary lives in [`RESULTS.md`](../RESULTS.md) at the repo root.

---

## Output Files

| File | Description |
|---|---|
| `data/records.csv` | Generated FEBRL records |
| `data/ground_truth.csv` | Known duplicate pairs (FEBRL) |
| `data/splink_febrl_results.json` | Splink FEBRL benchmark results |
| `data/tilores_febrl_results.json` | Tilores FEBRL benchmark results |

---

## What We Measure

| Metric | FEBRL |
|---|---|
| Setup time (zero → first result) | ✓ |
| Batch throughput (records/sec) | ✓ |
| Total run time at ~1M records | ✓ |
| Precision / Recall / F1 | ✓ (ground truth available) |
| Real-time search latency (Tilores) | ✓ |
| Infrastructure requirements | ✓ |
| Estimated cost | ✓ |

---

## Benchmark Design Notes

### Fairness
Both tools are configured with equivalent matching logic on the same fields:
- Name similarity: Jaro-Winkler at 0.9 / 0.7 thresholds
- Date of birth: exact match
- Address: fuzzy string similarity
- Postcode: exact match

Splink uses DuckDB (single-machine, no cluster) — the fastest recommended backend for this scale.  
Tilores uses the managed SaaS API.

### Why DuckDB for Splink?
Splink's DuckDB backend is the recommended default for datasets up to ~100M records. It runs on a single machine without any cluster setup, which is the most common deployment for Splink users. This makes it the fairest comparison point for a "getting started" evaluation.

### Why no Spark?
Spark would require cluster provisioning, which is an infrastructure overhead that is part of the comparison — not a shortcut to avoid. The benchmark documents infrastructure requirements explicitly.

### Match decision boundary
**Splink** uses a match probability ≥ 0.80 as the decision boundary for a "match" (adjustable in the Splink script). **Tilores** is rule-based and has no probability score — a record pair matches if it satisfies any of the linking rules in `tilores_configs/febrl/rule-config.json`. See [`METHODOLOGY.md`](../METHODOLOGY.md) for the full rule set.

---

## Machine Specs (to document when running)

Please note the machine you ran the benchmark on in `RESULTS.md`:

```
CPU:    [e.g., Apple M3 Pro, 12-core]
RAM:    [e.g., 36GB]
OS:     [e.g., macOS 15.4]
Python: [e.g., 3.12.4]
Splink: [e.g., 4.0.16]
```

---

## License

Benchmark scripts: Apache 2.0  
FEBRL-style generated data: synthetic, no license restrictions
