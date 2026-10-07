import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

DATA = "benchmark/data/matching_features.csv"

print("Loading features...")

df = pd.read_csv(DATA)

# We don't need IDs as ML features
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

print(f"Total samples: {len(df):,}")
print(f"Positive samples: {y.sum():,}")
print(f"Negative samples: {(y == 0).sum():,}")

# --------------------------------------------------
# Train / Test split
# --------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print(f"\nTraining samples: {len(X_train):,}")
print(f"Testing samples:  {len(X_test):,}")

# --------------------------------------------------
# Random Forest
# --------------------------------------------------

print("\nTraining Random Forest...")

model = RandomForestClassifier(
    n_estimators=200,
    max_depth=12,
    random_state=42,
    n_jobs=-1,
    class_weight="balanced"
)

model.fit(X_train, y_train)

print("Training complete.")

# --------------------------------------------------
# Predictions
# --------------------------------------------------

predictions = model.predict(X_test)

probabilities = model.predict_proba(X_test)[:, 1]

# --------------------------------------------------
# Evaluation
# --------------------------------------------------

accuracy = accuracy_score(y_test, predictions)
precision = precision_score(y_test, predictions)
recall = recall_score(y_test, predictions)
f1 = f1_score(y_test, predictions)

print("\n===================================")
print("MODEL RESULTS")
print("===================================")

print(f"Accuracy:  {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall:    {recall:.4f}")
print(f"F1 Score:  {f1:.4f}")

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, predictions))

print("\nClassification Report:")
print(classification_report(y_test, predictions))

# --------------------------------------------------
# Feature importance
# --------------------------------------------------

print("\n=== FEATURE IMPORTANCE ===")

importance = pd.Series(
    model.feature_importances_,
    index=feature_columns
).sort_values(ascending=False)

print(importance)