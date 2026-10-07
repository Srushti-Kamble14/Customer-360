import pandas as pd

RECORDS = "benchmark/data/records.csv"
GROUND_TRUTH = "benchmark/data/ground_truth.csv"

print("Loading records...")
df = pd.read_csv(RECORDS)

print(f"Records: {len(df):,}")

# --------------------------------------------------
# Helper: count candidate pairs produced by a block
# --------------------------------------------------

def count_pairs(block_columns):
    sizes = df.groupby(block_columns, dropna=False).size()

    # For a block containing n records:
    # number of possible pairs = n * (n - 1) / 2
    pairs = (sizes * (sizes - 1) // 2).sum()

    return pairs


strategies = {
    "City": ["city"],
    "City + Postcode": ["city", "postcode"],
    "City + First Name": ["city", "first_name"],
    "City + Last Name": ["city", "last_name"],
    "City + Email": ["city", "email"],
    "City + Phone": ["city", "phone"],
}

print("\n=== BLOCKING COMPARISON ===")

for name, columns in strategies.items():
    pairs = count_pairs(columns)

    print(
        f"{name:22} "
        f"{pairs:>15,} candidate pairs"
    )

# --------------------------------------------------
# Theoretical all-vs-all comparisons
# --------------------------------------------------

n = len(df)
all_pairs = n * (n - 1) // 2

print("\n=== BASELINE ===")
print(f"All-vs-all pairs: {all_pairs:,}")

print("\n=== REDUCTION ===")

for name, columns in strategies.items():
    pairs = count_pairs(columns)

    reduction = (1 - pairs / all_pairs) * 100

    print(
        f"{name:22} "
        f"reduces comparisons by {reduction:.4f}%"
    )