import pandas as pd

RECORDS = "benchmark/data/records.csv"
GROUND_TRUTH = "benchmark/data/ground_truth.csv"

print("Loading data...")

df = pd.read_csv(RECORDS, dtype=str).fillna("")
truth = pd.read_csv(GROUND_TRUTH, dtype=str)

# Create lookup:
# record_id -> row data
df = df.set_index("record_id")

strategies = {
    "City": ["city"],
    "City + Postcode": ["city", "postcode"],
    "City + First Name": ["city", "first_name"],
    "City + Last Name": ["city", "last_name"],
    "City + Email": ["city", "email"],
    "City + Phone": ["city", "phone"],
}

print("\n=== BLOCKING RECALL ===")

for name, columns in strategies.items():

    # Get both records for every known true duplicate pair
    left = df.loc[truth["record_id_1"], columns].reset_index(drop=True)
    right = df.loc[truth["record_id_2"], columns].reset_index(drop=True)

    # A true pair survives the block if ALL blocking fields match
    matches = (left.values == right.values).all(axis=1)

    captured = matches.sum()
    total = len(truth)
    recall = captured / total * 100

    print(
        f"{name:22} "
        f"captured: {captured:>7,} / {total:,}   "
        f"recall: {recall:6.2f}%"
    )
    