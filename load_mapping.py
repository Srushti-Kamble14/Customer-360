import psycopg2
from urllib.parse import quote

PASSWORD = "EY?yNuauni62%6r"
encoded_password = quote(PASSWORD, safe="")

DATABASE_URL = (
    f"postgresql://postgres:{encoded_password}"
    "@db.xgejqqytmwnkrwrxnzxl.supabase.co:5432/postgres"
)

CSV_FILE = "benchmark/data/customer_record_mapping.csv"

print("Connecting to Supabase...")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

print("Connected!")
print("Loading 1M customer mappings...")

with open(CSV_FILE, "r", encoding="utf-8") as f:
    cur.copy_expert(
        """
        COPY customer_record_mapping (
            record_id,
            master_customer_id
        )
        FROM STDIN
        WITH CSV HEADER
        NULL ''
        """,
        f
    )

conn.commit()

print("========================================")
print("MAPPING IMPORT COMPLETE")
print("========================================")

cur.close()
conn.close()