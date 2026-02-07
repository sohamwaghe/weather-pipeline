from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
import json
import logging
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def load_weather_to_raw_table(**kwargs):
    """
    Loads weather data from XCom into PostgreSQL.
    
    This function:
    1. Pulls the extracted weather data from the 'extract_weather_data' task using XCom.
    2. Connects to the PostgreSQL database using credentials from environment variables.
    3. Ensures the schema 'raw' and table 'weather_data' exist.
    4. Inserts each weather record into the table.
    5. Commits the transaction and closes the connection.
    
    Args:
        **kwargs: Airflow context arguments.
    """
    ti = kwargs['ti']
    weather_data_list = ti.xcom_pull(task_ids='extract_weather_data')
    
    if not weather_data_list:
        logging.info("No weather data to load.")
        return

    # Database connection parameters
    db_user = os.getenv("POSTGRES_USER")
    db_password = os.getenv("POSTGRES_PASSWORD")
    db_host = os.getenv("POSTGRES_HOST")
    db_port = os.getenv("POSTGRES_PORT")
    db_name = os.getenv("POSTGRES_DB")
    
    conn = None
    try:
        # Context manager for automatic connection handling? 
        # psycopg2 connection can be used as context manager for transaction, 
        # but closing connection needs to be explicit or via `with psycopg2.connect() ... as conn:`
        
        logging.info("Connecting to PostgreSQL...")
        conn = psycopg2.connect(
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
            database=db_name
        )
        
        # Open a cursor to perform database operations
        with conn.cursor() as cur:
            # Create Schema and Table if they ensure idempotency of setup
            logging.info("Ensuring schema and table exist...")
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
            # Checks for duplicate entries based on city and api_call_timestamp
            
            logging.info(f"Inserting {len(weather_data_list)} records...")
            inserted_count = 0
            
            for data in weather_data_list:
                metadata = data.get("_metadata", {})
                city_name = metadata.get("city_name")
                api_call_timestamp = metadata.get("api_call_timestamp")
                ingestion_timestamp = metadata.get("ingestion_timestamp")
                
                # Convert dict to JSON string for JSONB
                api_response_json = json.dumps(data)
                
                # Parameterized query to prevent SQL injection
                # ON CONFLICT DO NOTHING ensures idempotency if we re-run the extraction 
                # for the same timestamp (which XCom might pass if re-run downstream only)
                insert_query = """
                    INSERT INTO raw.weather_data 
                    (city_name, api_response, api_call_timestamp, ingestion_timestamp)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (city_name, api_call_timestamp) DO NOTHING;
                """
                
                cur.execute(insert_query, (
                    city_name, 
                    api_response_json, 
                    api_call_timestamp, 
                    ingestion_timestamp
                ))
                
                # Check if a row was actually inserted
                if cur.rowcount > 0:
                    inserted_count += 1

            conn.commit()
            logging.info(f"Successfully inserted {inserted_count} new records.")
            
    except Exception as e:
        logging.error(f"Error loading data to PostgreSQL: {e}")
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()
            logging.info("PostgreSQL connection closed.")

def extract_weather_from_api(**kwargs):
    """
    Extracts weather data from WeatherStack API for a list of cities.
    
    This function:
    1. Retrieves the API key from the environment.
    2. Iterates through a predefined list of cities.
    3. Makes a GET request to the WeatherStack API for each city.
    4. collecting the standardized JSON response and metadata.
    5. Returns the list of weather data to be pushed to XCom.
    
    Args:
        **kwargs: Airflow context arguments.
        
    Returns:
        list: A list of dictionaries containing weather data and metadata for each city.
    """
    api_key = os.getenv("WEATHERSTACK_API_KEY")
    if not api_key:
        logging.error("WEATHERSTACK_API_KEY not found in environment variables.")
        # We raise an error here to fail the task if the configuration is missing
        raise ValueError("WEATHERSTACK_API_KEY not found.")

    cities = ["London", "New York", "Tokyo", "Mumbai", "Sydney"]
    weather_data_list = []
    
    base_url = "http://api.weatherstack.com/current"
    
    for city in cities:
        try:
            logging.info(f"Fetching weather data for {city}...")
            params = {
                "access_key": api_key,
                "query": city
            }
            
            # Use a timeout to ensure the task doesn't hang indefinitely
            response = requests.get(base_url, params=params, timeout=10)
            
            # Check for HTTP errors (e.g., 401 Unauthorized, 404 Not Found)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API-specific errors (WeatherStack returns 200 even for some errors)
            if "error" in data:
                logging.error(f"API Error for {city}: {data['error']['info']}")
                continue

            # Add metadata
            # We add timestamps to track when the data was generated vs when we ingested it.
            # This is crucial for debugging data freshness and lineage issues.
            current_time = datetime.utcnow().isoformat()
            data["_metadata"] = {
                "city_name": city,
                "api_call_timestamp": current_time,
                "ingestion_timestamp": current_time,
                "status_code": response.status_code
            }
            
            weather_data_list.append(data)
            logging.info(f"Successfully fetched data for {city}.")
            
        except requests.exceptions.RequestException as e:
            # We handle errors per city to prevent a single failure (e.g., one city's API call failing)
            # from failing the entire task. This ensures we collect as much data as possible.
            logging.error(f"Error fetching data for {city}: {e}")
            continue
        except Exception as e:
            logging.error(f"Unexpected error for {city}: {e}")
            continue

    # XCom (Cross-Communication) is used to pass messages or small amounts of data 
    # between tasks. Here we return the list of data, which Airflow automatically 
    # pushes to XCom with the key 'return_value'.
    logging.info(f"Extracted data for {len(weather_data_list)} cities.")
    return weather_data_list

default_args = {
    'owner': 'airflow',
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': False,
}

with DAG(
    dag_id="weather_etl_pipeline",
    default_args=default_args,
    description="A simple ETL pipeline for weather data (WeatherStack)",
    schedule_interval="@hourly",
    start_date=datetime.now() - timedelta(days=1),
    catchup=False,
    tags=['weather', 'etl', 'production'],
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

    extract_weather_data >> load_to_postgres
