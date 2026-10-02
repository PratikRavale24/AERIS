-- AERIS PostgreSQL Initialization
-- Creates least-privilege roles and append-only audit protections.
-- Executed once by docker-entrypoint-initdb.d on first container start.

-- Read secrets for passwords
\set migrator_pass `cat /run/secrets/db_migrator_password`
\set app_pass `cat /run/secrets/db_password`

-- Create roles with least privilege
CREATE ROLE vayu_migrator LOGIN PASSWORD :'migrator_pass';
CREATE ROLE vayu_app LOGIN PASSWORD :'app_pass';

-- Grant schema usage
GRANT CONNECT ON DATABASE aeris TO vayu_migrator;
GRANT CONNECT ON DATABASE aeris TO vayu_app;

-- vayu_migrator: DDL privileges (used only by Alembic)
GRANT CREATE ON SCHEMA public TO vayu_migrator;
ALTER DEFAULT PRIVILEGES FOR ROLE aeris_admin IN SCHEMA public
    GRANT ALL ON TABLES TO vayu_migrator;
ALTER DEFAULT PRIVILEGES FOR ROLE aeris_admin IN SCHEMA public
    GRANT ALL ON SEQUENCES TO vayu_migrator;
ALTER DEFAULT PRIVILEGES FOR ROLE vayu_migrator IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO vayu_app;
ALTER DEFAULT PRIVILEGES FOR ROLE vayu_migrator IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO vayu_app;

-- vayu_app: DML only, no DDL, no superuser
-- (Specific table-level restrictions applied after migration via function below)

-- Function to protect immutable tables (called after migration)
CREATE OR REPLACE FUNCTION protect_immutable_tables() RETURNS void AS $$
BEGIN
    -- Audit log: append-only (no UPDATE, DELETE, TRUNCATE)
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'audit_log') THEN
        EXECUTE 'REVOKE UPDATE, DELETE ON audit_log FROM vayu_app';
        
        -- Create trigger to prevent UPDATE on audit_log
        IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_audit_log_no_update') THEN
            CREATE OR REPLACE FUNCTION prevent_audit_modification() RETURNS trigger AS $t$
            BEGIN
                RAISE EXCEPTION 'Modification of audit_log is forbidden. This table is append-only.';
            END;
            $t$ LANGUAGE plpgsql;
            
            CREATE TRIGGER trg_audit_log_no_update
                BEFORE UPDATE OR DELETE ON audit_log
                FOR EACH ROW EXECUTE FUNCTION prevent_audit_modification();
                
            CREATE TRIGGER trg_audit_log_no_truncate
                BEFORE TRUNCATE ON audit_log
                FOR EACH STATEMENT EXECUTE FUNCTION prevent_audit_modification();
        END IF;
    END IF;

    -- Decisions: no DELETE (immutable records)
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'decisions') THEN
        EXECUTE 'REVOKE DELETE ON decisions FROM vayu_app';
        
        IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_decisions_no_delete') THEN
            CREATE OR REPLACE FUNCTION prevent_decision_delete() RETURNS trigger AS $t$
            BEGIN
                RAISE EXCEPTION 'Deletion of decision records is forbidden.';
            END;
            $t$ LANGUAGE plpgsql;
            
            CREATE TRIGGER trg_decisions_no_delete
                BEFORE DELETE ON decisions
                FOR EACH ROW EXECUTE FUNCTION prevent_decision_delete();
        END IF;
    END IF;

    -- Evidence passports: fully immutable
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'evidence_passports') THEN
        EXECUTE 'REVOKE UPDATE, DELETE ON evidence_passports FROM vayu_app';
        
        IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_passport_no_modify') THEN
            CREATE OR REPLACE FUNCTION prevent_passport_modification() RETURNS trigger AS $t$
            BEGIN
                RAISE EXCEPTION 'Modification of evidence_passports is forbidden. These records are immutable.';
            END;
            $t$ LANGUAGE plpgsql;
            
            CREATE TRIGGER trg_passport_no_modify
                BEFORE UPDATE OR DELETE ON evidence_passports
                FOR EACH ROW EXECUTE FUNCTION prevent_passport_modification();
                
            CREATE TRIGGER trg_passport_no_truncate
                BEFORE TRUNCATE ON evidence_passports
                FOR EACH STATEMENT EXECUTE FUNCTION prevent_passport_modification();
        END IF;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Note: protect_immutable_tables() is called by the backend after Alembic migration completes.
-- This ensures tables exist before triggers are created.
