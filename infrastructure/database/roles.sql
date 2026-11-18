-- AEGIS-DocIntel Database Roles & Least-Privilege Provisioning
-- PROT-FINAL-05: Workstream DEP-04 & DEP-TEST-006

-- 1. Migration Role (Runs schema changes in CI/CD pipeline)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'aegis_migration') THEN
        CREATE ROLE aegis_migration WITH LOGIN NOINHERIT;
    END IF;
END $$;

-- 2. Application Runtime Role (Minimal privilege: DML only, NO DDL)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'aegis_app') THEN
        CREATE ROLE aegis_app WITH LOGIN NOINHERIT;
    END IF;
END $$;

-- 3. Read-Only Auditing Role (SELECT only)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'aegis_readonly') THEN
        CREATE ROLE aegis_readonly WITH LOGIN NOINHERIT;
    END IF;
END $$;

-- Grant minimal permissions on schema public
GRANT CONNECT ON DATABASE aegis_production TO aegis_app, aegis_readonly, aegis_migration;
GRANT USAGE ON SCHEMA public TO aegis_app, aegis_readonly, aegis_migration;

-- Migration role gets DDL
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO aegis_migration;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO aegis_migration;

-- Application role gets DML only (SELECT, INSERT, UPDATE, DELETE)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO aegis_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO aegis_app;

-- Readonly role gets SELECT only
GRANT SELECT ON ALL TABLES IN SCHEMA public TO aegis_readonly;

-- Revoke default DDL rights from application and readonly roles
REVOKE CREATE ON SCHEMA public FROM aegis_app, aegis_readonly;
