import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
)

DATA = "benchmark/data/matching_features.csv"

print("Loading features...")
df = pd.read_csv(DATA)

feature_columns = [
    "first_name_similarity",
    "last_name_similarity",
    "address_similarity",
    "email_similarity",
    "phone_similarity",
    "dob_similarity",
    "postcode_similarity",
]

X = df[feature_columns]
y = df["label"]

# Same split as before
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)

print("\nTraining model...")

model = RandomForestClassifier(
    n_estimators=200,
    max_depth=12,
    random_state=42,
    n_jobs=-1,
    class_weight="balanced",
)

model.fit(X_train, y_train)

# Probability that pair is SAME CUSTOMER
probabilities = model.predict_proba(X_test)[:, 1]

print("\n===================================")
print("PROBABILITY DISTRIBUTION")
print("===================================")

positive_probs = probabilities[y_test.values == 1]
negative_probs = probabilities[y_test.values == 0]

print("\nTRUE MATCHES:")
print(f"Minimum: {positive_probs.min():.4f}")
print(f"25%:     {np.percentile(positive_probs, 25):.4f}")
print(f"Median:  {np.median(positive_probs):.4f}")
print(f"75%:     {np.percentile(positive_probs, 75):.4f}")
print(f"Maximum: {positive_probs.max():.4f}")

print("\nNON-MATCHES:")
print(f"Minimum: {negative_probs.min():.4f}")
print(f"25%:     {np.percentile(negative_probs, 25):.4f}")
print(f"Median:  {np.median(negative_probs):.4f}")
print(f"75%:     {np.percentile(negative_probs, 75):.4f}")
print(f"Maximum: {negative_probs.max():.4f}")


# --------------------------------------------------
# Threshold analysis
# --------------------------------------------------

print("\n===================================")
print("THRESHOLD ANALYSIS")
print("===================================")

print(
    f"{'Threshold':<12}"
    f"{'Precision':<12}"
    f"{'Recall':<12}"
    f"{'F1':<12}"
    f"{'Matches':<12}"
)

for threshold in [
    0.50,
    0.60,
    0.70,
    0.80,
    0.85,
    0.90,
    0.95,
]:
    predictions = (probabilities >= threshold).astype(int)

    precision = precision_score(
        y_test,
        predictions,
        zero_division=0,
    )

    recall = recall_score(
        y_test,
        predictions,
        zero_division=0,
    )

    f1 = f1_score(
        y_test,
        predictions,
        zero_division=0,
    )

    matches = predictions.sum()

    print(
        f"{threshold:<12.2f}"
        f"{precision:<12.4f}"
        f"{recall:<12.4f}"
        f"{f1:<12.4f}"
        f"{matches:<12,}"
    )