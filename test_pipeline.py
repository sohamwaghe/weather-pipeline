import os
import psycopg2
import time
import sys

def verify_pipeline():
    print("🚀 Starting Pipeline Verification...")
    
    # 1. Check if DB is reachable
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "postgres"),
            database=os.getenv("POSTGRES_DB", "weather_db"),
            user=os.getenv("POSTGRES_USER", "Airflow"),
            password=os.getenv("POSTGRES_PASSWORD", "Airflow"),
            port=os.getenv("POSTGRES_PORT", "5432")
        )
        print("✅ Database Connection: SUCCESS")
    except Exception as e:
        print(f"❌ Database Connection: FAILED - {e}")
        return False

    # 2. Check for existence of schemas
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name IN ('raw', 'analytics');")
            schemas = [r[0] for r in cur.fetchall()]
            if 'raw' in schemas:
                print("✅ Schema 'raw': FOUND")
            else:
                print("❌ Schema 'raw': MISSING")
                return False
                
            if 'analytics' in schemas:
                print("✅ Schema 'analytics': FOUND")
            else:
                print("⚠️ Schema 'analytics': MISSING (Expected if dbt hasn't run yet)")
    except Exception as e:
        print(f"❌ Schema Verification: FAILED - {e}")
        return False

    print("🏁 Verification Complete!")
    return True

if __name__ == "__main__":
    success = verify_pipeline()
    if not success:
        sys.exit(1)
    sys.exit(0)
