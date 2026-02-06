-- Database Initialization Script for Weather Data Pipeline
-- This script runs automatically when the PostgreSQL container first starts

-- ============================================================================
-- 1. SCHEMA SETUP
-- ============================================================================

-- We use separate schemas to organize data by its lifecycle stage:
-- 'raw'       : Landing zone for unprocessed data exactly as received from API
-- 'staging'   : Intermediate area for cleaning, type casting, and deduping
-- 'analytics' : Final star schema/marts ready for dashboard consumption

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;

-- ============================================================================
-- 2. RAW DATA STORAGE
-- ============================================================================

-- Rationale for storing raw JSON:
-- 1. Auditability: We preserve the exact response from the API for debugging
-- 2. Resilience: If our transform logic changes, we can re-process historical data
-- 3. Flexibility: We can extract new fields later without needing to backfill

CREATE TABLE IF NOT EXISTS raw.weather_data (
    id SERIAL PRIMARY KEY,
    
    -- Searchable metadata fields
    city_name VARCHAR(100),
    
    -- The complete API response stored as binary JSON for efficient querying
    api_response JSONB,
    
    -- Timestamps for data lineage
    ingestion_timestamp TIMESTAMP DEFAULT NOW(),  -- When we received the data
    api_call_timestamp TIMESTAMP,                 -- When the API said the data was measured
    
    -- Metadata for auditing
    source VARCHAR(50) DEFAULT 'weatherstack'
);

-- ============================================================================
-- 3. PERFORMANCE OPTIMIZATION
-- ============================================================================

-- Index for efficient querying by city and time (common access patterns)
CREATE INDEX IF NOT EXISTS idx_raw_weather_city_time 
ON raw.weather_data(city_name, ingestion_timestamp);

-- GIN index allows high-speed querying within the JSONB structure itself
CREATE INDEX IF NOT EXISTS idx_raw_weather_json 
ON raw.weather_data USING gin (api_response);

-- ============================================================================
-- 4. PERMISSIONS
-- ============================================================================

-- Ensure the main user has full control over all schemas
GRANT ALL PRIVILEGES ON SCHEMA raw TO CURRENT_USER;
GRANT ALL PRIVILEGES ON SCHEMA staging TO CURRENT_USER;
GRANT ALL PRIVILEGES ON SCHEMA analytics TO CURRENT_USER;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA raw TO CURRENT_USER;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA staging TO CURRENT_USER;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA analytics TO CURRENT_USER;

