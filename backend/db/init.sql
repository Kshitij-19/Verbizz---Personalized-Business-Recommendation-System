-- Create the Business table if it doesn't exist
CREATE TABLE IF NOT EXISTS Business (
    id SERIAL PRIMARY KEY,
    businessid VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    rating NUMERIC(3, 2),
    review_count INTEGER,
    address TEXT,
    category TEXT,
    city TEXT,
    state TEXT,
    country TEXT,
    zip_code TEXT,
    latitude NUMERIC(10, 6),
    longitude NUMERIC(10, 6),
    phone TEXT,
    price VARCHAR(30),
    image_url TEXT,
    url TEXT,
    distance NUMERIC(6, 2),
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Check if the Business table exists, then run the COPY command
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'business') THEN
        COPY business (
            id, businessid, name, rating, review_count, address, category, city, state,
            country, zip_code, latitude, longitude, phone, price, image_url, url,
            distance, createdat, updatedat
        )
        FROM '/tmp/final_cleaned_data.csv'
        DELIMITER ','
        CSV HEADER
        QUOTE '"'
        ESCAPE '"';
    END IF;
END $$;