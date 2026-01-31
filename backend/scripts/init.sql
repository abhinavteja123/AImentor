-- AI Mentor Database Initialization Script
-- This script runs automatically when PostgreSQL container starts

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create tables (basic structure - Alembic will handle migrations later)

-- Note: The SQLAlchemy models will create the actual tables on first run
-- This file is here for any custom PostgreSQL setup or initial data

-- Log that initialization is complete
DO $$
BEGIN
    RAISE NOTICE 'AI Mentor PostgreSQL database initialized successfully!';
END $$;
