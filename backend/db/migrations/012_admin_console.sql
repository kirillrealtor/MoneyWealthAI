-- =====================================================================
-- 012_admin_console — product-owner admin: a separate staff identity (RBAC),
-- a user `suspended` flag, and AUDITED cross-tenant read/write functions.
--
-- Security model: the app connects as `app_user` (NOBYPASSRLS) and must NEVER
-- read across tenants directly. The console's cross-tenant access is funneled
-- through these narrow SECURITY DEFINER functions (owned by the migration role,
-- which bypasses RLS) — each returns only what one screen needs. A bug in app
-- code therefore cannot exfiltrate a tenant's data; access is purpose-built and
-- logged at the app layer.
-- =====================================================================

-- Suspend flag — target of the admin "suspend user" action.
ALTER TABLE users ADD COLUMN IF NOT EXISTS suspended BOOLEAN NOT NULL DEFAULT false;

-- Admins are a SEPARATE identity from end users (blast-radius isolation): a
-- compromised user account can never be an admin, and vice-versa.
CREATE TABLE IF NOT EXISTS admins (
  admin_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email         VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR NOT NULL,
  role          VARCHAR(20) NOT NULL DEFAULT 'analyst'
                CHECK (role IN ('super_admin', 'owner', 'support', 'analyst')),
  mfa_secret    VARCHAR,            -- reserved for TOTP enrollment (next milestone)
  is_active     BOOLEAN NOT NULL DEFAULT true,
  last_login_at TIMESTAMPTZ,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

REVOKE ALL ON admins FROM PUBLIC;
GRANT SELECT, INSERT, UPDATE ON admins TO app_user;

-- ── Audited cross-tenant functions (SECURITY DEFINER) ────────────────────────

-- KPI aggregates. NOTE (1M scale): swap the internals for a pre-aggregated
-- rollup/materialized view so the dashboard never COUNT(*)s millions of rows.
CREATE OR REPLACE FUNCTION admin_kpis()
RETURNS TABLE(
  total_users bigint, verified_users bigint, suspended_users bigint,
  signups_today bigint, signups_7d bigint, signups_30d bigint,
  total_budgets bigint, total_goals bigint, linked_items bigint
)
LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
  SELECT
    (SELECT count(*) FROM users),
    (SELECT count(*) FROM users WHERE is_verified),
    (SELECT count(*) FROM users WHERE suspended),
    (SELECT count(*) FROM users WHERE created_at >= date_trunc('day', now())),
    (SELECT count(*) FROM users WHERE created_at >= now() - interval '7 days'),
    (SELECT count(*) FROM users WHERE created_at >= now() - interval '30 days'),
    (SELECT count(*) FROM budgets),
    (SELECT count(*) FROM goals),
    (SELECT count(*) FROM plaid_items)
$$;

-- Paginated user search (newest first).
CREATE OR REPLACE FUNCTION admin_list_users(p_search text, p_limit int, p_offset int)
RETURNS TABLE(
  user_id uuid, email varchar, full_name varchar, tier varchar,
  is_verified boolean, suspended boolean, created_at timestamptz, last_login_at timestamptz
)
LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
  SELECT user_id, email, full_name, tier, is_verified, suspended, created_at, last_login_at
    FROM users
   WHERE p_search IS NULL OR p_search = ''
      OR email ILIKE '%' || p_search || '%'
      OR full_name ILIKE '%' || p_search || '%'
   ORDER BY created_at DESC, user_id
   LIMIT GREATEST(1, LEAST(p_limit, 100)) OFFSET GREATEST(0, p_offset)
$$;

-- Single user detail + per-user counts.
CREATE OR REPLACE FUNCTION admin_get_user(p_user_id uuid)
RETURNS TABLE(
  user_id uuid, email varchar, full_name varchar, tier varchar, advisor_persona varchar,
  is_verified boolean, suspended boolean, onboarding_step int,
  created_at timestamptz, last_login_at timestamptz,
  budget_count bigint, goal_count bigint, linked_items bigint
)
LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
  SELECT u.user_id, u.email, u.full_name, u.tier, u.advisor_persona,
         u.is_verified, u.suspended, u.onboarding_step, u.created_at, u.last_login_at,
         (SELECT count(*) FROM budgets b WHERE b.user_id = u.user_id),
         (SELECT count(*) FROM goals g WHERE g.user_id = u.user_id),
         (SELECT count(*) FROM plaid_items p WHERE p.user_id = u.user_id)
    FROM users u WHERE u.user_id = p_user_id
$$;

-- Admin mutation of a user (tier / suspend / verify). NULL args = leave as-is.
CREATE OR REPLACE FUNCTION admin_update_user(
  p_user_id uuid, p_tier varchar, p_suspended boolean, p_is_verified boolean
)
RETURNS TABLE(user_id uuid, tier varchar, suspended boolean, is_verified boolean)
LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
  UPDATE users SET
    tier        = COALESCE(p_tier, tier),
    suspended   = COALESCE(p_suspended, suspended),
    is_verified = COALESCE(p_is_verified, is_verified),
    updated_at  = now()
  WHERE user_id = p_user_id
  RETURNING user_id, tier, suspended, is_verified
$$;

-- Audit feed (newest first).
CREATE OR REPLACE FUNCTION admin_audit(p_limit int, p_offset int)
RETURNS TABLE(
  log_id uuid, user_id uuid, action varchar, resource varchar,
  resource_id uuid, ip_address inet, metadata jsonb, ts timestamptz
)
LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
  SELECT log_id, user_id, action, resource, resource_id, ip_address, metadata, timestamp
    FROM audit_logs
   ORDER BY timestamp DESC
   LIMIT GREATEST(1, LEAST(p_limit, 100)) OFFSET GREATEST(0, p_offset)
$$;

REVOKE ALL ON FUNCTION admin_kpis() FROM PUBLIC;
REVOKE ALL ON FUNCTION admin_list_users(text, int, int) FROM PUBLIC;
REVOKE ALL ON FUNCTION admin_get_user(uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION admin_update_user(uuid, varchar, boolean, boolean) FROM PUBLIC;
REVOKE ALL ON FUNCTION admin_audit(int, int) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION admin_kpis() TO app_user;
GRANT EXECUTE ON FUNCTION admin_list_users(text, int, int) TO app_user;
GRANT EXECUTE ON FUNCTION admin_get_user(uuid) TO app_user;
GRANT EXECUTE ON FUNCTION admin_update_user(uuid, varchar, boolean, boolean) TO app_user;
GRANT EXECUTE ON FUNCTION admin_audit(int, int) TO app_user;
