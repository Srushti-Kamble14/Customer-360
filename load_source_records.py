import psycopg2

from urllib.parse import quote

PASSWORD = "EY?yNuauni62%6r"
encoded_password = quote(PASSWORD, safe="")

DATABASE_URL = (
    f"postgresql://postgres:{encoded_password}"
    "@db.xgejqqytmwnkrwrxnzxl.supabase.co:5432/postgres"
)

CSV_FILE = "benchmark/data/records.csv"

print("Connecting to Supabase...")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

print("Connected!")
print("Loading 1M source records...")

with open(CSV_FILE, "r", encoding="utf-8") as f:
    cur.copy_expert(
        """
        COPY source_records (
            record_id,
            entity_id,
            first_name,
            last_name,
            date_of_birth,
            street_address,
            city,
            postcode,
            phone,
            email
        )
        FROM STDIN
        WITH CSV HEADER
        NULL ''
        """,
        f
    )

conn.commit()

print("========================================")
print("SOURCE RECORD IMPORT COMPLETE")
print("========================================")

cur.close()
conn.close()