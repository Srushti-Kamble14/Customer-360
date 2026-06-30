# Benchmark Data — Overview

**Purpose:** Reference for the FEBRL synthetic dataset used in this benchmark — its schema, the corruption ("noise") model, and how to regenerate it.

The large data files are **not** committed to git (see the repo `.gitignore`). They are fully reproducible from the generator script.

---

## FEBRL synthetic (`records.jsonl`, `records.csv`, `ground_truth.csv`)

### What it is

A 1 M-record synthetic person dataset generated with `Faker(en_GB)` and a controlled corruption layer. Designed to mimic the well-known ANU FEBRL benchmark patterns at production scale. Fully deterministic (seed `42`) — regenerating produces byte-identical output.

### Volume

| File | Records | Purpose |
|---|--:|---|
| `records.jsonl` | 1,000,000 | Line-delimited input for Tilores ingest (one JSON object per line) |
| `records.csv` | 1,000,000 | Identical data in CSV. `wc -l` reports ~1.5 M because ~497 k records contain embedded newlines in `street_address` (UK Faker produces multi-line addresses like `"Studio 4\nLydia Islands"`). Always parse with a real CSV reader (Python `csv`, pandas, DuckDB `read_csv`) — never with `awk`, `head`, or `for line in $(cat …)`. |
| `ground_truth.csv` | 100,000 pairs | Known duplicate pairs for accuracy measurement |

The 1 M records break down as: **900,000 unique entities + 100,000 duplicate records** (each duplicate is a corrupted copy of one of the originals — one duplicate per ~9th entity, ~10 % duplicate rate).

### Schema (per record)

```json
{
  "id": "E0000000",                       // record_id; duplicates suffix with "_dup"
  "first_name": "Ruth",
  "last_name": "Griffiths",
  "date_of_birth": "1989-06-25",          // ISO YYYY-MM-DD
  "street_address": "2 Sian Streets",
  "city": "New Maryton",                  // city is NEVER corrupted (anchor field)
  "postcode": "E3 8ZA",                   // UK postcode format
  "phone": "+44(0)191496038",             // +44 with optional (0) and varied formatting
  "email": "ruth.griffiths@yahoo.com"     // {first}.{last}@{free_provider} — never corrupted
}
```

CSV adds two extra columns at the front:
```
record_id, entity_id, first_name, last_name, date_of_birth, street_address, city, postcode, phone, email
```
where `entity_id` is the **true match key** — an original record and its duplicate share the same `entity_id` (e.g. `E0000009` and `E0000009_dup`).

### Ground truth format

```csv
record_id_1,record_id_2
E0000009,E0000009_dup
E0000037,E0000037_dup
```

100,000 pairs. Each pair = one original + its duplicate. There are **no transitive triplets** — the corruption pipeline produces exactly one duplicate per affected entity, so clusters are always size 2.

### Corruption recipe (the "noise model")

Each duplicate is a copy of an original with 1–3 fields corrupted, drawn uniformly from `[first_name, last_name, date_of_birth, street_address, postcode, phone]`. Operations per corrupted field (uniform random):

| Op | Example |
|---|---|
| `swap` | `John` → `Jonh` |
| `delete` | `John` → `Jon` |
| `insert` | `John` → `Johnn` |
| `replace` | `John` → `Jorn` |

Special cases:
- **Date corruption** shifts day or month by ±1 (clamped to valid ranges) — simulates transposition errors.
- **10 % chance** one of `[phone, email, street_address]` is blanked entirely (`""`).
- **`city` is never corrupted** — intentional anchor field; used as an exact-match anchor in the Tilores rule config.
- **`email` is never corrupted directly** — but may be blanked by the 10 % rule.

### Characteristics worth knowing

- **Duplicate density ~10 %**: enough signal that recall metrics are not noisy.
- **Cluster size cap = 2**: this dataset cannot exercise multi-record-cluster behaviour.
- **No address geocoding**: addresses are Faker-generated UK strings; postcode-to-lat/lon is fictional.
- **No name reversals**: first/last are never swapped.
- **UK locale**: names, postcodes and phone numbers follow `en_GB` conventions.

### Regenerating

```bash
python benchmark/generate_febrl_data.py
# → benchmark/data/records.csv + ground_truth.csv
#   (JSONL conversion happens inside benchmark_tilores_febrl.py)
```

Runtime ~3–5 min on a laptop. Disk ~300 MB.

---

## Result files

Pre-computed result JSONs live in [`../../results/`](../../results/):

| File | Description |
|---|---|
| `splink_febrl_results.json` | Splink (DuckDB) on FEBRL — F1 0.8867, throughput 108 k rec/s |
| `tilores_febrl_results.json` | Tilores on FEBRL — F1 0.9949 |
| `headline_metrics.json` | Side-by-side headline comparison |

Compile a fresh raw report after a new run:

```bash
python benchmark/compile_results.py
# → benchmark/benchmark_results.md  (curated summary lives in RESULTS.md)
```
