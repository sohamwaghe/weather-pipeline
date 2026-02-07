import os
import psycopg2
import sys
import subprocess
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv('/opt/airflow/.env')

# ANSI Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def print_pass(msg):
    print(f"{GREEN}PASS: {msg}{RESET}")

def print_fail(msg):
    print(f"{RED}FAIL: {msg}{RESET}")

def print_warn(msg):
    print(f"{YELLOW}WARN: {msg}{RESET}")

def check_docker_containers():
    print("\n--- 1. Checking Docker Containers ---")
    # This might fail if run inside a container without docker socket mounted
    # We'll try, but skip if not possible
    try:
        # Check if we are in a docker container? 
        # Easier to checking expected hostnames if inside container
        # If running locally, use docker ps
        
        # Simple check: try to resolve 'postgres' hostname. 
        # If it resolves, we are likely in the network.
        import socket
        try:
            socket.gethostbyname('postgres')
            print_pass("Service 'postgres' is reachable")
        except:
            print_warn("Service 'postgres' not reachable by hostname (are you running inside docker-compose network?)")

    except Exception as e:
        print_warn(f"Could not check containers: {e}")

def check_postgres_connection():
    print("\n--- 2. Checking PostgreSQL Connection ---")
    try:
        # Try getting env vars, default to airflow/airflow for testing inside container
        user = os.getenv('POSTGRES_USER', 'airflow')
        password = os.getenv('POSTGRES_PASSWORD', 'airflow')
        host = os.getenv('POSTGRES_HOST', 'postgres')
        db = os.getenv('POSTGRES_DB', 'weather_db')
        port = os.getenv('POSTGRES_PORT', '5432')

        conn = psycopg2.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database=db
        )
        print_pass("Successfully connected to PostgreSQL")
        return conn
    except Exception as e:
        print_fail(f"Connection failed: {e}")
        return None

def check_schemas(conn):
    print("\n--- 3. Verifying Schemas ---")
    schemas = ['raw', 'staging', 'analytics'] # analytics is usually the marts schema? 
    # In our dbt profile we set schema='staging', so marts might be in 'staging' or configured schema
    # Let's check 'raw' and the default public or configured schemas
    # Actually, we should check for 'raw' and whatever schema dbt writes to.
    # Based on profiles.yml, it writes to 'staging'. 
    # Marts usually go to a separate schema if confirmed, or same. 
    # Let's check for 'raw' and 'public' (default) or 'staging'.
    
    expected_schemas = ['raw', 'public'] 
    
    with conn.cursor() as cur:
        cur.execute("SELECT schema_name FROM information_schema.schemata;")
        existing_schemas = [row[0] for row in cur.fetchall()]
        
        for schema in expected_schemas:
            if schema in existing_schemas:
                print_pass(f"Schema '{schema}' exists")
            else:
                print_warn(f"Schema '{schema}' not found (might be created later)")

def check_data_freshness(conn):
    print("\n--- 4. Checking Data Freshness ---")
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT MAX(api_call_timestamp) 
                FROM raw.weather_data;
            """)
            last_run = cur.fetchone()[0]
            
            if last_run:
                # Assuming timestamp is in Postgres (naive or aware)
                # If naive, assume UTC.
                now = datetime.utcnow()
                # Ensure last_run is offset-naive for comparison if checking against utcnow
                if last_run.tzinfo:
                    last_run = last_run.replace(tzinfo=None)
                
                diff = now - last_run
                if diff < timedelta(hours=2):
                    print_pass(f"Data is fresh! Last run: {last_run} (Age: {diff})")
                else:
                    print_fail(f"Data is stale. Last run: {last_run} (Age: {diff})")
            else:
                print_fail("No data found in raw.weather_data")
    except Exception as e:
        print_fail(f"Error checking freshness: {e}")

def verify_models(conn):
    print("\n--- 5 & 6. Verifying dbt Models ---")
    # Check for table existence in probable schemas (public or staging)
    # dbt default schema is 'staging' as per profiles.yml
    # but dbt projects often write marts to 'staging_marts' or just 'staging'?
    # In `dbt_project.yml`: valid configs.
    # We will look in 'staging' and 'public'.
    
    models = [
        ('staging', 'stg_weather', 'view'),
        ('staging', 'dim_cities', 'table'),
        ('staging', 'dim_time', 'table'),
        ('staging', 'fact_weather', 'table')
    ]
    
    with conn.cursor() as cur:
        for schema, table, kind in models:
            # Check if table/view exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = %s 
                    AND table_name = %s
                );
            """, (schema, table))
            exists = cur.fetchone()[0]
            
            if exists:
                print_pass(f"Model '{schema}.{table}' exists")
            else:
                # Try 'public' schema just in case
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    );
                """, (table,))
                exists_public = cur.fetchone()[0]
                if exists_public:
                    print_pass(f"Model 'public.{table}' exists")
                else:
                    print_fail(f"Model '{table}' NOT found in schema '{schema}' or 'public'")

def run_analytics_query(conn):
    print("\n--- 7. Sample Analytics Query ---")
    query = """
    SELECT 
        c.city_name,
        ROUND(AVG(f.temperature)::numeric, 2) as avg_temp_24h,
        MAX(f.temperature) as max_temp,
        MIN(f.temperature) as min_temp,
        COUNT(*) as readings
    FROM staging.fact_weather f
    JOIN staging.dim_cities c ON f.city_id = c.city_id
    JOIN staging.dim_time t ON f.time_id = t.time_id
    WHERE t.timestamp >= NOW() - INTERVAL '24 hours'
    GROUP BY c.city_name
    ORDER BY avg_temp_24h DESC;
    """
    
    try:
        # Check if pandas is available for pretty printing
        try:
            import pandas as pd
            df = pd.read_sql_query(query, conn)
            if not df.empty:
                print(df.to_string(index=False))
                print_pass("Analytics query executed successfully")
            else:
                print_warn("Analytics query returned no data (pipeline might need to run fully)")
        except ImportError:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
                if rows:
                    print(f"{'City':<15} | {'Avg Temp':<10} | {'Readings':<10}")
                    print("-" * 40)
                    for row in rows:
                        print(f"{row[0]:<15} | {row[1]:<10} | {row[4]:<10}")
                    print_pass("Analytics query executed successfully")
                else:
                    print_warn("1Analytics query returned no data")
    
    except Exception as e:
        print_fail(f"Error running analytics query: {e}")

def main():
    print("==========================================")
    print("      WEATHER PIPELINE VALIDATION")
    print("==========================================")
    
    check_docker_containers()
    
    conn = check_postgres_connection()
    if conn:
        check_schemas(conn)
        check_data_freshness(conn)
        verify_models(conn)
        run_analytics_query(conn)
        conn.close()
    else:
        print_fail("Stopping tests due to DB connection failure")
        sys.exit(1)
        
    print("\n==========================================")
    print("           VALIDATION COMPLETE")
    print("==========================================")

if __name__ == "__main__":
    main()
