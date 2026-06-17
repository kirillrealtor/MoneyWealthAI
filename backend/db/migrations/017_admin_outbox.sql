-- 017_admin_outbox — audited read + retry for the notification outbox, surfaced
-- in the admin console. Same SECURITY DEFINER pattern as 012/014 (no RLS bypass
-- for the app role).

-- Recent outbox rows, newest first, optionally filtered by status.
CREATE OR REPLACE FUNCTION admin_outbox(p_status text, p_limit int)
RETURNS TABLE(
  outbox_id uuid, channel varchar, status varchar, attempts int,
  error text, created_at timestamptz, sent_at timestamptz
)
LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
  SELECT outbox_id, channel, status, attempts, error, created_at, sent_at
    FROM notification_outbox
   WHERE p_status IS NULL OR p_status = '' OR status = p_status
   ORDER BY created_at DESC
   LIMIT GREATEST(1, LEAST(p_limit, 100))
$$;

-- Re-queue a failed delivery (the outbox-retry worker picks up 'pending').
CREATE OR REPLACE FUNCTION admin_outbox_retry(p_outbox_id uuid)
RETURNS TABLE(outbox_id uuid, status varchar)
LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
  UPDATE notification_outbox
     SET status = 'pending', error = NULL
   WHERE outbox_id = p_outbox_id AND status = 'failed'
  RETURNING outbox_id, status
$$;

REVOKE ALL ON FUNCTION admin_outbox(text, int) FROM PUBLIC;
REVOKE ALL ON FUNCTION admin_outbox_retry(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION admin_outbox(text, int) TO app_user;
GRANT EXECUTE ON FUNCTION admin_outbox_retry(uuid) TO app_user;
