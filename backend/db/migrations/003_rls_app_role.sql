-- =====================================================================
-- 003_rls_app_role — Make tenant isolation REAL.
--
-- Problem fixed: RLS on `users` was defined but bypassed because the app
-- connected as the table OWNER (owners bypass RLS) and never set tenant
-- context. This migration:
--   1. Adds tenant_id to the secret-token tables so tenant can be resolved
--      WITHOUT a circular read of the (now RLS-protected) users table.
--   2. Recreates the users policy with USING + WITH CHECK (covers INSERT).
--   3. FORCEs RLS so even the owner is subject to it.
--   4. Creates a NON-OWNER `app_user` role that the application connects as,
--      so RLS is actually enforced at the data layer.
--
-- Production note: the app_user role + password are provisioned by IaC and
-- the password comes from AWS Secrets Manager. The DO block below is for
-- local/dev parity only.
-- =====================================================================

-- 1. Tenant columns on secret-token tables (backfill BEFORE forcing RLS).
ALTER TABLE user_sessions ADD COLUMN tenant_id UUID REFERENCES tenants(tenant_id);
ALTER TABLE email_verification_tokens ADD COLUMN tenant_id UUID REFERENCES tenants(tenant_id);

UPDATE user_sessions s SET tenant_id = u.tenant_id
  FROM users u WHERE u.user_id = s.user_id;
UPDATE email_verification_tokens t SET tenant_id = u.tenant_id
  FROM users u WHERE u.user_id = t.user_id;

ALTER TABLE user_sessions ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE email_verification_tokens ALTER COLUMN tenant_id SET NOT NULL;

-- 2. Recreate the users policy with WITH CHECK so INSERT/UPDATE are scoped too.
DROP POLICY IF EXISTS tenant_isolation_users ON users;
CREATE POLICY tenant_isolation_users ON users
  USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
  WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- 3. Enforce RLS even for the table owner.
ALTER TABLE users FORCE ROW LEVEL SECURITY;

-- 4. Non-owner application role.
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_user') THEN
    CREATE ROLE app_user LOGIN PASSWORD 'app_user';
  END IF;
END$$;

GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;
-- Future tables (later migrations) automatically grant to app_user.
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO app_user;

-- app_user must NOT bypass RLS (it isn't a superuser, but be explicit).
ALTER ROLE app_user NOBYPASSRLS;
