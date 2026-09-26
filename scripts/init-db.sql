-- Database initialization script for DAM
-- Run as part of PostgreSQL container startup

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create full-text search configuration for English
-- (already available by default, but we can customize if needed)

-- Set default privileges for dam user
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO dam;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO dam;