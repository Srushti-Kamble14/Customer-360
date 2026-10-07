import redis
import json
import time
from fastapi import FastAPI, HTTPException
import psycopg2
import os
from urllib.parse import quote
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Customer 360 API",
    description="Customer Master Data Management API",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --------------------------------------------------
# DATABASE CONFIG
# --------------------------------------------------

PASSWORD = os.getenv("SUPABASE_PASSWORD")
encoded_password = quote(PASSWORD, safe="")

DATABASE_URL = (
    f"postgresql://postgres:{encoded_password}"
    "@db.xgejqqytmwnkrwrxnzxl.supabase.co:5432/postgres"
)

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_USERNAME = os.getenv("REDIS_USERNAME", "default")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    username=REDIS_USERNAME,
    password=REDIS_PASSWORD,
    decode_responses=True,
    ssl=False,
    max_connections=20
)


def get_connection():
    return psycopg2.connect(DATABASE_URL)


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Customer 360 API is running",
        "status": "healthy"
    }

@app.get("/redis-test")
def redis_test():

    redis_client.set(
        "customer360:test",
        "Redis is working!",
        ex=60
    )

    value = redis_client.get("customer360:test")

    return {
        "redis": value
    }

# --------------------------------------------------
# SEARCH CUSTOMERS
# --------------------------------------------------

@app.get("/customers/search")
def search_customers(
    email: str | None = None,
    phone: str | None = None,
    name: str | None = None,
    postcode: str | None = None
):
    if not any([email, phone, name, postcode]):
        raise HTTPException(
            status_code=400,
            detail="Provide email, phone, name, or postcode"
        )

    conn = get_connection()
    cur = conn.cursor()

    conditions = []
    params = []

    if email:
        conditions.append("LOWER(email) = LOWER(%s)")
        params.append(email)

    if phone:
        conditions.append("phone = %s")
        params.append(phone)

    if name:
        conditions.append(
            """
            LOWER(first_name || ' ' || last_name)
            LIKE LOWER(%s)
            """
        )
        params.append(f"%{name}%")

    if postcode:
        conditions.append("LOWER(postcode) = LOWER(%s)")
        params.append(postcode)

    query = f"""
        SELECT
            master_customer_id,
            first_name,
            last_name,
            date_of_birth,
            street_address,
            city,
            postcode,
            phone,
            email,
            source_record_count
        FROM master_customers
        WHERE {" AND ".join(conditions)}
        LIMIT 20
    """

    cur.execute(query, params)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return {
        "count": len(rows),
        "results": [
            {
                "master_customer_id": row[0],
                "first_name": row[1],
                "last_name": row[2],
                "date_of_birth": row[3],
                "street_address": row[4],
                "city": row[5],
                "postcode": row[6],
                "phone": row[7],
                "email": row[8],
                "source_record_count": row[9]
            }
            for row in rows
        ]
    }

# --------------------------------------------------
# GET CUSTOMER 360
# --------------------------------------------------

@app.get("/customers/{master_customer_id}")
def get_customer(master_customer_id: str):

    cache_key = f"customer360:{master_customer_id}"

    # ==========================================
    # 1. CHECK REDIS
    # ==========================================

    cached_customer = redis_client.get(cache_key)

    if cached_customer:

        print(f"⚡ CACHE HIT: {master_customer_id}")

        customer = json.loads(cached_customer)

        customer["cache"] = "redis"

        return customer

    print(f"🐘 CACHE MISS: {master_customer_id}")

    # ==========================================
    # 2. CACHE MISS → QUERY SUPABASE
    # ==========================================

    conn = get_connection()
    cur = conn.cursor()

    start_time = time.perf_counter()

    cur.execute(
        """
        SELECT
            master_customer_id,
            first_name,
            last_name,
            date_of_birth,
            street_address,
            city,
            postcode,
            phone,
            email,
            source_record_ids,
            source_record_count
        FROM master_customers
        WHERE master_customer_id = %s
        """,
        (master_customer_id,)
    )

    customer = cur.fetchone()

    db_time = time.perf_counter() - start_time

    cur.close()
    conn.close()

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    result = {
        "master_customer_id": customer[0],
        "first_name": customer[1],
        "last_name": customer[2],
        "date_of_birth": str(customer[3]) if customer[3] else None,
        "street_address": customer[4],
        "city": customer[5],
        "postcode": customer[6],
        "phone": customer[7],
        "email": customer[8],
        "source_record_ids": (
            customer[9].split(",")
            if customer[9]
            else []
        ),
        "source_record_count": customer[10],
        "cache": "database",
        "db_time_ms": round(db_time * 1000, 3)
    }

    # ==========================================
    # 3. STORE RESULT IN REDIS
    # ==========================================

    redis_data = {
        key: value
        for key, value in result.items()
        if key not in ["cache", "db_time_ms"]
    }

    redis_client.set(
        cache_key,
        json.dumps(redis_data),
        ex=300
    )

    return result


@app.get("/benchmark/cache/{master_customer_id}")
def benchmark_cache(master_customer_id: str):

    cache_key = f"customer360:{master_customer_id}"

    # -----------------------------
    # DATABASE TIME
    # -----------------------------
    conn = get_connection()
    cur = conn.cursor()

    start = time.perf_counter()

    cur.execute(
        """
        SELECT
            master_customer_id,
            first_name,
            last_name,
            email
        FROM master_customers
        WHERE master_customer_id = %s
        """,
        (master_customer_id,)
    )

    db_result = cur.fetchone()

    db_time = time.perf_counter() - start

    cur.close()
    conn.close()

    if not db_result:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    # -----------------------------
    # REDIS TIME
    # -----------------------------
    start = time.perf_counter()

    redis_result = redis_client.get(cache_key)

    redis_time = time.perf_counter() - start

    return {
        "master_customer_id": master_customer_id,
        "database_time_ms": round(db_time * 1000, 3),
        "redis_time_ms": round(redis_time * 1000, 3),
        "redis_cached": redis_result is not None,
        "speedup": round(
            db_time / redis_time,
            2
        ) if redis_time > 0 else None
    }