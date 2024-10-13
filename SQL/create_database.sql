CREATE SCHEMA IF NOT EXISTS "Satelite" AUTHORIZATION postgres;
CREATE TABLE IF NOT EXISTS "Satelite".tle_data (
    id SERIAL PRIMARY KEY,
    satellite_name VARCHAR(255),
    line1 TEXT NOT NULL,
    line2 TEXT NOT NULL,
    norad_id VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_norad_id UNIQUE (norad_id)
);