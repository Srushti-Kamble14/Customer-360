import pandas as pd

RECORDS = "benchmark/data/records.csv"
GROUND_TRUTH = "benchmark/data/ground_truth.csv"

print("Loading data...")

records = pd.read_csv(RECORDS)
truth = pd.read_csv(GROUND_TRUTH)

# Create lookup by record_id
records = records.set_index("record_id")

# Get the two records for every known duplicate pair
left = records.loc[truth["record_id_1"]]
right = records.loc[truth["record_id_2"]]

fields = [
    "first_name",
    "last_name",
    "date_of_birth",
    "street_address",
    "city",
    "postcode",
    "phone",
    "email",
]

print("\n=== DUPLICATE PAIR ANALYSIS ===")
print(f"Total known duplicate pairs: {len(truth):,}\n")

for field in fields:
    a = left[field].fillna("").astype(str).reset_index(drop=True)
    b = right[field].fillna("").astype(str).reset_index(drop=True)

    same = (a == b).sum()
    different = len(a) - same

    print(
        f"{field:16} "
        f"same: {same:>7,} ({same/len(a)*100:6.2f}%)   "
        f"different/missing: {different:>7,} ({different/len(a)*100:6.2f}%)"
    )

print("\n=== MISSING VALUES IN DUPLICATES ===")

for field in fields:
    missing_left = left[field].isna().sum()
    missing_right = right[field].isna().sum()

    print(
        f"{field:16} "
        f"left missing: {missing_left:>6,}   "
        f"right missing: {missing_right:>6,}"
    )