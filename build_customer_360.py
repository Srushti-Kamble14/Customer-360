import pandas as pd

RECORDS = "benchmark/data/records.csv"
MAPPING = "benchmark/data/customer_record_mapping.csv"
OUTPUT = "benchmark/data/customer_360.csv"

FIELDS = [
    "first_name",
    "last_name",
    "date_of_birth",
    "street_address",
    "city",
    "postcode",
    "phone",
    "email",
]

print("Loading records...")
records = pd.read_csv(RECORDS, dtype=str).fillna("")

print("Loading mapping...")
mapping = pd.read_csv(MAPPING, dtype=str)

print("Joining data...")
df = records.merge(
    mapping,
    on="record_id",
    how="inner"
)

print(f"Records joined: {len(df):,}")

# Empty strings -> missing
for field in FIELDS:
    df[field] = df[field].replace("", pd.NA)

print("Sorting records...")
df = df.sort_values(
    ["master_customer_id", "record_id"]
)

print("Building unified customer profiles...")

# Pick first non-missing value for each customer.
# Since every duplicate group is small, this is much faster
# than calculating mode() for every group.
profile = (
    df.groupby("master_customer_id", sort=False)[FIELDS]
      .first()
      .reset_index()
)

print("Building source record information...")

source_info = (
    df.groupby("master_customer_id", sort=False)
      .agg(
          source_record_ids=("record_id", ",".join),
          source_record_count=("record_id", "size")
      )
      .reset_index()
)

print("Combining profile...")

customer_360 = profile.merge(
    source_info,
    on="master_customer_id",
    how="left"
)

print(f"Master customers: {len(customer_360):,}")

print("Saving Customer 360...")
customer_360.to_csv(
    OUTPUT,
    index=False
)

print()
print("========================================")
print("Customer 360 BUILD COMPLETE")
print("========================================")
print(f"Output: {OUTPUT}")
print(f"Master customers: {len(customer_360):,}")
print(f"Source records: {len(df):,}")
print("========================================")