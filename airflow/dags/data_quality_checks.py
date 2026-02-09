import logging
import os
import psycopg2
from datetime import datetime, timedelta

def get_db_connection():
    db_user = os.getenv("POSTGRES_USER")
    db_password = os.getenv("POSTGRES_PASSWORD")
    db_host = os.getenv("POSTGRES_HOST")
    db_port = os.getenv("POSTGRES_PORT")
    db_name = os.getenv("POSTGRES_DB")

    return psycopg2.connect(
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port,
        database=db_name
    )

def check_data_freshness():
    """Query raw.weather_data for latest ingestion_timestamp"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT MAX(ingestion_timestamp) FROM raw.weather_data;")
            last_update = cur.fetchone()[0]
            
            if not last_update:
                return {'status': 'fail', 'message': 'No data found in raw.weather_data', 'last_update': None}
            
            diff = datetime.utcnow() - last_update
            
            if diff > timedelta(hours=2):
                return {'status': 'fail', 'message': f'Data is very stale. Last update: {last_update}', 'last_update': last_update}
            elif diff > timedelta(minutes=90):
                return {'status': 'warn', 'message': f'Data is slightly delayed. Last update: {last_update}', 'last_update': last_update}
            
            return {'status': 'pass', 'message': 'Data is fresh.', 'last_update': last_update}
    finally:
        conn.close()

def check_data_completeness():
    """Check we have data for ALL expected cities (London, New York, Tokyo, Mumbai, Sydney) in the last 2 hours"""
    expected_cities = ["London", "New York", "Tokyo", "Mumbai", "Sydney"]
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # We check the last 2 hours to allow for slight delays
            query = """
                SELECT DISTINCT city_name 
                FROM raw.weather_data 
                WHERE ingestion_timestamp > NOW() - INTERVAL '2 hours';
            """
            cur.execute(query)
            present_cities = [row[0] for row in cur.fetchall()]
            
            missing_cities = [city for city in expected_cities if city not in present_cities]
            
            if missing_cities:
                return {'status': 'fail', 'message': f'Missing data for cities: {", ".join(missing_cities)}'}
            
            return {'status': 'pass', 'message': 'All expected cities are present.'}
    finally:
        conn.close()

def check_temperature_anomalies():
    """Check for physically impossible temperatures or suspicious jumps"""
    conn = get_db_connection()
    anomalies = []
    try:
        with conn.cursor() as cur:
            # 1. Physically impossible bounds
            query_bounds = """
                SELECT city_name, temperature, api_call_timestamp 
                FROM analytics.fact_weather 
                WHERE ingestion_timestamp > NOW() - INTERVAL '2 hours'
                AND (temperature < -50 OR temperature > 60);
            """
            cur.execute(query_bounds)
            for row in cur.fetchall():
                anomalies.append(f"CRITICAL: {row[0]} had temperature {row[1]} at {row[2]} (Out of bounds)")
            
            # 2. Suspicious jumps (> 20C in 1 hour)
            # This is a bit complex for a simple query without window functions over historical data
            # but we can check if there's any record in the last hour that differs from the record 1 hour before it.
            query_jumps = """
                WITH latest_hourly AS (
                    SELECT 
                        city_id, 
                        temperature, 
                        api_call_timestamp,
                        LAG(temperature) OVER (PARTITION BY city_id ORDER BY api_call_timestamp) as prev_temp
                    FROM analytics.fact_weather
                )
                SELECT c.city_name, l.temperature, l.prev_temp, l.api_call_timestamp
                FROM latest_hourly l
                JOIN analytics.dim_cities c ON l.city_id = c.city_id
                WHERE l.api_call_timestamp > NOW() - INTERVAL '2 hours'
                AND ABS(l.temperature - l.prev_temp) > 20;
            """
            cur.execute(query_jumps)
            for row in cur.fetchall():
                anomalies.append(f"WARNING: {row[0]} temp jumped from {row[2]} to {row[1]} at {row[3]}")

            if any("CRITICAL" in a for a in anomalies):
                return {'status': 'fail', 'message': "; ".join(anomalies)}
            elif anomalies:
                return {'status': 'warn', 'message': "; ".join(anomalies)}
            
            return {'status': 'pass', 'message': 'No temperature anomalies detected.'}
    finally:
        conn.close()

def check_null_values():
    """Check for NULLs in temperature, humidity, pressure"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            query = """
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN temperature IS NULL THEN 1 END) as null_temp,
                    COUNT(CASE WHEN humidity IS NULL THEN 1 END) as null_hum,
                    COUNT(CASE WHEN pressure IS NULL THEN 1 END) as null_pres
                FROM analytics.fact_weather
                WHERE ingestion_timestamp > NOW() - INTERVAL '24 hours';
            """
            cur.execute(query)
            row = cur.fetchone()
            total = row[0]
            if total == 0:
                return {'status': 'pass', 'message': 'No records to check for NULLs.'}
            
            null_metrics = {
                'temperature': (row[1] / total) * 100,
                'humidity': (row[2] / total) * 100,
                'pressure': (row[3] / total) * 100
            }
            
            critical_nulls = [k for k, v in null_metrics.items() if v > 5]
            
            message = ", ".join([f"{k}: {v:.1f}% NULL" for k, v in null_metrics.items()])
            
            if critical_nulls:
                return {'status': 'fail', 'message': f'Critical NULL percentage in: {", ".join(critical_nulls)}. Detail: {message}'}
            
            return {'status': 'pass', 'message': f'NULL levels healthy. {message}'}
    finally:
        conn.close()

def check_duplicate_records():
    """Check for duplicate city+timestamp in fact_weather"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            query = """
                SELECT city_id, api_call_timestamp, COUNT(*)
                FROM analytics.fact_weather
                GROUP BY city_id, api_call_timestamp
                HAVING COUNT(*) > 1;
            """
            cur.execute(query)
            dupes = cur.fetchall()
            
            if dupes:
                return {'status': 'fail', 'message': f'Found {len(dupes)} sets of duplicate records! Sample: CityID {dupes[0][0]} at {dupes[0][1]}'}
            
            return {'status': 'pass', 'message': 'No duplicate records found.'}
    finally:
        conn.close()

def run_all_checks():
    """Aggregates all quality checks"""
    checks = {
        'Freshness': check_data_freshness(),
        'Completeness': check_data_completeness(),
        'Anomalies': check_temperature_anomalies(),
        'Null Values': check_null_values(),
        'Duplicates': check_duplicate_records()
    }
    
    summary = []
    has_fail = False
    
    print("\n" + "="*50)
    print("DATA QUALITY MONITORING REPORT")
    print("="*50)
    print(f"{'Check Name':<20} | {'Status':<7} | {'Message'}")
    print("-" * 50)
    
    for name, result in checks.items():
        status = result['status'].upper()
        if status == 'FAIL':
            has_fail = True
        print(f"{name:<20} | {status:<7} | {result['message']}")
        summary.append(f"{name}: {status}")

    print("="*50)
    
    if has_fail:
        raise Exception(f"Data Quality Check Failed! Summary: {', '.join(summary)}")
    
    return summary
