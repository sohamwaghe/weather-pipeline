from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import data_quality_checks

import requests
import json
import logging
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def load_weather_to_raw_table(**kwargs):
    ti = kwargs['ti']
    weather_data_list = ti.xcom_pull(task_ids='extract_weather_data')
    
    logging.info(f"Received {len(weather_data_list) if weather_data_list else 0} records from XCom.")
    
    if not weather_data_list:
        logging.warning("No weather data to load. Check 'extract_weather_data' task.")
        return

    db_user = os.getenv("POSTGRES_USER", "Airflow")
    db_password = os.getenv("POSTGRES_PASSWORD", "Airflow")
    db_host = os.getenv("POSTGRES_HOST", "postgres")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "weather_db")
    
    conn = None
    try:
        logging.info(f"Connecting to {db_name} at {db_host}...")
        conn = psycopg2.connect(user=db_user, password=db_password, host=db_host, port=db_port, database=db_name)
        with conn.cursor() as cur:
            cur.execute("CREATE SCHEMA IF NOT EXISTS raw;")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS raw.weather_data (
                    id SERIAL PRIMARY KEY,
                    city_name TEXT NOT NULL,
                    api_response JSONB NOT NULL,
                    api_call_timestamp TIMESTAMP NOT NULL,
                    ingestion_timestamp TIMESTAMP NOT NULL,
                    UNIQUE(city_name, api_call_timestamp) 
                );
            """)
            
            inserted_count = 0
            for data in weather_data_list:
                metadata = data.get("_metadata", {})
                city_name = metadata.get("city_name")
                api_call_timestamp = metadata.get("api_call_timestamp")
                ingestion_timestamp = metadata.get("ingestion_timestamp")
                api_response_json = json.dumps(data)
                
                insert_query = """
                    INSERT INTO raw.weather_data (city_name, api_response, api_call_timestamp, ingestion_timestamp)
                    VALUES (%s, %s, %s, %s) ON CONFLICT (city_name, api_call_timestamp) DO NOTHING;
                """
                cur.execute(insert_query, (city_name, api_response_json, api_call_timestamp, ingestion_timestamp))
                if cur.rowcount > 0:
                    inserted_count += 1
            
            conn.commit()
            logging.info(f"Successfully inserted {inserted_count} new records into raw.weather_data.")
    except Exception as e:
        logging.error(f"Error loading to PG: {e}")
        if conn: conn.rollback()
        raise e
    finally:
        if conn: conn.close()

def extract_weather_from_api(**kwargs):
    api_key = os.getenv("WEATHERSTACK_API_KEY")
    if not api_key:
        logging.error("WEATHERSTACK_API_KEY is missing!")
        return []
        
    cities = ["London", "New York", "Tokyo", "Mumbai", "Sydney"]
    weather_data_list = []
    base_url = "http://api.weatherstack.com/current"
    
    for city in cities:
        try:
            logging.info(f"Fetching data for {city}...")
            params = {"access_key": api_key, "query": city}
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if "error" in data:
                logging.error(f"API Error for {city}: {data['error'].get('info', 'Unknown error')}")
                continue
                
            current_time = datetime.utcnow().isoformat()
            data["_metadata"] = {
                "city_name": city, 
                "api_call_timestamp": current_time, 
                "ingestion_timestamp": current_time, 
                "status_code": response.status_code
            }
            weather_data_list.append(data)
            logging.info(f"Successfully collected data for {city}.")
        except Exception as e:
            logging.error(f"Exception for {city}: {e}")
            continue
            
    logging.info(f"Total records extracted: {len(weather_data_list)}")
    return weather_data_list

def task_failure_callback(context):
    logging.error("Task failed.")

default_args = {
    'owner': 'airflow',
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'on_failure_callback': task_failure_callback
}

with DAG(
    dag_id="weather_etl_pipeline",
    default_args=default_args,
    schedule_interval="@hourly",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['weather'],
) as dag:
    extract_weather_data = PythonOperator(
        task_id='extract_weather_data', 
        python_callable=extract_weather_from_api,
        provide_context=True
    )
    
    load_to_postgres = PythonOperator(
        task_id='load_to_postgres', 
        python_callable=load_weather_to_raw_table,
        provide_context=True
    )
    
    dbt_seed = BashOperator(
        task_id='dbt_seed', 
        bash_command='cd /opt/dbt && dbt seed --profiles-dir /opt/dbt'
    )
    
    dbt_run = BashOperator(
        task_id='dbt_run', 
        bash_command='cd /opt/dbt && dbt run --profiles-dir /opt/dbt'
    )
    
    dbt_test_task = BashOperator(
        task_id='dbt_test', 
        bash_command='cd /opt/dbt && dbt test --profiles-dir /opt/dbt'
    )
    
    dq_checks_task = PythonOperator(
        task_id='data_quality_checks', 
        python_callable=data_quality_checks.run_all_checks,
        provide_context=True
    )
    
    dbt_docs_task = BashOperator(
        task_id='dbt_docs_generate', 
        bash_command='cd /opt/dbt && dbt docs generate --profiles-dir /opt/dbt'
    )

    extract_weather_data >> load_to_postgres >> dbt_seed >> dbt_run >> dbt_test_task >> dq_checks_task >> dbt_docs_task
