-- =====================================================================
-- 014_admin_ops — audited cross-tenant read functions for the admin AI-ops
-- and Plaid-ops surfaces. Same pattern as 012: app_user (NOBYPASSRLS) calls
-- these owner-defined SECURITY DEFINER functions; no raw RLS bypass.
-- =====================================================================

-- Daily AI token usage (platform-wide) for the last N days.
CREATE OR REPLACE FUNCTION admin_ai_usage(p_days int)
RETURNS TABLE(day date, tokens bigint, users bigint)
LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
  SELECT date AS day, COALESCE(sum(tokens), 0)::bigint, count(DISTINCT user_id)::bigint
    FROM token_usage
   WHERE date >= current_date - GREATEST(1, LEAST(p_days, 90))
   GROUP BY date
   ORDER BY date
$$;

-- Today's biggest token spenders.
CREATE OR REPLACE FUNCTION admin_top_token_users(p_limit int)
RETURNS TABLE(user_id uuid, email varchar, tokens bigint)
LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
  SELECT tu.user_id, u.email, tu.tokens::bigint
    FROM token_usage tu JOIN users u ON u.user_id = tu.user_id
   WHERE tu.date = current_date
   ORDER BY tu.tokens DESC
   LIMIT GREATEST(1, LEAST(p_limit, 50))
$$;

-- Plaid connection + sync health at a glance.
CREATE OR REPLACE FUNCTION admin_plaid_health()
RETURNS TABLE(
  total_items bigint, good_items bigint, error_items bigint,
  active_jobs bigint, failed_jobs_24h bigint
)
LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
  SELECT
    (SELECT count(*) FROM plaid_items),
    (SELECT count(*) FROM plaid_items WHERE item_status = 'good'),
    (SELECT count(*) FROM plaid_items WHERE item_status <> 'good'),
    (SELECT count(*) FROM sync_jobs WHERE status IN ('pending', 'running')),
    (SELECT count(*) FROM sync_jobs WHERE status = 'failed' AND started_at >= now() - interval '24 hours')
$$;

-- Recent sync jobs (newest first; failures bubble up).
CREATE OR REPLACE FUNCTION admin_sync_jobs(p_limit int)
RETURNS TABLE(
  sync_id uuid, item_id uuid, status varchar,
  error_message text, transactions_synced int, started_at timestamptz
)
LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
  SELECT sync_id, item_id, status, error_message, transactions_synced, started_at
    FROM sync_jobs
   ORDER BY started_at DESC
   LIMIT GREATEST(1, LEAST(p_limit, 100))
$$;

REVOKE ALL ON FUNCTION admin_ai_usage(int) FROM PUBLIC;
REVOKE ALL ON FUNCTION admin_top_token_users(int) FROM PUBLIC;
REVOKE ALL ON FUNCTION admin_plaid_health() FROM PUBLIC;
REVOKE ALL ON FUNCTION admin_sync_jobs(int) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION admin_ai_usage(int) TO app_user;
GRANT EXECUTE ON FUNCTION admin_top_token_users(int) TO app_user;
GRANT EXECUTE ON FUNCTION admin_plaid_health() TO app_user;
GRANT EXECUTE ON FUNCTION admin_sync_jobs(int) TO app_user;
