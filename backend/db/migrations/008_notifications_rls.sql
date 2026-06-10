-- =====================================================================
-- 008_notifications_rls — Phase 5 proactive layer.
--   * tenant_id + FORCE RLS on alerts and notification_preferences (parity).
--   * notification_outbox: durable, idempotent, at-least-once delivery record
--     for email/push/sms channels (in-app notifications ARE the alerts rows).
-- =====================================================================

ALTER TABLE alerts                  ADD COLUMN tenant_id UUID REFERENCES tenants(tenant_id);
ALTER TABLE notification_preferences ADD COLUMN tenant_id UUID REFERENCES tenants(tenant_id);

-- Backfill (lift FORCE so the owner can read users during the copy).
ALTER TABLE users NO FORCE ROW LEVEL SECURITY;
UPDATE alerts a                  SET tenant_id = u.tenant_id FROM users u WHERE u.user_id = a.user_id;
UPDATE notification_preferences p SET tenant_id = u.tenant_id FROM users u WHERE u.user_id = p.user_id;
ALTER TABLE users FORCE ROW LEVEL SECURITY;

UPDATE alerts                   SET tenant_id = '00000000-0000-0000-0000-000000000001' WHERE tenant_id IS NULL;
UPDATE notification_preferences SET tenant_id = '00000000-0000-0000-0000-000000000001' WHERE tenant_id IS NULL;

ALTER TABLE alerts                  ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE notification_preferences ALTER COLUMN tenant_id SET NOT NULL;

CREATE INDEX idx_alerts_tenant ON alerts(tenant_id);

-- Delivery outbox (channels other than in-app). dedupe_key makes retries and
-- replica overlap safe (at-least-once without spamming users).
CREATE TABLE notification_outbox (
  outbox_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  tenant_id   UUID NOT NULL REFERENCES tenants(tenant_id),
  alert_id    UUID REFERENCES alerts(alert_id) ON DELETE SET NULL,
  channel     VARCHAR(20) NOT NULL,                 -- email | push | sms
  status      VARCHAR(20) NOT NULL DEFAULT 'pending',-- pending | sent | failed | skipped
  dedupe_key  VARCHAR NOT NULL,
  attempts    INTEGER NOT NULL DEFAULT 0,
  error       TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  sent_at     TIMESTAMPTZ,
  UNIQUE (dedupe_key, channel)
);
CREATE INDEX idx_outbox_pending ON notification_outbox(status) WHERE status = 'pending';
CREATE INDEX idx_outbox_tenant ON notification_outbox(tenant_id);

DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['alerts','notification_preferences','notification_outbox'] LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', t);
    EXECUTE format($f$
      CREATE POLICY tenant_isolation_%1$s ON %1$I
        USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
        WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
    $f$, t);
  END LOOP;
END$$;

-- Keyset pager for the alert/digest batch scan. The scan is a legitimate
-- cross-tenant admin job; this SECURITY DEFINER function returns only the
-- (user_id, tenant_id) mapping so the worker can then process each user inside
-- its own tenant context — without granting the app role RLS bypass.
CREATE OR REPLACE FUNCTION list_users_for_scan(p_after uuid, p_limit int)
RETURNS TABLE(user_id uuid, tenant_id uuid)
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT user_id, tenant_id FROM users
   WHERE (p_after IS NULL OR user_id > p_after)
   ORDER BY user_id
   LIMIT GREATEST(1, LEAST(p_limit, 1000))
$$;

REVOKE ALL ON FUNCTION list_users_for_scan(uuid, int) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION list_users_for_scan(uuid, int) TO app_user;
