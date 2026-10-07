import pandas as pd
import re
from rapidfuzz.fuzz import ratio

RECORDS = "benchmark/data/records.csv"
GROUND_TRUTH = "benchmark/data/ground_truth.csv"

print("Loading data...")

df = pd.read_csv(RECORDS, dtype=str).fillna("")
truth = pd.read_csv(GROUND_TRUTH, dtype=str)

df = df.set_index("record_id")

# --------------------------------------------------
# Normalization
# --------------------------------------------------

def normalize_text(value):
    value = str(value).lower().strip()
    value = re.sub(r"[^a-z0-9]", "", value)
    return value


def normalize_phone(value):
    return re.sub(r"\D", "", str(value))


def normalize_email(value):
    return str(value).lower().strip()


def exact_similarity(a, b):
    if not a or not b:
        return 0.0
    return float(a == b)


def fuzzy_similarity(a, b):
    if not a or not b:
        return 0.0
    return ratio(a, b) / 100.0


# --------------------------------------------------
# Generate candidate pairs
# --------------------------------------------------

print("Generating candidate pairs...")

strategies = [
    ["city", "email"],
    ["city", "phone"],
    ["city", "postcode"],
    ["city", "first_name"],
    ["city", "last_name"],
]

candidate_pairs = set()

for columns in strategies:

    print("Blocking:", " + ".join(columns))

    for _, group in df.reset_index().groupby(columns, dropna=False):

        ids = group["record_id"].tolist()

        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):

                pair = tuple(sorted((ids[i], ids[j])))
                candidate_pairs.add(pair)

print(f"Total candidate pairs: {len(candidate_pairs):,}")


# --------------------------------------------------
# Ground truth
# --------------------------------------------------

truth_pairs = {
    tuple(sorted((a, b)))
    for a, b in zip(
        truth["record_id_1"],
        truth["record_id_2"]
    )
}


# --------------------------------------------------
# Feature generation
# --------------------------------------------------

print("Generating similarity features...")

rows = []

for index, (id1, id2) in enumerate(candidate_pairs):

    if index % 25_000 == 0:
        print(f"Processed {index:,} / {len(candidate_pairs):,}")

    a = df.loc[id1]
    b = df.loc[id2]

    first_name_a = normalize_text(a["first_name"])
    first_name_b = normalize_text(b["first_name"])

    last_name_a = normalize_text(a["last_name"])
    last_name_b = normalize_text(b["last_name"])

    address_a = normalize_text(a["street_address"])
    address_b = normalize_text(b["street_address"])

    email_a = normalize_email(a["email"])
    email_b = normalize_email(b["email"])

    phone_a = normalize_phone(a["phone"])
    phone_b = normalize_phone(b["phone"])

    dob_a = normalize_text(a["date_of_birth"])
    dob_b = normalize_text(b["date_of_birth"])

    postcode_a = normalize_text(a["postcode"])
    postcode_b = normalize_text(b["postcode"])

    row = {
        "record_id_1": id1,
        "record_id_2": id2,

        "first_name_similarity":
            fuzzy_similarity(first_name_a, first_name_b),

        "last_name_similarity":
            fuzzy_similarity(last_name_a, last_name_b),

        "address_similarity":
            fuzzy_similarity(address_a, address_b),

        "email_similarity":
            exact_similarity(email_a, email_b),

        "phone_similarity":
            exact_similarity(phone_a, phone_b),

        "dob_similarity":
            exact_similarity(dob_a, dob_b),

        "postcode_similarity":
            exact_similarity(postcode_a, postcode_b),

        "city_similarity":
            exact_similarity(
                normalize_text(a["city"]),
                normalize_text(b["city"])
            ),

        "label":
            int((id1, id2) in truth_pairs)
    }

    rows.append(row)


# --------------------------------------------------
# Save
# --------------------------------------------------

features = pd.DataFrame(rows)

features.to_csv(
    "benchmark/data/matching_features.csv",
    index=False
)

print("\n===================================")
print("FEATURE GENERATION COMPLETE")
print("===================================")

print(f"Candidate pairs: {len(features):,}")
print(f"Positive matches: {features['label'].sum():,}")
print(
    f"Negative matches: "
    f"{(features['label'] == 0).sum():,}"
)

print("\nFeature columns:")
print(features.columns.tolist())

print("\nSample:")
print(features.head())