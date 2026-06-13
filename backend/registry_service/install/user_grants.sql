-- PKB Registry Database User and Grants Script
-- Created: 2026-05-30
-- Description: Creates database user and assigns permissions to registry and rag schemas

-- ============================================================================
-- User Creation
-- ============================================================================

-- Create the user if it does not exist (replace 'pkb_user' and 'password123' with actual credentials)
-- Note: Ensure strong password in production
DO
$$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'pkb_user') THEN
      CREATE USER pkb_user WITH PASSWORD 'password123';
   END IF;
END
$$;

-- ============================================================================
-- Database Privileges
-- ============================================================================

-- Grant connect and temporary tables access on target databases if they exist
DO
$$
BEGIN
   IF EXISTS (SELECT FROM pg_catalog.pg_database WHERE datname = 'PKB') THEN
      EXECUTE 'GRANT CONNECT, TEMPORARY ON DATABASE "PKB" TO pkb_user';
   END IF;
END
$$;


-- ============================================================================
-- Grant Privileges on Schemas
-- ============================================================================

-- Ensure schemas exist
CREATE SCHEMA IF NOT EXISTS registry;

-- Grant usage and create on both schemas
GRANT USAGE, CREATE ON SCHEMA registry TO pkb_user;
GRANT USAGE, CREATE ON SCHEMA public TO pkb_user;


-- ============================================================================
-- Registry Schema - Full Rights
-- ============================================================================

-- Grant all privileges on all tables in registry schema
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA registry TO pkb_user;

-- Grant all privileges on all sequences in registry schema
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA registry TO pkb_user;

-- Grant all privileges on all functions in registry schema
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA registry TO pkb_user;

-- Set default privileges for future objects in registry schema
ALTER DEFAULT PRIVILEGES IN SCHEMA registry GRANT ALL PRIVILEGES ON TABLES TO pkb_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA registry GRANT ALL PRIVILEGES ON SEQUENCES TO pkb_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA registry GRANT ALL PRIVILEGES ON FUNCTIONS TO pkb_user;


-- ============================================================================
-- Public Schema - Full Rights
-- ============================================================================

-- Grant all privileges on all tables in public schema
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO pkb_user;

-- Grant all privileges on all sequences in public schema
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO pkb_user;

-- Grant all privileges on all functions in public schema
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO pkb_user;

-- Set default privileges for future objects in public schema
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO pkb_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO pkb_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON FUNCTIONS TO pkb_user;


-- ============================================================================
-- Optional: Additional Convenience Grants
-- ============================================================================

-- Grant CONNECT privilege on the database (optional, depending on authentication method)
-- GRANT CONNECT ON DATABASE pkb_registry TO pkb_user;

-- Grant TEMPORARY privilege to allow temp tables if needed
-- GRANT TEMPORARY ON DATABASE pkb_registry TO pkb_user;

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Uncomment below to verify grants were applied (run as superuser):
/*
SELECT * FROM information_schema.role_table_grants WHERE grantee = 'pkb_user';
SELECT * FROM information_schema.table_privileges WHERE grantee = 'pkb_user';
*/

-- ============================================================================
-- End of Script
-- ============================================================================
