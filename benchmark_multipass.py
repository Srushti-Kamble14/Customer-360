import pandas as pd

RECORDS = "benchmark/data/records.csv"
GROUND_TRUTH = "benchmark/data/ground_truth.csv"

print("Loading data...")

df = pd.read_csv(RECORDS, dtype=str).fillna("")
truth = pd.read_csv(GROUND_TRUTH, dtype=str)

# --------------------------------------------------
# Create candidate pairs for one blocking strategy
# --------------------------------------------------

def get_candidates(columns):
    groups = df.groupby(columns, dropna=False)

    candidates = set()

    for _, group in groups:
        ids = group["record_id"].tolist()

        # Generate all pairs inside this block
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                candidates.add((ids[i], ids[j]))

    return candidates


strategies = {
    "City + Email": ["city", "email"],
    "City + Phone": ["city", "phone"],
    "City + Postcode": ["city", "postcode"],
    "City + First Name": ["city", "first_name"],
    "City + Last Name": ["city", "last_name"],
}

# --------------------------------------------------
# Run each blocking pass
# --------------------------------------------------

all_candidates = set()

print("\n=== MULTI-PASS BLOCKING ===")

for name, columns in strategies.items():

    print(f"\nRunning: {name}")

    candidates = get_candidates(columns)

    print(f"Candidates: {len(candidates):,}")

    all_candidates.update(candidates)

    print(
        f"Combined candidates so far: "
        f"{len(all_candidates):,}"
    )


# --------------------------------------------------
# Evaluate recall
# --------------------------------------------------

truth_pairs = set(
    zip(
        truth["record_id_1"],
        truth["record_id_2"]
    )
)

# Ground truth pairs are oriented the same way,
# but normalize them just in case.
truth_pairs_normalized = {
    tuple(sorted(pair))
    for pair in truth_pairs
}

candidate_pairs_normalized = {
    tuple(sorted(pair))
    for pair in all_candidates
}

captured = len(
    truth_pairs_normalized &
    candidate_pairs_normalized
)

total = len(truth_pairs_normalized)

recall = captured / total * 100

# --------------------------------------------------
# Compare with all-vs-all
# --------------------------------------------------

n = len(df)

all_pairs = n * (n - 1) // 2

reduction = (
    1 -
    len(all_candidates) / all_pairs
) * 100


print("\n====================================")
print("FINAL MULTI-PASS RESULTS")
print("====================================")

print(f"Total records:             {n:,}")
print(f"All possible pairs:        {all_pairs:,}")
print(f"Candidate pairs:           {len(all_candidates):,}")
print(f"True duplicates captured:  {captured:,}")
print(f"Blocking recall:           {recall:.2f}%")
print(f"Pair reduction:            {reduction:.6f}%")