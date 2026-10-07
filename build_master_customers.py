import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier


FEATURES = "benchmark/data/matching_features.csv"
RECORDS = "benchmark/data/records.csv"
OUTPUT = "benchmark/data/customer_record_mapping.csv"

FEATURE_COLUMNS = [
    "first_name_similarity",
    "last_name_similarity",
    "address_similarity",
    "email_similarity",
    "phone_similarity",
    "dob_similarity",
    "postcode_similarity",
]

MATCH_THRESHOLD = 0.90


# ==================================================
# 1. LOAD DATA
# ==================================================

print("Loading features...")
df = pd.read_csv(FEATURES)

print("Loading all records...")
records = pd.read_csv(
    RECORDS,
    usecols=["record_id"],
    dtype=str
)

print(f"Total source records: {len(records):,}")


# ==================================================
# 2. TRAIN MODEL
# ==================================================

X = df[FEATURE_COLUMNS]
y = df["label"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("\nTraining Random Forest...")

model = RandomForestClassifier(
    n_estimators=200,
    max_depth=12,
    random_state=42,
    n_jobs=-1,
    class_weight="balanced"
)

model.fit(X_train, y_train)

print("Model trained.")


# ==================================================
# 3. PREDICT ALL CANDIDATE PAIRS
# ==================================================

print("\nCalculating match probabilities...")

df["match_probability"] = model.predict_proba(X)[:, 1]

matches = df[
    df["match_probability"] >= MATCH_THRESHOLD
].copy()

print(f"Candidate pairs:    {len(df):,}")
print(f"Confirmed matches:  {len(matches):,}")


# ==================================================
# 4. UNION-FIND
# ==================================================

print("\nBuilding customer groups...")


class UnionFind:

    def __init__(self):
        self.parent = {}
        self.rank = {}

    def add(self, x):

        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0

    def find(self, x):

        if self.parent[x] != x:
            self.parent[x] = self.find(
                self.parent[x]
            )

        return self.parent[x]

    def union(self, a, b):

        self.add(a)
        self.add(b)

        root_a = self.find(a)
        root_b = self.find(b)

        if root_a == root_b:
            return

        if self.rank[root_a] < self.rank[root_b]:

            self.parent[root_a] = root_b

        elif self.rank[root_a] > self.rank[root_b]:

            self.parent[root_b] = root_a

        else:

            self.parent[root_b] = root_a
            self.rank[root_a] += 1


uf = UnionFind()


# ==================================================
# 5. IMPORTANT:
#    ADD ALL 1M RECORDS
# ==================================================

print("Adding all records to customer groups...")

for record_id in records["record_id"]:

    uf.add(record_id)


print(
    f"Records registered: "
    f"{len(uf.parent):,}"
)


# ==================================================
# 6. CONNECT MATCHED RECORDS
# ==================================================

print("Connecting matched records...")

for _, row in matches.iterrows():

    uf.union(
        row["record_id_1"],
        row["record_id_2"]
    )


# ==================================================
# 7. BUILD GROUPS
# ==================================================

print("Building final customer groups...")

groups = {}

for record_id in uf.parent:

    root = uf.find(record_id)

    if root not in groups:
        groups[root] = []

    groups[root].append(record_id)


# ==================================================
# 8. ASSIGN MASTER CUSTOMER IDs
# ==================================================

print("Assigning master customer IDs...")

mapping_rows = []

counter = 1

for root, record_ids in groups.items():

    master_id = f"C{counter:06d}"

    for record_id in record_ids:

        mapping_rows.append({
            "record_id": record_id,
            "master_customer_id": master_id
        })

    counter += 1


mapping = pd.DataFrame(mapping_rows)


# ==================================================
# 9. SAVE
# ==================================================

mapping.to_csv(
    OUTPUT,
    index=False
)


# ==================================================
# 10. RESULTS
# ==================================================

print("\n===================================")
print("CUSTOMER 360 GROUPING COMPLETE")
print("===================================")

print(
    f"Total source records: "
    f"{len(records):,}"
)

print(
    f"Records in mapping:   "
    f"{len(mapping):,}"
)

print(
    f"Master customers:     "
    f"{mapping['master_customer_id'].nunique():,}"
)

print(
    f"Confirmed matches:    "
    f"{len(matches):,}"
)

print("\nSample mapping:")
print(mapping.head(20))

print(f"\nSaved to: {OUTPUT}")