import os
import sys
import psycopg2
from psycopg2 import sql
import time

# Get database connection details from environment variables
# In Docker, these are injected from .env
# If running locally, make sure these are set in your environment
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_NAME = os.getenv("POSTGRES_DB", "weather_db")
DB_USER = os.getenv("POSTGRES_USER", "airflow")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "airflow")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

def wait_for_db(retries=5, delay=2):
    """Wait for database to become available"""
    print(f"Connecting to database {DB_NAME} at {DB_HOST}:{DB_PORT}...")
    
    for i in range(retries):
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASS,
                port=DB_PORT
            )
            print("✅ Successfully connected to PostgreSQL!")
            return conn
        except psycopg2.OperationalError as e:
            print(f"⚠️ Connection failed (attempt {i+1}/{retries}): {e}")
            time.sleep(delay)
    
    print("❌ Could not connect to database after multiple attempts.")
    sys.exit(1)

def check_schemas(cur):
    """Verify that required schemas exist"""
    required_schemas = ['raw', 'staging', 'analytics']
    missing = []
    
    print("\nChecking schemas...")
    for schema in required_schemas:
        cur.execute(
            "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
            (schema,)
        )
        if cur.fetchone():
            print(f"  ✅ Schema '{schema}' exists")
        else:
            print(f"  ❌ Schema '{schema}' MISSING")
            missing.append(schema)
            
    return len(missing) == 0

def check_tables(cur):
    """Verify that key tables exist"""
    required_tables = [('raw', 'weather_data')]
    missing = []
    
    print("\nChecking tables...")
    for schema, table in required_tables:
        cur.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = %s
            """,
            (schema, table)
        )
        if cur.fetchone():
            print(f"  ✅ Table '{schema}.{table}' exists")
        else:
            print(f"  ❌ Table '{schema}.{table}' MISSING")
            missing.append(f"{schema}.{table}")
            
    return len(missing) == 0

def main():
    conn = wait_for_db()
    
    try:
        cur = conn.cursor()
        
        schemas_ok = check_schemas(cur)
        tables_ok = check_tables(cur)
        
        print("\n" + "="*50)
        if schemas_ok and tables_ok:
            print("🎉 SYSTEM CHECK PASSED: Database is correctly initialized!")
            sys.exit(0)
        else:
            print("💥 SYSTEM CHECK FAILED: Database initialization is incomplete.")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ An error occurred during verification: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
