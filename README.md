# Splink vs. Tilores — Reproducible Benchmark

**Tilores F1 0.9949 · Splink F1 0.8867 · +10.8pp on 1M FEBRL records**

This repository contains the benchmark code, configuration, and results for a head-to-head comparison between [Splink](https://github.com/moj-analytical-services/splink) (open-source entity resolution by the UK Ministry of Justice) and [Tilores](https://tilores.io) (commercial entity resolution API by Tilo Tech GmbH). Every number in this repo is reproducible by anyone with a Python environment and access to a Tilores instance.

---

## The Problem

Entity resolution — finding records that refer to the same real-world entity — is one of the hardest data quality problems in production. The challenge is not just accuracy at small scale; it is accuracy + low latency + incremental ingestion at millions of records. Most benchmarks stop at accuracy. This one does not.

---

## Headline Result

| Metric | Splink (DuckDB) | Tilores | Δ |
|---|---|---|---|
| **F1 Score** | 0.8867 | **0.9949** | **+10.8pp** |
| Precision | 0.9999 | **0.9998** | ~tie |
| **Recall** | 0.7965 | **0.9900** | **+19.4pp** |
| True positives (of 100K) | 79,655 | **99,000** | |
| False positives | 5 | 15 | |
| False negatives | 20,345 | **1,000** | |

Dataset: 1,000,000 synthetic FEBRL records (en_GB, seed 42) with 100,000 known ground-truth duplicate pairs. Snapshot: 2026-06-03.

---

## The Honest Trade-off

**Splink wins on batch throughput.** Running as an embedded DuckDB library, Splink processes 1M records in 9.24 seconds (108,225 rec/s). For pure offline deduplication pipelines with no real-time requirement, that is hard to beat at zero infrastructure cost.

**Tilores wins on F1, real-time search, and persistent indexing.** Tilores builds a queryable entity graph that persists after ingest. Search latency on a 1M-record index is 8.6ms p95 on LAN. Adding a new record is a single API call, not a full re-run. For customer-facing KYC or real-time fraud workflows, Splink is architecturally unsuitable; Tilores is purpose-built for them.

**One-line summary:** Splink for R&D and offline batch. Tilores for production and real-time.

---

## How to Reproduce in 4 Commands

```bash
# 1. Install dependencies
pip install splink faker pandas requests
go install github.com/tilotech/batch-graphql@latest

# 2. Generate 1M synthetic FEBRL records
python benchmark/generate_febrl_data.py

# 3. Run Splink (no account needed)
python benchmark/benchmark_splink_febrl.py

# 4. Run Tilores (requires a running Tilores instance)
export TILORES_API_URL=https://YOUR_INSTANCE.svc.tilores.io/YOUR_ID/graphql
export TILORES_TOKEN=your-token-here
python benchmark/benchmark_tilores_febrl.py
```

See [`benchmark/README.md`](benchmark/README.md) for the full step-by-step guide and result compilation.

---

## Repository Structure

```
benchmark/                    Benchmark scripts (Python)
  ├── benchmark_splink_febrl.py

  ├── benchmark_tilores_febrl.py

  ├── generate_febrl_data.py

  ├── compile_results.py
  ├── data/                   Data directory (large files excluded — see .gitignore)
  │   └── README.md           Dataset documentation
  └── tilores_configs/febrl/  Tilores rule configuration used in this benchmark
results/                      Pre-computed JSON results for both tools
RESULTS.md                    Compiled benchmark results with tables
METHODOLOGY.md                Full methodology: datasets, metrics, fairness rationale
CONTRIBUTING.md               How to report issues, propose tuning improvements
TROUBLESHOOTING.md            Common reproduction failures and fixes
```

---

## Data

- **FEBRL synthetic dataset:** 1,000,000 records generated with Faker (seed 42, `en_GB`). Fully reproducible via `generate_febrl_data.py`. No license restrictions.
Large data files are excluded from git (see `.gitignore`) and must be regenerated locally.

---

## Methodology

See [`METHODOLOGY.md`](METHODOLOGY.md) for the full methodology, including dataset construction, evaluation protocol, fairness rationale, and known limitations.

Key points:
- Both tools match on the **same fields**: `first_name`, `last_name`, `date_of_birth`, `city`, `postcode`, `phone`
- **Splink:** probabilistic EM model, Jaro-Winkler ≥ 0.9 / 0.7 on names, exact DOB and postcode, match threshold probability ≥ 0.80
- **Tilores:** rule-based entity graph, Cologne phonetic + Levenshtein distance ≤ 1 on names, OSA Damerau-Levenshtein for fuzzy DOB, city-exact and postcode anchors across 6 linking rules — no probability score
- Splink backend: DuckDB (recommended default for <100M records; no cluster required)
- Tilores hardware: 32GB LXC container — same memory class as a developer laptop running Splink

---

## Tilores Rule Configuration

The exact Tilores rule configuration used in this benchmark is published at [`benchmark/tilores_configs/febrl/rule-config.json`](benchmark/tilores_configs/febrl/rule-config.json). Without it, "reproducible" is a claim, not a fact.

---

## License

Code: Apache 2.0. See [`LICENSE`](LICENSE).  
Documentation (RESULTS.md, METHODOLOGY.md, this README): CC BY 4.0.

---

## Author

Hendrik Nehnes, [Tilo Tech GmbH](https://tilores.io)  
Snapshot date: 2026-06-03 · [tilores.io](https://tilores.io)
