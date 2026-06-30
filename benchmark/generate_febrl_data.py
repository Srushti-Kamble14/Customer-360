"""
Generate a synthetic FEBRL-style dataset for the Splink vs. Tilores benchmark.

This script creates:
  - records.csv         : ~1M records with injected duplicates
  - ground_truth.csv    : known duplicate pairs (record_id_1, record_id_2)

Dataset design:
  - 900,000 unique entities
  - ~100,000 duplicate records (one duplicate per ~9th entity → ~10% duplicate rate)
  - Duplicates have realistic noise: typos, swapped name components, missing fields

Usage:
  python benchmark/generate_febrl_data.py

Output files:
  benchmark/data/records.csv
  benchmark/data/ground_truth.csv
"""

import os
import csv
import random
import string
from faker import Faker

SEED = 42
NUM_ENTITIES = 900_000
NUM_DUPLICATES = 100_000   # one duplicate every ~9 entities
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data")

fake = Faker("en_GB")
Faker.seed(SEED)
random.seed(SEED)


def corrupt_string(s: str, corruption_rate: float = 0.15) -> str:
    """Introduce realistic typos into a string."""
    if not s or random.random() > corruption_rate:
        return s
    chars = list(s)
    op = random.choice(["swap", "delete", "insert", "replace"])
    if len(chars) < 2:
        return s
    i = random.randint(0, len(chars) - 1)
    if op == "swap" and i < len(chars) - 1:
        chars[i], chars[i + 1] = chars[i + 1], chars[i]
    elif op == "delete":
        del chars[i]
    elif op == "insert":
        chars.insert(i, random.choice(string.ascii_lowercase))
    elif op == "replace":
        chars[i] = random.choice(string.ascii_lowercase)
    return "".join(chars)


def corrupt_date(dob: str) -> str:
    """Shift day or month by ±1 to simulate transposition errors."""
    try:
        parts = dob.split("-")
        if len(parts) != 3:
            return dob
        year, month, day = parts
        field = random.choice(["day", "month"])
        if field == "day":
            day = str(max(1, min(28, int(day) + random.choice([-1, 1])))).zfill(2)
        else:
            month = str(max(1, min(12, int(month) + random.choice([-1, 1])))).zfill(2)
        return f"{year}-{month}-{day}"
    except (ValueError, IndexError):
        return dob


def make_record(entity_id: str, is_duplicate: bool = False, base: dict = None) -> dict:
    """Generate a single record. If is_duplicate, corrupt the base record."""
    if not is_duplicate:
        first = fake.first_name()
        last = fake.last_name()
        dob = fake.date_of_birth(minimum_age=18, maximum_age=90).strftime("%Y-%m-%d")
        street = fake.street_address()
        city = fake.city()
        postcode = fake.postcode()
        phone = fake.phone_number()[:15]
        email = f"{first.lower()}.{last.lower()}@{fake.free_email_domain()}"
        return {
            "record_id": entity_id,
            "entity_id": entity_id,
            "first_name": first,
            "last_name": last,
            "date_of_birth": dob,
            "street_address": street,
            "city": city,
            "postcode": postcode,
            "phone": phone,
            "email": email,
        }
    else:
        # Corrupt 1–3 fields from the base record
        rec = base.copy()
        dup_id = entity_id + "_dup"
        rec["record_id"] = dup_id
        fields_to_corrupt = random.sample(
            ["first_name", "last_name", "date_of_birth", "street_address", "postcode", "phone"],
            k=random.randint(1, 3),
        )
        for field in fields_to_corrupt:
            if field == "date_of_birth":
                rec[field] = corrupt_date(rec[field])
            elif field == "phone":
                rec[field] = corrupt_string(rec[field], corruption_rate=1.0)
            else:
                rec[field] = corrupt_string(rec[field], corruption_rate=1.0)
        # Occasionally blank out a field entirely
        if random.random() < 0.1:
            rec[random.choice(["phone", "email", "street_address"])] = ""
        return rec


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    records_path = os.path.join(OUTPUT_DIR, "records.csv")
    truth_path = os.path.join(OUTPUT_DIR, "ground_truth.csv")

    fieldnames = [
        "record_id", "entity_id", "first_name", "last_name",
        "date_of_birth", "street_address", "city", "postcode", "phone", "email",
    ]

    # Determine which entities get a duplicate
    dup_entity_indices = set(random.sample(range(NUM_ENTITIES), NUM_DUPLICATES))

    print(f"Generating {NUM_ENTITIES} base records + {NUM_DUPLICATES} duplicates...")
    total = 0

    with open(records_path, "w", newline="", encoding="utf-8") as rf, \
         open(truth_path, "w", newline="", encoding="utf-8") as tf:

        writer = csv.DictWriter(rf, fieldnames=fieldnames)
        writer.writeheader()

        truth_writer = csv.writer(tf)
        truth_writer.writerow(["record_id_1", "record_id_2"])

        for i in range(NUM_ENTITIES):
            entity_id = f"E{i:07d}"
            base = make_record(entity_id)
            writer.writerow(base)
            total += 1

            if i in dup_entity_indices:
                dup = make_record(entity_id, is_duplicate=True, base=base)
                writer.writerow(dup)
                truth_writer.writerow([entity_id, dup["record_id"]])
                total += 1

            if (i + 1) % 100_000 == 0:
                print(f"  {i + 1:,} entities processed ({total:,} records written)...")

    print(f"\nDone. Total records: {total:,}")
    print(f"Records written to : {records_path}")
    print(f"Ground truth written to: {truth_path}")


if __name__ == "__main__":
    main()
