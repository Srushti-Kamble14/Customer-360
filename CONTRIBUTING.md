# Contributing

This benchmark is published in the spirit of reproducibility. Contributions that improve clarity, fairness, or reproducibility are welcome.

---

## Reporting Reproducibility Issues

If the numbers don't match on your hardware, open an issue with:

1. Your machine specs (CPU, RAM, OS, Python version, Splink version)
2. The exact command you ran
3. The output you observed vs. the expected output in `RESULTS.md`
4. Whether you used the pre-generated data or regenerated it from scratch

We commit to investigating and responding within 48 hours of a reproducibility report.

---

## Proposing Tuning Improvements

The Splink configuration in this benchmark is our best-effort attempt at a fair comparison. If you know a better Splink configuration that would improve F1 without overfitting to the FEBRL dataset, we want to know.

**How to propose:**
1. Open an issue describing the proposed change (which parameters, why)
2. Include the F1/Precision/Recall you achieved
3. We will re-run with your suggested config, publish the result in a `RUN-N.md` addendum, and credit you in the file

We will not cherry-pick configs that favour Tilores. If your Splink config beats the current Tilores result, that goes in the repo too.

---

## Submitting Additional Datasets

We are interested in benchmarks on datasets beyond FEBRL:
- Splink's canonical `fake_1000` / `febrl4` datasets
- Other public entity resolution datasets with known ground truth

Open an issue to discuss before implementing. Large data files should not be committed to the repo — instead, provide a generator or fetch script (like `generate_febrl_data.py`).

---

## Code of Conduct

Be direct and technical. Critique the benchmark, not the people. We will engage constructively with criticism from the Splink community, including criticism that is uncomfortable.

If you experience harassment, contact [hello@tilores.io](mailto:hello@tilores.io).

---

## What We Will Not Merge

- Changes that remove the honest trade-off section from README.md
- Configs tuned on the ground-truth data (leakage)
- Benchmark-gaming (e.g., choosing a different match threshold post-hoc to improve numbers)
