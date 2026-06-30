# Troubleshooting

Common issues when reproducing this benchmark.

---

## Python Version Mismatch

**Symptom:** `ImportError` or unexpected `splink` behaviour.

**Cause:** Splink 4.x requires Python 3.10 or later. Python 3.9 and earlier are not supported.

**Fix:**
```bash
python3 --version   # must be 3.10+
python3 -m venv .venv
source .venv/bin/activate
pip install splink faker pandas requests
```

---

## DuckDB Memory Limit on Low-RAM Machines

**Symptom:** `OutOfMemoryError` or killed process during Splink run on 1M records.

**Cause:** The FEBRL benchmark at 1M records requires approximately 8–12 GB of RAM for DuckDB's blocking and comparison steps.

**Fix:**
- Use a machine with at least 16 GB RAM for reliable results
- Alternatively, reduce `SAMPLE_SIZE` in `benchmark_splink_febrl.py` and note the dataset size in your results

---

## Tilores Auth Failures

**Symptom:** `401 Unauthorized` or `GraphQL errors: [{'message': 'Unauthorized'}]`

**Cause:** `TILORES_TOKEN` is missing, expired, or set to the wrong endpoint.

**Fix:**
```bash
# Verify environment variables are set
echo $TILORES_API_URL
echo $TILORES_TOKEN

# Re-export with correct values
export TILORES_API_URL=https://YOUR_INSTANCE.svc.tilores.io/YOUR_ID/graphql
export TILORES_TOKEN=your-token-here
```

If your token has expired, generate a new one from the Tilores dashboard or contact [service@tilores.io](mailto:service@tilores.io).

---

## Tilores Connection Refused

**Symptom:** `ConnectionRefusedError` or `requests.exceptions.ConnectionError`

**Cause:** The Tilores instance at `TILORES_API_URL` is not running or the URL is incorrect.

**Fix:**
```bash
# Test connectivity
curl -s "$TILORES_API_URL" -X POST \
  -H "Authorization: Bearer $TILORES_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"{__typename}"}' | python3 -m json.tool
```

Expected: `{"data": {"__typename": "Query"}}`

---

## Throughput / Latency Numbers Don't Match

**Symptom:** Your Tilores throughput or latency differs from the numbers in RESULTS.md.

**Cause:** Throughput and latency are network-sensitive. LAN numbers (~8.6ms p95 search latency) are the canonical values for a local deployment. If your Tilores instance is reached over VPN or WAN, expect higher latency. Ingest throughput varies with concurrency setting; the published benchmark uses `-c 1` (sequential) for maximum accuracy.

**Expected variance:**
- Same LAN segment as Tilores instance: throughput within ~20% of published LAN figures
- VPN or cloud-to-cloud: throughput will be lower; accuracy metrics are unaffected

Accuracy (F1 / Precision / Recall) is entirely network-independent. If your accuracy differs by more than ±0.001 from the published values using the same seed and config, open an issue.

---

## Numbers Don't Reproduce at All

**Symptom:** F1 is significantly different (>0.01) from published results.

**Checklist:**
1. Did you use `seed=42` in `generate_febrl_data.py`? (It is hardcoded — this should not vary.)
2. Did you use the exact `rule-config.json` from `benchmark/tilores_configs/febrl/`?
3. Is your Splink version ≥ 4.0? (`pip show splink | grep Version`)
4. Did you run the full 1M-record dataset, not a subsample?

If all of the above are true and numbers still diverge, open an issue with your full output. We treat reproducibility failures as high-priority bugs.

---

## batch-graphql Not Found

**Symptom:** `EnvironmentError: batch-graphql CLI not found`

**Fix:**
```bash
# Requires Go 1.21+
go install github.com/tilotech/batch-graphql@latest

# Add Go bin to PATH
export PATH="$PATH:$(go env GOPATH)/bin"

# Verify
batch-graphql --version
```
