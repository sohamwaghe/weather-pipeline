-- Create the custom schema for weather data
CREATE SCHEMA IF NOT EXISTS weather_data;

-- Table to store raw weather data from WeatherStack API
CREATE TABLE IF NOT EXISTS weather_data.raw_weather (
    id SERIAL PRIMARY KEY,
    city VARCHAR(50) NOT NULL,
    temperature DECIMAL(5,2),
    humidity INTEGER,
    wind_speed DECIMAL(5,2),
    weather_description VARCHAR(100),
    observation_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for querying by city and time
CREATE INDEX IF NOT EXISTS idx_weather_city_time 
ON weather_data.raw_weather(city, observation_time);
